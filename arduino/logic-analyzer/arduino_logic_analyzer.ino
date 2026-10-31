/*
 * ============================================================================
 *  8-Channel Logic Analyzer - Arduino Uno R3 firmware
 *  Version 1.0
 * ============================================================================
 *
 *  Works together with the PC application "logic_analyzer_gui.py".
 *
 *  CHANNEL / PIN MAPPING
 *  ---------------------
 *    Channel   Digital mode (fast)   Analog mode (slow, adjustable threshold)
 *    CH1       D2                    A0
 *    CH2       D3                    A1
 *    CH3       D4                    A2
 *    CH4       D5                    A3
 *    CH5       D6                    A4
 *    CH6       D7                    A5
 *    CH7       D8                    D8  (digital)
 *    CH8       D9                    D9  (digital)
 *    GND       GND  (always connect the ground of the circuit under test!)
 *
 *  D0/D1 are used by the USB serial port and D13 is left free.
 *
 *  OPERATION
 *  ---------
 *  - The PC sends one ASCII command per line (terminated with '\n').
 *  - The Arduino captures a block of samples into SRAM and sends it back as a
 *    single binary frame.
 *  - Sampling is paced by Timer1 (CTC mode). The loop polls the compare flag,
 *    so the sampling instants are deterministic (jitter of a few CPU cycles).
 *    Interrupts are disabled while sampling.
 *  - Trigger: samples are written into a circular buffer, so pre-trigger data
 *    is available. When the trigger condition occurs, the remaining
 *    post-trigger samples are captured and the buffer is sent in order.
 *
 *  COMMANDS (PC -> Arduino)
 *  ------------------------
 *    ID                      -> "LA8 <version> <max_samples>\n"
 *    A                       -> abort capture; answers "ABORT\n"
 *    S <rate> <analog> <thr_mV> <trigType> <trigCh> <prePct> <auto> <count>
 *        rate     sample rate in Hz
 *        analog   0 = digital mode, 1 = analog mode (threshold applies)
 *        thr_mV   analog threshold in millivolts (0..5000)
 *        trigType 0 off, 1 rising, 2 falling, 3 any edge, 4 high, 5 low
 *        trigCh   trigger channel, 0..7 (CH1..CH8)
 *        prePct   pre-trigger percentage of the buffer (0..90)
 *        auto     1 = auto (capture anyway after a timeout), 0 = normal
 *        count    number of samples (rounded down to 128/256/512/1024)
 *
 *  FRAME (Arduino -> PC), little endian
 *  ------------------------------------
 *    0xA5 0x5A | flags(1) | actual_rate(4) | count(2) | trigPos(2) |
 *    data[count] | checksum(1, sum of data bytes modulo 256)
 *      flags bit0 = triggered, bit1 = analog mode
 *      trigPos    index of the trigger sample inside data[] (0xFFFF = none)
 *
 *  Text replies ("ABORT", "ERR ...") are ASCII lines and never contain 0xA5.
 * ============================================================================
 */

#include <Arduino.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdlib.h>

// ----------------------------------------------------------------------------
// Configuration
// ----------------------------------------------------------------------------
#define FW_ID             "LA8 1.0 1024"
#define SERIAL_BAUD       500000UL   // must match the PC application

#define BUF_SIZE          1024U      // capture buffer (bytes of SRAM)
#define MIN_SAMPLES       128U

#define MAX_RATE_DIGITAL  250000UL   // Hz, no trigger
#define MAX_RATE_TRIGGER  125000UL   // Hz, trigger enabled (more work per sample)
#define MAX_RATE_ANALOG   5000UL     // Hz, 6 ADC conversions per sample
#define SLOW_RATE         2000UL     // below this rate the capture can be aborted

#define TRIG_OFF          0
#define TRIG_RISING       1
#define TRIG_FALLING      2
#define TRIG_EDGE         3
#define TRIG_HIGH         4
#define TRIG_LOW          5

#define FLAG_TRIGGERED    0x01
#define FLAG_ANALOG       0x02

#define LINE_MAX_LEN      48

#define ALWAYS_INLINE     inline __attribute__((always_inline))

// ----------------------------------------------------------------------------
// Global state (SRAM budget: ~1.1 KB used, Uno has 2 KB)
// ----------------------------------------------------------------------------
static uint8_t  sampleBuf[BUF_SIZE];
static char     lineBuf[LINE_MAX_LEN];
static uint8_t  lineLen = 0;
static uint16_t analogThresholdCounts = 512;   // 10-bit ADC counts

// ----------------------------------------------------------------------------
// Timer1: sample clock
// ----------------------------------------------------------------------------

// Starts Timer1 in CTC mode so that the OCF1A flag is set at "rate" Hz.
// Returns the real sample rate obtained (integer rounding of the divider).
static uint32_t timerStart(uint32_t rate) {
  static const uint16_t presc[5] = {1, 8, 64, 256, 1024};
  uint8_t  idx = 0;
  uint32_t top = 2;

  for (idx = 0; idx < 5; idx++) {
    uint32_t div = (uint32_t)presc[idx] * rate;
    top = (F_CPU + div / 2UL) / div;           // rounded
    if (top <= 65536UL) break;
  }
  if (idx == 5) { idx = 4; top = 65536UL; }
  if (top < 2UL) top = 2UL;

  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1  = 0;
  OCR1A  = (uint16_t)(top - 1UL);
  TIFR1  = _BV(OCF1A);                          // clear flag
  TCCR1B = _BV(WGM12) | (idx + 1);              // CTC, prescaler bits 1..5

  return F_CPU / ((uint32_t)presc[idx] * top);
}

static void timerStop() {
  TCCR1B = 0;
  TIFR1  = _BV(OCF1A);
}

// ----------------------------------------------------------------------------
// Sampling functions
// ----------------------------------------------------------------------------

// Digital: D2..D7 = PORTD bits 2..7, D8..D9 = PORTB bits 0..1
// Result: bit0..bit5 = D2..D7, bit6 = D8, bit7 = D9
static ALWAYS_INLINE uint8_t sampleDigital() {
  return (uint8_t)((PIND >> 2) | (PINB << 6));
}

// Analog: A0..A5 are digitised and compared with the threshold.
// D8/D9 stay digital. The six conversions are sequential, so the channels are
// sampled ~13 us apart from each other (skew).
static uint8_t sampleAnalog() {
  uint8_t v = 0;
  for (uint8_t ch = 0; ch < 6; ch++) {
    ADMUX = _BV(REFS0) | ch;                    // AVcc reference, channel ch
    ADCSRA |= _BV(ADSC);
    while (ADCSRA & _BV(ADSC)) { }
    if (ADC > analogThresholdCounts) v |= _BV(ch);
  }
  return (uint8_t)(v | (PINB << 6));
}

static void analogEnable() {
  DIDR0  = 0x3F;                                // disable digital buffers A0..A5
  ADCSRA = _BV(ADEN) | _BV(ADPS2);              // ADC clock = F_CPU/16 = 1 MHz
}

static void analogDisable() {
  DIDR0  = 0x00;
  ADCSRA = _BV(ADEN) | _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0);  // Arduino default
}

static ALWAYS_INLINE uint8_t takeSample(bool analog) {
  if (analog) return sampleAnalog();
  return sampleDigital();
}

// Waits for the next sample tick. When "check" is true it also watches the
// serial receiver and returns false if the PC sent something (abort request).
static ALWAYS_INLINE bool waitTick(bool check) {
  if (check) {
    while (!(TIFR1 & _BV(OCF1A))) {
      if (UCSR0A & _BV(RXC0)) return false;
    }
  } else {
    while (!(TIFR1 & _BV(OCF1A))) { }
  }
  TIFR1 = _BV(OCF1A);                           // clear flag (write 1)
  return true;
}

// ----------------------------------------------------------------------------
// Capture engine
//   analog : use ADC + threshold
//   check  : allow abort while waiting for the sample tick (slow rates)
// "head" returns the index of the oldest sample inside the circular buffer.
// "trig" returns true if the trigger condition was found.
// The function is always inlined, so "analog" and "check" are compile-time
// constants in each of the three wrappers below.
// ----------------------------------------------------------------------------
static ALWAYS_INLINE bool captureEngine(bool analog, bool check,
                                        uint16_t n, uint16_t pre,
                                        uint8_t trigType, uint8_t trigMask,
                                        bool autoMode,
                                        uint16_t *headOut, bool *trigOut) {
  uint16_t head = 0;
  *trigOut = false;
  *headOut = 0;

  // ---- No trigger: simple linear capture --------------------------------
  if (trigType == TRIG_OFF) {
    for (uint16_t i = 0; i < n; i++) {
      if (!waitTick(check)) return false;
      sampleBuf[i] = takeSample(analog);
    }
    return true;
  }

  // ---- Trigger: circular buffer with pre-trigger -------------------------
  const uint16_t mask = n - 1;                  // n is a power of two
  uint8_t  prev   = takeSample(analog);
  uint16_t filled = 0;
  uint16_t waited = 0;
  bool     fired  = false;

  for (;;) {
    if (!waitTick(true)) return false;          // always abortable while searching
    uint8_t s = takeSample(analog);
    sampleBuf[head] = s;
    head = (head + 1) & mask;

    if (filled < pre) {                         // collect pre-trigger samples first
      filled++;
      prev = s;
      continue;
    }

    bool fire;
    switch (trigType) {
      case TRIG_RISING:  fire = !(prev & trigMask) &&  (s & trigMask); break;
      case TRIG_FALLING: fire =  (prev & trigMask) && !(s & trigMask); break;
      case TRIG_EDGE:    fire = ((prev ^ s) & trigMask) != 0;          break;
      case TRIG_HIGH:    fire =  (s & trigMask) != 0;                  break;
      default:           fire =  (s & trigMask) == 0;                  break; // LOW
    }
    prev = s;

    if (fire) { fired = true; break; }
    if (autoMode && (++waited >= n)) break;     // auto: give up, show free-run data
  }

  if (fired) {                                  // post-trigger samples
    uint16_t post = n - pre - 1;
    while (post--) {
      if (!waitTick(check)) return false;
      sampleBuf[head] = takeSample(analog);
      head = (head + 1) & mask;
    }
  }

  *headOut = head;
  *trigOut = fired;
  return true;
}

static bool captureDigitalFast(uint16_t n, uint16_t pre, uint8_t tt, uint8_t tm,
                               bool autoMode, uint16_t *head, bool *trig) {
  return captureEngine(false, false, n, pre, tt, tm, autoMode, head, trig);
}

static bool captureDigitalSlow(uint16_t n, uint16_t pre, uint8_t tt, uint8_t tm,
                               bool autoMode, uint16_t *head, bool *trig) {
  return captureEngine(false, true, n, pre, tt, tm, autoMode, head, trig);
}

static bool captureAnalog(uint16_t n, uint16_t pre, uint8_t tt, uint8_t tm,
                          bool autoMode, uint16_t *head, bool *trig) {
  return captureEngine(true, true, n, pre, tt, tm, autoMode, head, trig);
}

// ----------------------------------------------------------------------------
// Frame transmission
// ----------------------------------------------------------------------------
static void sendFrame(uint8_t flags, uint32_t rate, uint16_t n,
                      uint16_t trigPos, uint16_t head) {
  uint8_t hdr[11];
  hdr[0]  = 0xA5;
  hdr[1]  = 0x5A;
  hdr[2]  = flags;
  hdr[3]  = (uint8_t)(rate);
  hdr[4]  = (uint8_t)(rate >> 8);
  hdr[5]  = (uint8_t)(rate >> 16);
  hdr[6]  = (uint8_t)(rate >> 24);
  hdr[7]  = (uint8_t)(n);
  hdr[8]  = (uint8_t)(n >> 8);
  hdr[9]  = (uint8_t)(trigPos);
  hdr[10] = (uint8_t)(trigPos >> 8);

  uint8_t sum = 0;
  for (uint16_t i = 0; i < n; i++) sum += sampleBuf[i];   // order independent

  Serial.write(hdr, sizeof(hdr));
  Serial.write(&sampleBuf[head], (size_t)(n - head));     // oldest -> end of ring
  if (head) Serial.write(sampleBuf, (size_t)head);        // start of ring -> newest
  Serial.write(sum);
}

// ----------------------------------------------------------------------------
// Command handling
// ----------------------------------------------------------------------------
static bool parseArgs(char *p, long *out, uint8_t count) {
  for (uint8_t i = 0; i < count; i++) {
    while (*p == ' ') p++;
    if (*p == '\0') return false;
    char *end;
    out[i] = strtol(p, &end, 10);
    if (end == p) return false;
    p = end;
  }
  return true;
}

static void flushRx() {
  while (Serial.available()) Serial.read();
}

static void cmdStart(char *args) {
  long a[8];
  if (!parseArgs(args, a, 8)) { Serial.println(F("ERR ARGS")); return; }
  if (a[3] < 0 || a[3] > 5 || a[4] < 0 || a[4] > 7 || a[5] < 0 || a[5] > 90) {
    Serial.println(F("ERR RANGE"));
    return;
  }

  uint32_t rate    = (a[0] < 1) ? 1UL : (uint32_t)a[0];
  bool     analog  = (a[1] != 0);
  uint32_t thrMv   = (a[2] < 0) ? 0UL : ((a[2] > 5000) ? 5000UL : (uint32_t)a[2]);
  uint8_t  trigType = (uint8_t)a[3];
  uint8_t  trigMask = (uint8_t)(1U << (uint8_t)a[4]);
  uint8_t  prePct   = (uint8_t)a[5];
  bool     autoMode = (a[6] != 0);

  // Number of samples: largest power of two <= requested, 128..1024
  uint16_t n = MIN_SAMPLES;
  while ((uint32_t)n * 2UL <= (uint32_t)a[7] && (uint32_t)n * 2UL <= BUF_SIZE) n <<= 1;

  // Rate limits
  uint32_t maxRate = analog ? MAX_RATE_ANALOG
                            : ((trigType != TRIG_OFF) ? MAX_RATE_TRIGGER : MAX_RATE_DIGITAL);
  if (rate > maxRate) rate = maxRate;

  uint16_t pre = (uint16_t)(((uint32_t)n * prePct) / 100UL);
  if (pre > n - 2) pre = n - 2;

  analogThresholdCounts = (uint16_t)((thrMv * 1023UL) / 5000UL);

  Serial.flush();                               // let previous TX finish
  flushRx();

  if (analog) analogEnable();
  uint32_t actualRate = timerStart(rate);

  uint16_t head = 0;
  bool trig = false;
  bool ok;

  cli();                                        // no ISR jitter while sampling
  if (analog)                    ok = captureAnalog(n, pre, trigType, trigMask, autoMode, &head, &trig);
  else if (rate < SLOW_RATE)     ok = captureDigitalSlow(n, pre, trigType, trigMask, autoMode, &head, &trig);
  else                           ok = captureDigitalFast(n, pre, trigType, trigMask, autoMode, &head, &trig);
  sei();

  timerStop();
  if (analog) analogDisable();

  if (!ok) {                                    // aborted by the PC
    delay(3);                                   // let the rest of the abort command arrive
    flushRx();
    Serial.println(F("ABORT"));
    return;
  }

  uint8_t flags = (trig ? FLAG_TRIGGERED : 0) | (analog ? FLAG_ANALOG : 0);
  uint16_t trigPos = trig ? pre : 0xFFFF;
  sendFrame(flags, actualRate, n, trigPos, head);
}

static void handleLine(char *line) {
  switch (line[0]) {
    case 'I':                                   // ID
      Serial.println(F(FW_ID));
      break;
    case 'A':                                   // abort (nothing running)
      Serial.println(F("ABORT"));
      break;
    case 'S':                                   // start capture
      cmdStart(line + 1);
      break;
    default:
      Serial.println(F("ERR CMD"));
      break;
  }
}

static bool readLine() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      bool hasData = (lineLen > 0);
      lineBuf[lineLen] = '\0';
      lineLen = 0;
      if (hasData) return true;                 // ignore empty lines
      continue;
    }
    if (lineLen < LINE_MAX_LEN - 1) lineBuf[lineLen++] = c;
    else lineLen = 0;                           // line too long: discard
  }
  return false;
}

// ----------------------------------------------------------------------------
// Arduino entry points
// ----------------------------------------------------------------------------
void setup() {
  Serial.begin(SERIAL_BAUD);
  for (uint8_t pin = 2; pin <= 9; pin++) pinMode(pin, INPUT);      // digital inputs
  for (uint8_t pin = A0; pin <= A5; pin++) pinMode(pin, INPUT);    // analog inputs
}

void loop() {
  if (readLine()) handleLine(lineBuf);
}
