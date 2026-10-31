# LabJack T7 Function Generator

A two-channel arbitrary function generator with a desktop GUI for the **LabJack T7**, built with Python, Tkinter and the LabJack LJM library. It uses the T7's hardware-timed **stream-out** feature to drive the two analog outputs (`DAC0` and `DAC1`) with continuous, jitter-free waveforms.

> **Status:** the signal-generation code (waveforms, sweep, burst, AM/FM, sample-rate planning) is covered by offline tests. The hardware layer follows the LabJack LJM documentation, but if you find a T7 firmware- or driver-specific problem, please open an issue (see [Troubleshooting](#troubleshooting)).

---

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Connecting the LabJack T7](#connecting-the-labjack-t7)
- [Usage](#usage)
- [How it works](#how-it-works)
- [Operating limits](#operating-limits)
- [Configuration constants](#configuration-constants)
- [Arbitrary waveform file format](#arbitrary-waveform-file-format)
- [Troubleshooting](#troubleshooting)
- [Project structure](#project-structure)
- [License](#license)

---

## Features

- **Two independent channels** (`DAC0`, `DAC1`) generated in sync from the same hardware stream clock.
- **Waveforms:** sine, square, triangle, sawtooth, reverse ramp, exponential rise, exponential fall, gaussian, sinc, noise, DC and arbitrary (CSV).
- **Per-channel parameters:** frequency, amplitude (Vpp), offset, phase, duty cycle / symmetry, signal inversion, output enable.
- **Modes:**
  | Mode | Description |
  |---|---|
  | Continuous | Standard periodic waveform |
  | Sweep | Linear or logarithmic frequency sweep (start frequency, stop frequency, sweep time) |
  | Burst | N cycles of the waveform followed by idle time, repeated every burst period |
  | AM | Amplitude modulation (modulating frequency, depth 0-100 %) |
  | FM | Frequency modulation (modulating frequency, peak deviation) |
- **Live preview** of each channel's waveform on a 0-5 V grid.
- **Clipping warning** when amplitude and offset exceed the DAC range.
- **Automatic apply** of parameter changes while the output is running (optional).
- **Save / load** the full configuration as a JSON file (including arbitrary waveforms).
- Safe shutdown: both DACs are set to 0 V when the output is switched off or the window is closed.

## Requirements

- A **LabJack T7** or T7-Pro, connected over USB, Ethernet or Wi-Fi.
- **Python 3.8+** with Tkinter (included in the standard Windows and macOS installers; on Debian/Ubuntu install `python3-tk`).
- The **LabJack LJM library** (driver), downloaded from the [LabJack software page](https://labjack.com/pages/support?doc=/software-driver/installer-downloads/ljm-software-installers-t4-t7-digit/).
- Python packages: `labjack-ljm` and `numpy`.

## Installation

1. Install the LabJack LJM driver for your operating system.
2. Clone the repository and install the Python dependencies:

   ```bash
   git clone https://github.com/<your-user>/<your-repo>.git
   cd <your-repo>
   pip install labjack-ljm numpy
   ```

3. Run the application:

   ```bash
   python function_generator_t7.py
   ```

## Connecting the LabJack T7

The program opens the first T7 it finds (`ljm.openS("T7", "ANY", "ANY")`), so it works with any connection type supported by LJM (USB, Ethernet, Wi-Fi). Close LabJack Kipling or any other program using the device before starting.

| Generator channel | T7 terminal | Reference |
|---|---|---|
| Channel 1 | `DAC0` | `GND` |
| Channel 2 | `DAC1` | `GND` |

Notes:

- Use the `GND` terminal next to the DAC terminals as the signal return.
- The DAC outputs are low-power signal outputs. If you need to drive a load, check the LabJack T7 datasheet for the DAC output current and impedance, and use a buffer or amplifier when required.
- Do not connect the outputs to voltages outside the T7 specified range.
- No other T7 terminals are used. The program uses `FIO_STATE` internally only as a dummy stream input channel (see [How it works](#how-it-works)); no physical pin needs to be connected.

## Usage

1. Start the program. It connects to the T7 and sets `DAC0` and `DAC1` to 0 V.
2. For each channel, tick **Output enabled** and choose a **Waveform** and **Mode**.
3. Enter the parameters. Fields that do not apply to the selected waveform/mode are greyed out.
4. Check the live preview and the status line at the bottom (sample rate, warnings, errors).
5. Press **OUTPUT: OFF** to start the generator; the button changes to **OUTPUT: ON**. Press it again to stop (outputs return to 0 V).
6. While running, changes are applied automatically after a short delay (400 ms). Untick *Apply changes automatically* and use **Apply now** if you prefer to apply them manually.

Because the T7 DAC cannot produce negative voltages, signals are defined as:

```
v(t) = offset + (Vpp / 2) * w(t)        with w(t) between -1 and +1
```

and the result must stay within **0 to 5 V**. For a sine wave of amplitude *A* Vpp centred in the range, use `offset = 2.5 V` and `Vpp <= 5 V`.

### Mode details

- **Sweep:** `Frequency` is the start frequency and `Stop frequency` the end. The whole sweep lasts `Sweep time` and then repeats.
- **Burst:** the waveform at `Frequency` is output for `Burst cycles` cycles, then the output stays at the offset level until `Burst period` has elapsed.
- **AM / FM:** `Frequency` is the carrier and `Modulating freq.` the modulating signal. The carrier is rounded to the nearest integer multiple of the modulating frequency so that the pattern repeats exactly.
- **Noise:** uniform white noise. It is a 2048-sample block that loops (about 10 times per second at the default settings), so it is pseudo-random, not truly continuous.
- **DC:** outputs a constant `offset` voltage (no stream is used if all enabled channels are DC).

## How it works

### Stream-out playback

1. For each enabled channel, the PC computes **one fundamental period** of the signal in `N` samples (`N` up to 2048). The fundamental period is `1/f` for continuous mode, the sweep time for sweeps, the burst period for bursts, and `1/f_mod` for AM/FM.
2. The samples are written to the T7 stream-out buffer (`STREAM_OUTn_BUFFER_F32`) and configured to loop (`STREAM_OUTn_LOOP_SIZE`, `STREAM_OUTn_SET_LOOP`). `STREAM_OUTn_TARGET` is set to the DAC register (`1000` for DAC0, `1002` for DAC1).
3. The stream is started with the common sample rate `fs`. From then on, the T7 updates the DACs by itself using its hardware clock, so the output does not depend on the PC's timing or CPU load.
4. A background thread keeps reading the stream so that the (dummy) stream-in buffer never overflows.

The output frequency is simply:

```
f_out = fs / N
```

### Sample-rate planning

Both channels share one stream clock, so one sample rate `fs` is chosen for both:

- The channel with the highest repetition frequency gets as many samples as possible (`N = min(2048, MAX_FS / f)`), which sets `fs = N * f`.
- The other channel uses `N2 = round(fs / f2)` samples. Its actual repetition frequency is `fs / N2`, which can differ very slightly from the requested one; the real value is shown under each preview.
- If a channel would need more than 2048 samples (very large frequency ratio between the channels), an error is shown.

### Application structure

| Part | Description |
|---|---|
| `waveform()`, `generate()`, `solve()` | Pure signal computation and sample-rate planning (no hardware access) |
| `Generator` | Hardware layer: configures stream-out, starts/stops the stream, reader thread |
| `Panel` | GUI for one channel (parameters, preview, arbitrary-waveform loader) |
| `App` | Main window: connection, start/stop, auto-apply, configuration save/load |

## Operating limits

Most limits come from the T7 hardware and from the way stream-out works, not from the software.

| Item | Limit |
|---|---|
| Output voltage | **0 to 5 V** only (no negative voltages) |
| DAC resolution | 12 bits (about 1.2 mV per step) |
| Number of channels | 2 (`DAC0`, `DAC1`) |
| Samples per period | 8 to 2048 |
| Maximum sample rate | `MAX_FS` = 20 000 samples/s (default, adjustable) |
| Maximum repetition frequency | `MAX_FS / 8` = **2.5 kHz** with default settings. A 2.5 kHz sine would only have 8 points per cycle; for good quality keep it well below this |
| Minimum sample rate | `MIN_FS` = 1 sample/s (lowest frequency about 0.0005 Hz with 2048 samples) |
| Frequency ratio between channels | The slower channel must fit in 2048 samples at the shared sample rate (about 1:2000 maximum, depending on the faster channel) |
| Sweep / AM / FM content | The highest instantaneous frequency must be at least 4 samples per cycle at the chosen sample rate; otherwise an error is shown |
| Waveform shape accuracy | Limited by the number of samples per period, especially at high frequency (e.g. a 1 kHz signal has 20 samples per cycle at 20 kS/s) |
| Signal quality | The output is a stepped DAC output with no reconstruction filter; add an external low-pass filter if a smooth analog signal is needed |
| Noise | Looping 2048-sample block, not an infinite random sequence |
| AM / FM carrier | Rounded to an integer multiple of the modulating frequency |

For comparison, benchtop function generators reach MHz frequencies and ±10 V or more. This project is intended for low-frequency stimulus generation, test signals and lab automation with a T7.

## Configuration constants

At the top of `function_generator_t7.py`:

| Constant | Default | Meaning |
|---|---|---|
| `V_MIN`, `V_MAX` | 0.0, 5.0 | T7 DAC range (volts) |
| `MAX_FS` | 20000 | Maximum stream-out sample rate (samples/s). Lower it (e.g. 10000) if you get stream errors or distorted output |
| `MIN_FS` | 1.0 | Minimum sample rate (samples/s) |
| `N_MAX` | 2048 | Maximum samples per period |
| `N_MIN` | 8 | Minimum samples per period |

## Arbitrary waveform file format

Choose **Arbitrary** as the waveform and load a text or CSV file:

- One value per line, or several columns (the **last numeric column** of each line is used, so `time,value` files work).
- Lines that are not numeric (headers) are ignored.
- At least 2 points are required. The data is centred and normalised to ±1, then interpolated, so the file defines the *shape*; amplitude and offset are set in the GUI.
- The waveform is stretched to exactly one period of the selected frequency.

Example:

```csv
0.0
0.5
1.0
0.5
0.0
-0.5
-1.0
-0.5
```

## Troubleshooting

| Problem | Possible cause / solution |
|---|---|
| *Could not connect to the T7* | LJM driver not installed, device not connected, or another program (e.g. Kipling) is using the T7 |
| Stream errors or distorted output | Lower `MAX_FS`; use a direct USB connection instead of Wi-Fi/Ethernet for high rates |
| *CHx clipped* warning | `offset - Vpp/2` is below 0 V or `offset + Vpp/2` is above 5 V; reduce amplitude or adjust offset |
| *Frequency too high* | The repetition frequency exceeds `MAX_FS / 8`; reduce the frequency or the modulation/sweep content |
| *Frequency ratio between channels is too large* | Bring the two channel frequencies closer together |
| Output stays at 0 V | Check that the channel's **Output enabled** box is ticked and the main button shows **OUTPUT: ON** |
| `ModuleNotFoundError: tkinter` on Linux | Install it with `sudo apt install python3-tk` |

If you find a problem that depends on the T7 firmware or the LJM version (for example, stream-out buffer size handling), please open an issue with your T7 firmware version, LJM version, operating system and the exact error message.

## Project structure

```
.
├── function_generator_t7.py   # Application (GUI + signal generation + T7 stream-out)
├── README.md
└── LICENSE
```
