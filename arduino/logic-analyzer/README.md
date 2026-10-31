# 8-Channel Logic Analyzer with Arduino Uno R3

A low-cost logic analyzer made of:

- **Firmware** for the Arduino Uno R3 (`arduino_logic_analyzer/arduino_logic_analyzer.ino`): captures 8 digital channels in blocks of up to 1024 samples and sends them over USB.
- **PC application** in Python (`pc_gui/logic_analyzer_gui.py`): configures the capture, draws the waveforms and provides measurement and export tools.

The GUI and all code comments are in English.

```
logic_analyzer/
├── README.md
├── arduino_logic_analyzer/
│   └── arduino_logic_analyzer.ino     <- firmware (Arduino IDE)
└── pc_gui/
    ├── logic_analyzer_gui.py          <- PC application
    └── requirements.txt
```

---

## 1. Features

| Feature | Details |
|---|---|
| Channels | 8 inputs; each one can be enabled/disabled and **renamed** |
| Number conversion | "BUS" lane showing the value of the enabled channels in **binary, decimal, hexadecimal and octal**; also used in the cursor readout and the CSV |
| Time scale | **Configurable time/div** (1-2-5 list or typed value, e.g. `250us`, `1.5 ms`), 10 divisions |
| Zoom | Zoom +/−, Fit, "To cursors", mouse wheel (centered on the pointer), scroll bar, Pan buttons, middle-button drag |
| Cursors | Cursor A (left click) and B (right click or Shift+click), both draggable. They show ΔT, 1/ΔT, number of samples, and the bus value and each channel level at each cursor |
| Sample rate | Configurable from 1 Hz to 250 kHz (see limits) |
| Threshold | Analog mode with an adjustable 0–5 V threshold (see limitations) |
| Trigger | Rising edge, falling edge, any edge, high level, low level; selectable channel; 0–90 % pre-trigger; Auto/Normal mode |
| Control | Run (continuous), Single, Stop and **Pause display** (freezes the screen) |
| Export | **PNG** of the plot, **PDF** (light theme, print-friendly) and **CSV** with the data |
| DEMO mode | Simulated device to try the GUI without hardware |

---

## 2. Requirements

### Hardware
- Arduino Uno R3 (or a compatible board with an ATmega328P at 16 MHz) and a USB cable.
- Test leads/clips. **Always connect the ground of the circuit under test to the Arduino GND.**

### Software
- Arduino IDE 1.8.x / 2.x (or `arduino-cli`).
- Python 3.8 or later with Tkinter (on Debian/Ubuntu: `sudo apt install python3-tk`).
- Python libraries: `pyserial`, `numpy`, `matplotlib`.

---

## 3. Installation and usage

### 3.1 Firmware
1. Open `arduino_logic_analyzer/arduino_logic_analyzer.ino` in the Arduino IDE (the folder must have the same name as the `.ino` file).
2. Select **Arduino Uno** and the serial port, then click *Upload*.
3. Close the Serial Monitor if you opened it (the port must be free). The firmware runs at **500000 baud**.

### 3.2 PC application
```bash
cd pc_gui
python -m pip install -r requirements.txt
python logic_analyzer_gui.py
```
On Linux you may need permission to use the port: `sudo usermod -aG dialout $USER`, then log in again.

### 3.3 First capture
1. Choose the port and click **Connect** (the Arduino resets when the port is opened, so connecting takes ~2 s). To try the program without hardware, choose `DEMO (simulated device)`.
2. Set the **Sample rate** (rule of thumb: at least 5–10 times the highest signal frequency).
3. Click **Run** or **Single**.

### 3.4 Wiring

| Channel | Digital mode (fast) | Analog mode (adjustable threshold) |
|---|---|---|
| CH1 | D2 | A0 |
| CH2 | D3 | A1 |
| CH3 | D4 | A2 |
| CH4 | D5 | A3 |
| CH5 | D6 | A4 |
| CH6 | D7 | A5 |
| CH7 | D8 | D8 (digital) |
| CH8 | D9 | D9 (digital) |
| GND | GND | GND |

D0/D1 are used by the USB serial port.

> **Maximum input voltage: 5 V.** The Arduino inputs have no protection. For higher voltages use resistor dividers or level shifters; a 1–10 kΩ series resistor is recommended.
> The inputs have no pull-ups: an unconnected input floats and reads noise.

---

## 4. Interface guide

**Top bar:** port, baud rate (must match the firmware, 500000), Connect/Disconnect, Run, Single, Stop, Pause display, Save PNG, Export PDF, Export CSV.

**Channels:** enable/disable checkbox, color, editable name and associated pins. Names are used in the plot, in the cursor readout and in the CSV headers.

**Acquisition**
- *Sample rate*: accepts values such as `250k`, `100 kHz`, `500`. The firmware returns the actual rate obtained (shown in the plot title).
- *Samples*: 128, 256, 512 or 1024 samples.
- *Input mode*: digital (fast, fixed threshold) or analog (adjustable threshold).
- *Threshold (V)*: only active in analog mode.

**Trigger**
- *Type*: Off, Rising edge, Falling edge, Any edge, High level, Low level.
- *Channel*: the channel being monitored. *Pre-trigger (%)*: percentage of the buffer kept before the trigger event.
- *Mode*: **Auto** (if there is no trigger within one full buffer, the data is shown anyway) or **Normal** (waits indefinitely; cancel with Stop).
- With trigger enabled, the trigger instant is `t = 0` and is marked with a yellow "T" line. Without trigger, `t = 0` is the first sample.

**Display**
- *Time/div*: horizontal scale (10 divisions). It is also shown in the X-axis label.
- *Bus format*: numeric base of the BUS lane and of the readouts. Convention: **CH1 = bit 0 (LSB) … CH8 = bit 7 (MSB)**; disabled channels count as 0.
- *Light plot theme*: light theme (the PDF is always exported in light theme).

**Cursors and mouse**
- Left click: cursor A (draggable). Right click or Shift+click: cursor B.
- Wheel: zoom; Shift+wheel: pan; middle-button drag: pan.
- The bottom panel shows A, B, ΔT, 1/ΔT, number of samples, and the bus value (BIN/DEC/HEX/OCT) and every channel level at each cursor.

**Pause display:** freezes the screen (waveforms and values) so you can analyze it; acquisition keeps running in the background and the latest capture is shown when you resume. Exports use what is on screen.

**Export**
- *PNG*: saves the plot (not the whole window) at 150 dpi.
- *PDF*: vector plot in light theme.
- *CSV*: columns `Sample, Time_s, <enabled channels>, Value_BIN, Value_DEC, Value_HEX, Value_OCT`. Time is relative to the trigger (or to the first sample).

---

## 5. How it works

```
 Signals ──► Arduino Uno ──(USB serial, 500000 baud)──► Python GUI
             · Timer1 sets the sampling pace              · reader thread (frames)
             · 1024-byte buffer in SRAM                   · event queue → Tk
             · trigger + circular buffer                  · Matplotlib (drawing)
```

### 5.1 Firmware
- **Digital sampling:** `PIND` (D2–D7) and `PINB` (D8–D9) are read and packed into one byte: `(PIND >> 2) | (PINB << 6)`. Each channel is one bit, so all 8 channels are read at once with very few instructions.
- **Timing:** Timer1 in CTC mode generates the sample clock; the loop polls the `OCF1A` flag and takes the sample. The prescaler is chosen automatically to cover 1 Hz to 250 kHz. Interrupts are disabled during capture (no UART or `millis()` jitter).
- **Trigger and pre-trigger:** with trigger enabled, samples are written to a **circular buffer**. Once the pre-trigger samples have been collected and the condition is met, the remaining samples are captured and the buffer is sent in chronological order.
- **Cancellation:** while waiting for a trigger, or at slow rates (< 2 kHz), the firmware watches the serial port; any received byte (the PC sends `A`) aborts the capture.
- **Analog mode:** for A0–A5, one ADC conversion is made per channel (1 MHz ADC clock) and compared with the threshold, which the PC sends in mV.

### 5.2 Serial protocol
ASCII commands terminated with `\n`:

| Command | Reply |
|---|---|
| `ID` | `LA8 1.0 1024` |
| `A` | `ABORT` |
| `S <rate> <analog> <thr_mV> <trigType> <trigCh> <prePct> <auto> <count>` | one binary frame, or `ERR ...` / `ABORT` |

Frame (little endian): `A5 5A | flags(1) | actual_rate(4) | count(2) | trigPos(2) | data[count] | checksum(1)`. `flags`: bit0 = triggered, bit1 = analog mode. The checksum is the sum of the data bytes modulo 256. The PC resynchronizes and discards frames with a bad checksum.

### 5.3 PC application
- A **reader thread** separates text lines from binary frames and puts them in a queue; Tk polls it every 20 ms.
- A small state machine (`IDLE / ARMED / ABORTING`) arms captures, re-arms in Run mode and reconfigures when settings change during a capture.
- Drawing uses Matplotlib (`step` for the waveforms, `PolyCollection` for the bus). Bus values are labeled when the segment is wide enough (if the label does not fit with its `0x`/`0b`/`0o` prefix, it is shown without it).

---

## 6. Limitations

It is important to know these before trusting a measurement:

1. **Block capture, not continuous.** Only 1024 samples fit (2 KB SRAM). Between captures there is dead time (transfer + drawing, tens of ms), so events that happen between blocks are not seen.
2. **Maximum speed:** 250 kS/s without trigger, 125 kS/s with trigger and 5 kS/s in analog mode (the firmware limits the requested value and the GUI shows the real one). With a 1024-sample capture the window is short at high rates (4 ms at 250 kS/s). To see a signal properly, sample 5–10 times faster than its frequency: **it is not suitable for fast buses** (high-speed SPI/I²C, etc.). It is useful for UART, slow I²C/1-Wire, PWM, sensor signals and low-frequency logic.
3. **Threshold:** in digital mode the threshold is that of the ATmega328P at 5 V (low < ≈1.5 V, high > ≈3 V) and **cannot be adjusted**. A real adjustable threshold is only possible in analog mode, which:
   - covers only CH1–CH6 (A0–A5); CH7 and CH8 remain digital with a fixed threshold;
   - samples the channels sequentially, with about 13–15 µs of skew between channels, at a maximum of 5 kS/s;
   - has roughly 8 effective bits and uses AVcc (≈5 V from USB) as reference, so the absolute threshold has an error of a few tenths of a volt;
   - needs low-impedance sources (< 10 kΩ) and has no hysteresis (a noisy signal near the threshold may chatter).
   For 3.3 V logic in digital mode, the high level (≈3.3 V) is just above the 3 V minimum: it may work, but with little margin.
4. **Timing accuracy:** depends on the board oscillator (a crystal on the original Uno, but a ceramic resonator on many clones, which is less accurate). Resolution is the sampling period (e.g. 4 µs at 250 kS/s) and, while waiting for the trigger, there is up to ≈0.5 µs of sampling jitter.
5. **No input protection** or level adaptation: 5 V maximum.
6. **The PC can only cancel** a capture when a trigger is used, in analog mode, or at rates < 2 kHz. At high rates without trigger the capture (< 0.5 s) cannot be cancelled.
7. **Simple numeric bus:** the whole byte is interpreted (CH1 = LSB); there are no protocol decoders (UART, I²C, SPI…).
8. **"Pause" freezes the display**, it does not stop the acquisition on the Arduino (use Stop for that).
9. Boards with inexpensive USB-serial converters (CH340, etc.) normally accept 500000 baud; if not, lower `SERIAL_BAUD` in the firmware and the baud rate in the GUI to 250000 or 115200 (it works, only the transfer takes longer).

### Test status
- The firmware logic (channel packing, circular buffer, trigger/pre-trigger, checksum, rate limits, divider calculation) was verified by compiling it on a PC with simulated registers.
- The PC application was run against the simulated device (DEMO mode): protocol, captures, trigger, zoom, cursors and PNG/PDF/CSV exports.
- **It has not been tested on a real Arduino board**, and the sampling loop timing has not been measured with an oscilloscope. A first check with a known signal (e.g. a function generator at 1 kHz) is recommended and, if you want to run close to the 250 kS/s limit, verify the real rate.

---

## 7. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "No answer from the Arduino" | Firmware not uploaded, port busy (Serial Monitor open) or baud rate other than 500000 |
| Port does not appear | Missing driver (CH340/CP210x on clones), charge-only cable, or permissions (`dialout` on Linux) |
| Capture never triggers in Normal mode | The channel does not meet the condition; click Stop or use Auto mode |
| Noisy signals or erratic values | Unconnected (floating) input, missing common GND or long wires |
| "Missing" edges | Sample rate too low for the signal; increase it |
| `ModuleNotFoundError: tkinter` | Install your system's Tkinter package (`python3-tk`) |

---

## 8. Possible extensions

- Protocol decoders (UART, I²C, SPI) on the captured data.
- Deeper capture using external RAM or a board with more memory (e.g. an Arduino Mega, or a Raspberry Pi Pico for higher speeds).
- An external comparator (e.g. LM393 + filtered PWM) to get an adjustable threshold in fast mode too.
