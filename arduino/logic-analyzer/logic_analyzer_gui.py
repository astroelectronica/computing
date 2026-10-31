#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
8-Channel Logic Analyzer - PC application (Arduino Uno R3)
==========================================================

GUI for the firmware "arduino_logic_analyzer.ino".

Main features
  * 8 channels, individual enable/disable and editable names
  * Bus view with Binary / Decimal / Hexadecimal / Octal conversion
  * Time/div scale (editable), zoom, pan, fit, zoom to cursors
  * Two measurement cursors (A and B) with delta-time and frequency
  * Sample rate, input mode (digital / analog with adjustable threshold)
  * Trigger: rising, falling, any edge, high, low; pre-trigger; auto/normal
  * Run / Single / Stop / Pause (freeze display)
  * Export: PNG image, PDF (light theme) and CSV data
  * Built-in simulated device ("DEMO") to try the GUI without hardware

Dependencies: pyserial, numpy, matplotlib (tkinter ships with Python).
"""

import csv
import datetime
import math
import queue
import re
import struct
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.collections import PolyCollection                # noqa: E402
from matplotlib.figure import Figure                             # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator     # noqa: E402

try:
    import serial
    import serial.tools.list_ports
except ImportError:  # the GUI still works in DEMO mode
    serial = None

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
APP_TITLE = "8-Channel Logic Analyzer (Arduino Uno R3)"
NUM_CH = 8
DEFAULT_BAUD = 500000            # must match SERIAL_BAUD in the firmware
MAGIC = b"\xA5\x5A"
HEADER_LEN = 11                  # magic(2) flags(1) rate(4) count(2) trigPos(2)
DEMO_PORT = "DEMO (simulated device)"

PIN_LABELS = ["D2 / A0", "D3 / A1", "D4 / A2", "D5 / A3",
              "D6 / A4", "D7 / A5", "D8", "D9"]

TRIG_TYPES = ["Off", "Rising edge", "Falling edge", "Any edge",
              "High level", "Low level"]
TRIG_MODES = ["Auto", "Normal"]
BASES = ["Binary", "Decimal", "Hexadecimal", "Octal"]
INPUT_MODES = ["Digital - fast (D2-D9, TTL threshold)",
               "Analog - adjustable threshold (A0-A5, D8-D9)"]
SAMPLE_COUNTS = ["128", "256", "512", "1024"]
RATE_PRESETS = ["10 Hz", "100 Hz", "500 Hz", "1 kHz", "2 kHz", "5 kHz",
                "10 kHz", "20 kHz", "50 kHz", "100 kHz", "125 kHz",
                "200 kHz", "250 kHz"]

T_DIV_MIN = 1e-7
T_DIV_MAX = 1e3
DIVISIONS = 10

THEMES = {
    "dark": {
        "fig": "#1b1d23", "axes": "#101216", "grid": "#2c313a",
        "text": "#d7dae0", "nodata": "#171a1f",
        "curA": "#ff5252", "curB": "#40c4ff", "trig": "#ffeb3b",
        "colors": ["#ffd600", "#ff9100", "#00e676", "#40c4ff",
                   "#e040fb", "#ff5252", "#b2ff59", "#18ffff"],
    },
    "light": {
        "fig": "#ffffff", "axes": "#ffffff", "grid": "#d0d0d0",
        "text": "#202020", "nodata": "#eeeeee",
        "curA": "#d50000", "curB": "#0277bd", "trig": "#f9a825",
        "colors": ["#b38f00", "#e65100", "#2e7d32", "#0277bd",
                   "#8e24aa", "#c62828", "#558b2f", "#00838f"],
    },
}


# ----------------------------------------------------------------------------
# Helpers: formatting and parsing
# ----------------------------------------------------------------------------
def fmt_time(t, digits=3):
    """Format a time in seconds using s / ms / us / ns."""
    a = abs(t)
    if a < 1e-12:
        return "0 s"
    if a >= 0.9999:
        v, u = t, "s"
    elif a >= 0.9999e-3:
        v, u = t * 1e3, "ms"
    elif a >= 0.9999e-6:
        v, u = t * 1e6, "\u00b5s"
    else:
        v, u = t * 1e9, "ns"
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return f"{s} {u}"


def fmt_freq(f):
    """Format a frequency in Hz using Hz / kHz / MHz."""
    if f >= 1e6:
        s, u = f / 1e6, "MHz"
    elif f >= 1e3:
        s, u = f / 1e3, "kHz"
    else:
        s, u = f, "Hz"
    return f"{s:.4g} {u}"


def fmt_rate(r):
    return fmt_freq(r).replace("Hz", "S/s")


def parse_time(text):
    """Parse '200us', '1 ms', '0.5', '2e-3 s' ... into seconds (default unit: s)."""
    m = re.fullmatch(
        r"\s*([0-9]*\.?[0-9]+(?:[eE][+-]?\d+)?)\s*(ns|us|\u00b5s|ms|s)?\s*(?:/\s*div)?\s*",
        text.strip(), flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"Invalid time value: '{text}'")
    val = float(m.group(1))
    unit = (m.group(2) or "s").lower()
    scale = {"ns": 1e-9, "us": 1e-6, "\u00b5s": 1e-6, "ms": 1e-3, "s": 1.0}[unit]
    val *= scale
    if val <= 0:
        raise ValueError("Time must be greater than zero")
    return val


def parse_rate(text):
    """Parse '250k', '100 kHz', '1M', '500' ... into Hz."""
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*([kKmM]?)\s*(?:hz|s/s|sps)?\s*",
                     text.strip(), flags=re.IGNORECASE)
    if not m:
        raise ValueError(f"Invalid sample rate: '{text}'")
    val = float(m.group(1))
    mult = {"": 1.0, "k": 1e3, "m": 1e6}[m.group(2).lower()]
    val *= mult
    if val < 1:
        raise ValueError("Sample rate must be at least 1 Hz")
    return val


def nice_ceil(x):
    """Smallest 1-2-5 value >= x."""
    if x <= 0:
        return 1e-3
    base = 10.0 ** math.floor(math.log10(x))
    for m in (1, 2, 5, 10):
        if m * base >= x * 0.999999:
            return m * base
    return 10 * base


def fmt_value(v, base, prefix=True):
    """Format an 8-bit value in the chosen numeric base (optionally without prefix)."""
    v = int(v)
    if base == "Binary":
        return f"{'0b' if prefix else ''}{v:08b}"
    if base == "Decimal":
        return str(v)
    if base == "Hexadecimal":
        return f"{'0x' if prefix else ''}{v:02X}"
    return f"{'0o' if prefix else ''}{v:03o}"


def time_div_presets():
    vals = []
    for e in range(-7, 2):
        for m in (1, 2, 5):
            vals.append(m * 10.0 ** e)
    return [fmt_time(v) for v in vals if v <= 50]


# ----------------------------------------------------------------------------
# Capture data model
# ----------------------------------------------------------------------------
class Capture:
    """One acquired block of samples (one byte per sample, bit n = channel n+1)."""

    def __init__(self, data, rate, trig_idx=0, triggered=False, analog=False):
        self.data = np.frombuffer(bytes(data), dtype=np.uint8).copy()
        self.rate = float(rate)
        self.triggered = bool(triggered)
        self.trig_idx = int(trig_idx) if triggered else 0
        self.analog = bool(analog)
        self.timestamp = datetime.datetime.now()

    @property
    def n(self):
        return len(self.data)

    @property
    def dt(self):
        return 1.0 / self.rate

    @property
    def duration(self):
        return self.n * self.dt

    @property
    def t_min(self):
        return -self.trig_idx * self.dt

    @property
    def t_max(self):
        return (self.n - self.trig_idx) * self.dt

    def times(self):
        return (np.arange(self.n) - self.trig_idx) * self.dt

    def index_at(self, t):
        i = int(math.floor((t - self.t_min) / self.dt + 1e-9))
        return min(max(i, 0), self.n - 1)


# ----------------------------------------------------------------------------
# Serial stream parser (text lines + binary frames)
# ----------------------------------------------------------------------------
class StreamParser:
    """Splits the incoming byte stream into text lines and binary frames."""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, chunk):
        self.buf += chunk
        events = []
        while True:
            m = self.buf.find(MAGIC)
            nl = self.buf.find(b"\n")
            if m == -1 and nl == -1:
                if len(self.buf) > 8192:          # runaway garbage
                    del self.buf[:-16]
                break
            if nl != -1 and (m == -1 or nl < m):  # a text line comes first
                line = bytes(self.buf[:nl]).decode("ascii", "replace").strip()
                del self.buf[:nl + 1]
                if line:
                    events.append(("line", line))
                continue
            if m > 0:                              # drop garbage before the frame
                del self.buf[:m]
            if len(self.buf) < HEADER_LEN:
                break
            flags, rate, count, tpos = struct.unpack_from("<BIHH", self.buf, 2)
            if count == 0 or count > 4096:         # not a valid header: resync
                del self.buf[:2]
                continue
            total = HEADER_LEN + count + 1
            if len(self.buf) < total:
                break
            payload = bytes(self.buf[HEADER_LEN:HEADER_LEN + count])
            chk = self.buf[HEADER_LEN + count]
            del self.buf[:total]
            if (sum(payload) & 0xFF) == chk:
                events.append(("frame", flags, rate, count, tpos, payload))
            else:
                events.append(("error", "Checksum error in received frame"))
        return events


# ----------------------------------------------------------------------------
# Device links: real serial port and simulated device
# ----------------------------------------------------------------------------
class SerialLink:
    """Reads the serial port in a background thread and emits parsed events."""

    def __init__(self, ser, on_event):
        self.ser = ser
        self.on_event = on_event
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def send(self, text):
        self.ser.write((text + "\n").encode("ascii"))

    def _run(self):
        parser = StreamParser()
        while not self._stop.is_set():
            try:
                data = self.ser.read(max(1, self.ser.in_waiting))
            except Exception as exc:  # port unplugged, etc.
                self.on_event(("link_error", str(exc)))
                break
            if data:
                for ev in parser.feed(data):
                    self.on_event(ev)

    def close(self):
        self._stop.set()
        try:
            self._thread.join(timeout=0.5)
        except RuntimeError:
            pass
        try:
            self.ser.close()
        except Exception:
            pass


def demo_signal(total, rng):
    """Synthetic 8-channel test signal (CH1-4 counter, PWM, UART-like, ...)."""
    i = np.arange(total)
    d = ((i // 4) & 0x0F).astype(np.uint8)                       # CH1-CH4 counter
    d |= ((i % 40) < 10).astype(np.uint8) << 4                   # CH5 PWM 25 %
    bits = np.array([1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
    d |= np.repeat(bits, 8)[i % 128].astype(np.uint8) << 5       # CH6 UART 0xA5
    d |= (((i // 50) & 1).astype(np.uint8)) << 6                 # CH7 slow clock
    glitch = (rng.random(total) < 0.01).astype(np.uint8)         # CH8 glitches
    glitch = (np.convolve(glitch, [1, 1, 1], mode="same") > 0).astype(np.uint8)
    d |= glitch << 7
    return d


class DemoLink:
    """Simulated device that speaks the same protocol as the firmware."""

    def __init__(self, on_event):
        self.on_event = on_event
        self._cancel = threading.Event()
        self._busy = False
        self._rng = np.random.default_rng()

    def start(self):
        pass

    def send(self, text):
        parts = text.split()
        if not parts:
            return
        cmd = parts[0]
        if cmd == "ID":
            self.on_event(("line", "LA8 1.0 1024 DEMO"))
        elif cmd == "A":
            if self._busy:
                self._cancel.set()
            else:
                self.on_event(("line", "ABORT"))
        elif cmd == "S":
            try:
                args = [int(float(x)) for x in parts[1:9]]
                if len(args) != 8:
                    raise ValueError
            except ValueError:
                self.on_event(("line", "ERR ARGS"))
                return
            self._busy = True
            self._cancel.clear()
            threading.Thread(target=self._capture, args=(args,), daemon=True).start()
        else:
            self.on_event(("line", "ERR CMD"))

    def _capture(self, a):
        rate, analog, _thr, tt, tch, pct, auto, count = a
        n = 128
        while n * 2 <= count and n * 2 <= 1024:
            n *= 2
        max_rate = 5000 if analog else (125000 if tt else 250000)
        rate = max(1, min(rate, max_rate))
        pre = min(n * pct // 100, n - 2)

        total = 4 * n + 256
        phase = int(self._rng.integers(0, 128))
        sig = demo_signal(total + phase, self._rng)[phase:]
        trig_at = None
        if tt:
            bit = (sig >> tch) & 1
            for j in range(max(pre, 1), total - (n - pre - 1)):
                p, c = bit[j - 1], bit[j]
                if ((tt == 1 and p == 0 and c == 1) or (tt == 2 and p == 1 and c == 0)
                        or (tt == 3 and p != c) or (tt == 4 and c == 1)
                        or (tt == 5 and c == 0)):
                    trig_at = j
                    break

        wait = min(n / rate, 0.3)
        if tt and trig_at is None and not auto:
            # "Normal" mode with no trigger event: wait until aborted
            self._cancel.wait()
            wait = 0
        else:
            self._cancel.wait(wait)

        self._busy = False
        if self._cancel.is_set():
            self._cancel.clear()
            self.on_event(("line", "ABORT"))
            return
        if trig_at is not None:
            data = sig[trig_at - pre: trig_at - pre + n]
            flags, tpos = 0x01, pre
        else:
            data = sig[:n]
            flags, tpos = 0x00, 0xFFFF
        if analog:
            flags |= 0x02
        self.on_event(("frame", flags, rate, n, tpos, bytes(data.astype(np.uint8))))

    def close(self):
        self._cancel.set()


# ----------------------------------------------------------------------------
# Main application
# ----------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1440x880")
        root.minsize(1100, 720)

        # ---- runtime state
        self.events = queue.Queue()
        self.link = None
        self.link_state = "IDLE"          # IDLE | ARMED | ABORTING
        self.acq_mode = "stop"            # stop | single | run
        self.last_cmd = None
        self.capture = None               # capture shown on screen
        self.latest = None                # newest capture received
        self.cursors = {"A": None, "B": None}
        self.t_div = 1e-3
        self.t_start = 0.0
        self.max_samples = 1024
        self._last_sig = None
        self._redraw_job = None
        self._scale_guard = False
        self._drag = None
        self._pan = None

        # ---- Tk variables
        self.port_var = tk.StringVar()
        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUD))
        self.ch_enabled = [tk.BooleanVar(value=True) for _ in range(NUM_CH)]
        self.ch_names = [tk.StringVar(value=f"CH{i + 1}") for i in range(NUM_CH)]
        self.rate_var = tk.StringVar(value="100 kHz")
        self.samples_var = tk.StringVar(value="1024")
        self.mode_var = tk.StringVar(value=INPUT_MODES[0])
        self.thr_var = tk.StringVar(value="1.65")
        self.trig_type_var = tk.StringVar(value=TRIG_TYPES[0])
        self.trig_ch_var = tk.StringVar(value="CH1")
        self.pre_var = tk.StringVar(value="20")
        self.trig_mode_var = tk.StringVar(value=TRIG_MODES[0])
        self.tdiv_var = tk.StringVar(value=fmt_time(self.t_div))
        self.base_var = tk.StringVar(value="Hexadecimal")
        self.show_bus_var = tk.BooleanVar(value=True)
        self.light_var = tk.BooleanVar(value=False)
        self.paused_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Not connected.")
        self.conn_var = tk.StringVar(value="Disconnected")

        self._build_ui()
        self.refresh_ports()
        self.update_widget_states()
        self.update_buttons()
        self.update_measure()
        self.redraw()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(20, self.poll_events)

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        root = self.root

        # ---------------- top toolbar
        top = ttk.Frame(root, padding=(6, 4))
        top.pack(side="top", fill="x")

        ttk.Label(top, text="Port:").pack(side="left")
        self.port_cb = ttk.Combobox(top, textvariable=self.port_var, width=30,
                                    state="readonly")
        self.port_cb.pack(side="left", padx=(2, 2))
        ttk.Button(top, text="Refresh", width=8, command=self.refresh_ports).pack(side="left")
        ttk.Label(top, text="  Baud:").pack(side="left")
        ttk.Combobox(top, textvariable=self.baud_var, width=8,
                     values=["115200", "250000", "500000", "1000000"]).pack(side="left")
        self.connect_btn = ttk.Button(top, text="Connect", width=11, command=self.toggle_connect)
        self.connect_btn.pack(side="left", padx=6)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=6)

        self.run_btn = ttk.Button(top, text="\u25b6 Run", width=8, command=lambda: self.start_acq("run"))
        self.run_btn.pack(side="left", padx=1)
        self.single_btn = ttk.Button(top, text="Single", width=8, command=lambda: self.start_acq("single"))
        self.single_btn.pack(side="left", padx=1)
        self.stop_btn = ttk.Button(top, text="\u25a0 Stop", width=8, command=self.stop_acq)
        self.stop_btn.pack(side="left", padx=1)
        self.pause_btn = ttk.Checkbutton(top, text="Pause display", style="Toolbutton",
                                         variable=self.paused_var, command=self.on_pause)
        self.pause_btn.pack(side="left", padx=6)

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Button(top, text="Save PNG", command=self.export_png).pack(side="left", padx=1)
        ttk.Button(top, text="Export PDF", command=self.export_pdf).pack(side="left", padx=1)
        ttk.Button(top, text="Export CSV", command=self.export_csv).pack(side="left", padx=1)

        ttk.Label(top, textvariable=self.conn_var, foreground="#555555").pack(side="right", padx=6)

        # ---------------- status bar (bottom)
        status = ttk.Frame(root, padding=(6, 2))
        status.pack(side="bottom", fill="x")
        ttk.Label(status, textvariable=self.status_var).pack(side="left")

        # ---------------- body
        body = ttk.Frame(root)
        body.pack(side="top", fill="both", expand=True)

        side = ttk.Frame(body, padding=(6, 2))
        side.pack(side="left", fill="y")
        main = ttk.Frame(body)
        main.pack(side="left", fill="both", expand=True)

        self._build_side_panel(side)
        self._build_plot_area(main)

    def _build_side_panel(self, side):
        # ---- Channels
        ch_f = ttk.LabelFrame(side, text="Channels", padding=4)
        ch_f.pack(fill="x", pady=(0, 4))
        light_cols = THEMES["light"]["colors"]
        for i in range(NUM_CH):
            ttk.Checkbutton(ch_f, variable=self.ch_enabled[i],
                            command=self.schedule_redraw).grid(row=i, column=0)
            tk.Label(ch_f, text="\u25a0", fg=light_cols[i], font=("TkDefaultFont", 12)
                     ).grid(row=i, column=1)
            e = ttk.Entry(ch_f, textvariable=self.ch_names[i], width=14)
            e.grid(row=i, column=2, padx=2, pady=1)
            self.ch_names[i].trace_add("write", lambda *_: self.on_names_changed())
            ttk.Label(ch_f, text=PIN_LABELS[i], foreground="#666666").grid(row=i, column=3, padx=4)
        bf = ttk.Frame(ch_f)
        bf.grid(row=NUM_CH, column=0, columnspan=4, pady=(4, 0))
        ttk.Button(bf, text="All on", width=8, command=lambda: self.set_all_channels(True)).pack(side="left", padx=2)
        ttk.Button(bf, text="All off", width=8, command=lambda: self.set_all_channels(False)).pack(side="left", padx=2)

        # ---- Acquisition
        acq = ttk.LabelFrame(side, text="Acquisition", padding=4)
        acq.pack(fill="x", pady=4)
        ttk.Label(acq, text="Sample rate:").grid(row=0, column=0, sticky="w")
        self.rate_cb = ttk.Combobox(acq, textvariable=self.rate_var, values=RATE_PRESETS, width=12)
        self.rate_cb.grid(row=0, column=1, sticky="w", pady=1)
        self._cfg_bind(self.rate_cb)
        ttk.Label(acq, text="Samples:").grid(row=1, column=0, sticky="w")
        self.samples_cb = ttk.Combobox(acq, textvariable=self.samples_var, values=SAMPLE_COUNTS,
                                       width=12, state="readonly")
        self.samples_cb.grid(row=1, column=1, sticky="w", pady=1)
        self._cfg_bind(self.samples_cb)
        ttk.Label(acq, text="Input mode:").grid(row=2, column=0, sticky="w")
        self.mode_cb = ttk.Combobox(acq, textvariable=self.mode_var, values=INPUT_MODES,
                                    width=40, state="readonly")
        self.mode_cb.grid(row=3, column=0, columnspan=2, sticky="w", pady=1)
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e: (self.update_widget_states(),
                                                             self.on_config_changed()))
        ttk.Label(acq, text="Threshold (V):").grid(row=4, column=0, sticky="w")
        self.thr_sp = ttk.Spinbox(acq, textvariable=self.thr_var, from_=0.0, to=5.0,
                                  increment=0.05, width=8, format="%.2f",
                                  command=self.on_config_changed)
        self.thr_sp.grid(row=4, column=1, sticky="w", pady=1)
        self._cfg_bind(self.thr_sp)
        ttk.Label(acq, text="Max: 250 kS/s digital (125 kS/s with trigger),\n5 kS/s analog.",
                  foreground="#666666").grid(row=5, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # ---- Trigger
        trg = ttk.LabelFrame(side, text="Trigger", padding=4)
        trg.pack(fill="x", pady=4)
        ttk.Label(trg, text="Type:").grid(row=0, column=0, sticky="w")
        self.trig_type_cb = ttk.Combobox(trg, textvariable=self.trig_type_var, values=TRIG_TYPES,
                                         width=14, state="readonly")
        self.trig_type_cb.grid(row=0, column=1, sticky="w", pady=1)
        self.trig_type_cb.bind("<<ComboboxSelected>>", lambda e: (self.update_widget_states(),
                                                                  self.on_config_changed()))
        ttk.Label(trg, text="Channel:").grid(row=1, column=0, sticky="w")
        self.trig_ch_cb = ttk.Combobox(trg, textvariable=self.trig_ch_var,
                                       values=[f"CH{i + 1}" for i in range(NUM_CH)],
                                       width=14, state="readonly")
        self.trig_ch_cb.grid(row=1, column=1, sticky="w", pady=1)
        self._cfg_bind(self.trig_ch_cb)
        ttk.Label(trg, text="Pre-trigger (%):").grid(row=2, column=0, sticky="w")
        self.pre_sp = ttk.Spinbox(trg, textvariable=self.pre_var, from_=0, to=90, increment=5,
                                  width=8, command=self.on_config_changed)
        self.pre_sp.grid(row=2, column=1, sticky="w", pady=1)
        self._cfg_bind(self.pre_sp)
        ttk.Label(trg, text="Mode:").grid(row=3, column=0, sticky="w")
        self.trig_mode_cb = ttk.Combobox(trg, textvariable=self.trig_mode_var, values=TRIG_MODES,
                                         width=14, state="readonly")
        self.trig_mode_cb.grid(row=3, column=1, sticky="w", pady=1)
        self._cfg_bind(self.trig_mode_cb)

        # ---- Display
        dsp = ttk.LabelFrame(side, text="Display", padding=4)
        dsp.pack(fill="x", pady=4)
        ttk.Label(dsp, text="Time/div:").grid(row=0, column=0, sticky="w")
        self.tdiv_cb = ttk.Combobox(dsp, textvariable=self.tdiv_var, values=time_div_presets(), width=12)
        self.tdiv_cb.grid(row=0, column=1, sticky="w", pady=1)
        for ev in ("<<ComboboxSelected>>", "<Return>", "<FocusOut>"):
            self.tdiv_cb.bind(ev, self.on_tdiv_entered)
        zf = ttk.Frame(dsp)
        zf.grid(row=1, column=0, columnspan=2, pady=3)
        ttk.Button(zf, text="Zoom +", width=8, command=lambda: self.zoom(0.5)).grid(row=0, column=0, padx=1, pady=1)
        ttk.Button(zf, text="Zoom \u2212", width=8, command=lambda: self.zoom(2.0)).grid(row=0, column=1, padx=1, pady=1)
        ttk.Button(zf, text="Fit", width=8, command=self.zoom_fit).grid(row=0, column=2, padx=1, pady=1)
        ttk.Button(zf, text="\u25c0 Pan", width=8, command=lambda: self.pan(-0.25)).grid(row=1, column=0, padx=1, pady=1)
        ttk.Button(zf, text="Pan \u25b6", width=8, command=lambda: self.pan(0.25)).grid(row=1, column=1, padx=1, pady=1)
        ttk.Button(zf, text="To cursors", width=8, command=self.zoom_to_cursors).grid(row=1, column=2, padx=1, pady=1)
        ttk.Label(dsp, text="Bus format:").grid(row=2, column=0, sticky="w")
        base_cb = ttk.Combobox(dsp, textvariable=self.base_var, values=BASES, width=12, state="readonly")
        base_cb.grid(row=2, column=1, sticky="w", pady=1)
        base_cb.bind("<<ComboboxSelected>>", lambda e: (self.update_measure(), self.schedule_redraw()))
        ttk.Checkbutton(dsp, text="Show bus lane (enabled channels)", variable=self.show_bus_var,
                        command=self.schedule_redraw).grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(dsp, text="Light plot theme", variable=self.light_var,
                        command=self.schedule_redraw).grid(row=4, column=0, columnspan=2, sticky="w")

        # ---- Cursors
        cur = ttk.LabelFrame(side, text="Cursors", padding=4)
        cur.pack(fill="x", pady=4)
        ttk.Button(cur, text="Clear cursors", command=self.clear_cursors).pack(anchor="w")
        ttk.Label(cur, justify="left", foreground="#666666",
                  text=("Left click: cursor A (drag to move)\n"
                        "Right click / Shift+click: cursor B\n"
                        "Wheel: zoom   Shift+wheel: pan\n"
                        "Middle-button drag: pan")).pack(anchor="w", pady=(4, 0))

    def _build_plot_area(self, main):
        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.115, right=0.995, top=0.94, bottom=0.095)
        self.canvas = FigureCanvasTkAgg(self.fig, master=main)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        self.scale = ttk.Scale(main, from_=0.0, to=1.0, orient="horizontal",
                               command=self.on_scale_moved)
        self.scale.pack(side="top", fill="x", padx=8)

        self.measure_lbl = tk.Label(main, text="", justify="left", anchor="w",
                                    font=("Courier", 9), bg="#f4f4f4", relief="groove", padx=6, pady=3)
        self.measure_lbl.pack(side="top", fill="x", padx=4, pady=4)

        c = self.canvas
        c.mpl_connect("button_press_event", self.on_press)
        c.mpl_connect("button_release_event", self.on_release)
        c.mpl_connect("motion_notify_event", self.on_motion)
        c.mpl_connect("scroll_event", self.on_scroll)
        c.mpl_connect("resize_event", lambda e: self.schedule_redraw())

    def _cfg_bind(self, widget):
        for ev in ("<<ComboboxSelected>>", "<Return>", "<FocusOut>"):
            widget.bind(ev, self.on_config_changed, add="+")

    # ------------------------------------------------------ widget states --
    def update_widget_states(self):
        analog = self.mode_var.get() == INPUT_MODES[1]
        self.thr_sp.configure(state="normal" if analog else "disabled")
        trig_on = self.trig_type_var.get() != TRIG_TYPES[0]
        st = "readonly" if trig_on else "disabled"
        self.trig_ch_cb.configure(state=st)
        self.trig_mode_cb.configure(state=st)
        self.pre_sp.configure(state="normal" if trig_on else "disabled")

    def update_buttons(self):
        connected = self.link is not None
        self.run_btn.configure(state="normal" if connected else "disabled")
        self.single_btn.configure(state="normal" if connected else "disabled")
        self.stop_btn.configure(state="normal" if connected and self.acq_mode != "stop" else "disabled")
        self.connect_btn.configure(text="Disconnect" if connected else "Connect")

    def on_names_changed(self):
        self.update_measure()
        self.schedule_redraw()

    def set_all_channels(self, value):
        for v in self.ch_enabled:
            v.set(value)
        self.update_measure()
        self.schedule_redraw()

    def set_status(self, text):
        self.status_var.set(text)

    # ------------------------------------------------------- connection ----
    def refresh_ports(self):
        ports = [DEMO_PORT]
        if serial is not None:
            ports = [p.device for p in serial.tools.list_ports.comports()] + ports
        self.port_cb["values"] = ports
        if self.port_var.get() not in ports:
            self.port_var.set(ports[0])

    def toggle_connect(self):
        if self.link is not None:
            self.disconnect()
            return
        port = self.port_var.get()
        if port == DEMO_PORT:
            self.link = DemoLink(self.events.put)
            self.link.start()
            self.on_connected("DEMO")
            return
        if serial is None:
            messagebox.showerror("pyserial missing",
                                 "Install pyserial (pip install pyserial) or use the DEMO port.")
            return
        try:
            baud = int(self.baud_var.get())
        except ValueError:
            messagebox.showerror("Invalid baud rate", "The baud rate must be an integer.")
            return
        self.connect_btn.configure(state="disabled")
        self.set_status(f"Connecting to {port} (the Arduino resets when the port opens, ~2 s)...")
        threading.Thread(target=self._connect_worker, args=(port, baud), daemon=True).start()

    def _connect_worker(self, port, baud):
        try:
            ser = serial.Serial(port, baud, timeout=0.1)
            time.sleep(2.0)                      # Uno auto-reset + bootloader
            ser.reset_input_buffer()
            parser = StreamParser()
            info = None
            for _ in range(3):
                ser.write(b"ID\n")
                t_end = time.time() + 1.0
                while time.time() < t_end and info is None:
                    for ev in parser.feed(ser.read(max(1, ser.in_waiting))):
                        if ev[0] == "line" and ev[1].startswith("LA8"):
                            info = ev[1]
                if info:
                    break
            if info is None:
                ser.close()
                self.events.put(("connect_failed",
                                 "No answer from the Arduino. Check that the firmware is "
                                 "uploaded and that the baud rate is 500000."))
                return
            link = SerialLink(ser, self.events.put)
            link.start()
            self.events.put(("connected", link, info))
        except Exception as exc:
            self.events.put(("connect_failed", str(exc)))

    def on_connected(self, info):
        self.conn_var.set(f"Connected: {info}")
        self.set_status("Connected. Press Run or Single.")
        m = re.match(r"LA8\s+\S+\s+(\d+)", info)
        if m:
            self.max_samples = int(m.group(1))
        self.samples_cb["values"] = [s for s in SAMPLE_COUNTS if int(s) <= self.max_samples]
        self.connect_btn.configure(state="normal")
        self.link_state = "IDLE"
        self.acq_mode = "stop"
        self.update_buttons()

    def disconnect(self):
        if self.link is not None:
            if self.link_state == "ARMED":
                try:
                    self.link.send("A")
                except Exception:
                    pass
            self.link.close()
        self.link = None
        self.link_state = "IDLE"
        self.acq_mode = "stop"
        self.conn_var.set("Disconnected")
        self.set_status("Disconnected.")
        self.connect_btn.configure(state="normal")
        self.update_buttons()

    def on_close(self):
        self.disconnect()
        self.root.destroy()

    # ---------------------------------------------------- acquisition -------
    def build_start_cmd(self, silent=False):
        try:
            rate = parse_rate(self.rate_var.get())
            analog = 1 if self.mode_var.get() == INPUT_MODES[1] else 0
            thr = float(self.thr_var.get().replace(",", "."))
            if not 0.0 <= thr <= 5.0:
                raise ValueError("The threshold must be between 0 and 5 V")
            tt = TRIG_TYPES.index(self.trig_type_var.get())
            tch = int(self.trig_ch_var.get()[2:]) - 1
            pre = int(float(self.pre_var.get()))
            if not 0 <= pre <= 90:
                raise ValueError("Pre-trigger must be between 0 and 90 %")
            auto = 1 if self.trig_mode_var.get() == "Auto" else 0
            n = int(self.samples_var.get())
        except ValueError as exc:
            if not silent:
                messagebox.showerror("Invalid setting", str(exc))
            return None
        return f"S {int(round(rate))} {analog} {int(round(thr * 1000))} {tt} {tch} {pre} {auto} {n}"

    def _send(self, text):
        try:
            self.link.send(text)
            return True
        except Exception as exc:
            self.on_link_error(str(exc))
            return False

    def arm(self):
        cmd = self.build_start_cmd()
        if cmd is None:
            self.acq_mode = "stop"
            self.update_buttons()
            return
        if not self._send(cmd):
            return
        self.last_cmd = cmd
        self.link_state = "ARMED"
        trig_on = self.trig_type_var.get() != TRIG_TYPES[0]
        self.set_status("Waiting for trigger..." if trig_on else "Capturing...")
        self.update_buttons()

    def start_acq(self, mode):
        if self.link is None:
            return
        self.acq_mode = mode
        if self.link_state == "IDLE":
            self.arm()
        elif self.link_state == "ARMED":              # restart with current settings
            if self._send("A"):
                self.link_state = "ABORTING"
        self.update_buttons()

    def stop_acq(self):
        self.acq_mode = "stop"
        if self.link is not None and self.link_state == "ARMED":
            if self._send("A"):
                self.link_state = "ABORTING"
        self.set_status("Stopped.")
        self.update_buttons()

    def on_config_changed(self, *_):
        """Re-arm with the new settings if they really changed while capturing."""
        self.update_widget_states()
        if self.link is None or self.acq_mode == "stop" or self.link_state != "ARMED":
            return
        cmd = self.build_start_cmd(silent=True)
        if cmd is None or cmd == self.last_cmd:
            return
        if self._send("A"):
            self.link_state = "ABORTING"             # re-armed when ABORT arrives

    def on_pause(self):
        if self.paused_var.get():
            self.set_status("Display paused (acquisition continues in the background).")
        else:
            self.set_status("Display resumed.")
            if self.latest is not None:
                self.show_capture(self.latest)

    # ------------------------------------------------------ event loop ------
    def poll_events(self):
        try:
            while True:
                self.handle_event(self.events.get_nowait())
        except queue.Empty:
            pass
        self.root.after(20, self.poll_events)

    def handle_event(self, ev):
        kind = ev[0]
        if kind == "frame":
            self.on_frame(ev)
        elif kind == "line":
            self.on_line(ev[1])
        elif kind == "error":
            self.set_status(ev[1])
            if self.link_state == "ARMED":           # lost frame: carry on
                self.link_state = "IDLE"
                if self.acq_mode == "run":
                    self.arm()
                else:
                    self.acq_mode = "stop"
                    self.update_buttons()
        elif kind == "connected":
            self.link = ev[1]
            self.on_connected(ev[2])
        elif kind == "connect_failed":
            self.connect_btn.configure(state="normal")
            self.set_status("Connection failed.")
            messagebox.showerror("Connection failed", ev[1])
        elif kind == "link_error":
            self.on_link_error(ev[1])

    def on_link_error(self, msg):
        if self.link is not None:
            try:
                self.link.close()
            except Exception:
                pass
        self.link = None
        self.link_state = "IDLE"
        self.acq_mode = "stop"
        self.conn_var.set("Disconnected")
        self.set_status(f"Serial error: {msg}")
        self.update_buttons()
        messagebox.showerror("Serial error", msg)

    def on_line(self, line):
        if line == "ABORT":
            self.link_state = "IDLE"
            if self.acq_mode != "stop":
                self.arm()
            self.update_buttons()
        elif line.startswith("ERR"):
            self.link_state = "IDLE"
            self.acq_mode = "stop"
            self.set_status(f"Device error: {line}")
            self.update_buttons()

    def on_frame(self, ev):
        _, flags, rate, count, tpos, payload = ev
        if self.link_state == "ABORTING":            # stale frame, ignore
            return
        self.link_state = "IDLE"
        trig = bool(flags & 0x01) and tpos != 0xFFFF and tpos < count
        cap = Capture(payload, rate, tpos if trig else 0, trig, analog=bool(flags & 0x02))
        self.latest = cap
        if not self.paused_var.get():
            self.show_capture(cap)
        if self.acq_mode == "run":
            self.arm()
        elif self.acq_mode == "single":
            self.acq_mode = "stop"
            self.set_status("Single capture done.")
        self.update_buttons()

    def show_capture(self, cap):
        self.capture = cap
        sig = (int(cap.rate), cap.n)
        if sig != self._last_sig:                    # new rate / size: fit view
            self._last_sig = sig
            self.zoom_fit()
        else:
            self.apply_view()
        self.update_measure()
        txt = "triggered" if cap.triggered else "not triggered"
        self.set_status(f"Capture: {cap.n} samples @ {fmt_rate(cap.rate)} "
                        f"({fmt_time(cap.duration)}), {txt}.")

    # ------------------------------------------------------- view control ---
    def current_theme(self):
        return "light" if self.light_var.get() else "dark"

    def clamp_view(self):
        self.t_div = min(max(self.t_div, T_DIV_MIN), T_DIV_MAX)
        win = DIVISIONS * self.t_div
        lo = hi = self.t_start
        if self.capture is not None:
            lo = self.capture.t_min - 0.9 * win
            hi = self.capture.t_max - 0.1 * win
            self.t_start = min(max(self.t_start, lo), hi)
        return lo, hi

    def apply_view(self, t_div=None, t_start=None):
        if t_div is not None:
            self.t_div = t_div
        if t_start is not None:
            self.t_start = t_start
        lo, hi = self.clamp_view()
        self.tdiv_var.set(fmt_time(self.t_div))
        self._scale_guard = True
        try:
            self.scale.set((self.t_start - lo) / (hi - lo) if hi > lo else 0.0)
        finally:
            self._scale_guard = False
        self.schedule_redraw()

    def on_scale_moved(self, value):
        if self._scale_guard or self.capture is None:
            return
        lo, hi = self.clamp_view()
        self.t_start = lo + float(value) * (hi - lo)
        self.schedule_redraw()

    def on_tdiv_entered(self, *_):
        try:
            new = parse_time(self.tdiv_var.get())
        except ValueError as exc:
            self.set_status(str(exc))
            self.tdiv_var.set(fmt_time(self.t_div))
            return
        shown = parse_time(fmt_time(self.t_div))      # value currently displayed
        if abs(new - shown) > 1e-9 * shown:           # ignore FocusOut without edits
            self.apply_view(t_div=new)

    def zoom(self, factor, center=None):
        win = DIVISIONS * self.t_div
        if center is None:
            a, b = self.cursors["A"], self.cursors["B"]
            center = (a + b) / 2 if (a is not None and b is not None) else self.t_start + win / 2
        new_div = min(max(self.t_div * factor, T_DIV_MIN), T_DIV_MAX)
        real = new_div / self.t_div
        self.apply_view(t_div=new_div, t_start=center - (center - self.t_start) * real)

    def zoom_fit(self):
        if self.capture is None:
            return
        self.apply_view(t_div=nice_ceil(self.capture.duration / DIVISIONS),
                        t_start=self.capture.t_min)

    def zoom_to_cursors(self):
        a, b = self.cursors["A"], self.cursors["B"]
        if a is None or b is None or a == b:
            self.set_status("Place both cursors (A and B) first.")
            return
        lo, hi = min(a, b), max(a, b)
        span = hi - lo
        self.apply_view(t_div=span * 1.25 / DIVISIONS, t_start=lo - 0.125 * span)

    def pan(self, fraction):
        win = DIVISIONS * self.t_div
        self.apply_view(t_start=self.t_start + fraction * win)

    # ---------------------------------------------------- mouse handling ----
    def _x_from_event(self, ev):
        return self.ax.transData.inverted().transform((ev.x, ev.y))[0]

    def _pick_cursor(self, ev):
        for name in ("A", "B"):
            t = self.cursors[name]
            if t is None:
                continue
            px = self.ax.transData.transform((t, 0))[0]
            if abs(px - ev.x) <= 6:
                return name
        return None

    def on_press(self, ev):
        if ev.inaxes is not self.ax or ev.xdata is None:
            return
        if ev.button == 1:
            picked = self._pick_cursor(ev)
            if ev.key == "shift":
                picked, name = None, "B"
            else:
                name = picked or "A"
            self._drag = name
            if picked is None:
                self.set_cursor(name, ev.xdata)
        elif ev.button == 3:
            self._drag = "B"
            self.set_cursor("B", ev.xdata)
        elif ev.button == 2:
            self._pan = (ev.x, self.t_start)

    def on_motion(self, ev):
        if ev.x is None:
            return
        if self._drag is not None:
            self.set_cursor(self._drag, self._x_from_event(ev))
        elif self._pan is not None:
            px0, ts0 = self._pan
            width = max(self.ax.bbox.width, 1.0)
            self.apply_view(t_start=ts0 - (ev.x - px0) / width * DIVISIONS * self.t_div)

    def on_release(self, ev):
        self._drag = None
        self._pan = None

    def on_scroll(self, ev):
        if ev.inaxes is not self.ax or ev.xdata is None:
            return
        if ev.key == "shift":
            self.pan(-0.1 if ev.button == "up" else 0.1)
        else:
            self.zoom(0.8 if ev.button == "up" else 1.25, center=ev.xdata)

    def set_cursor(self, name, t):
        self.cursors[name] = float(t)
        self.update_measure()
        self.schedule_redraw()

    def clear_cursors(self):
        self.cursors = {"A": None, "B": None}
        self.update_measure()
        self.schedule_redraw()

    # ------------------------------------------------------ measurements ----
    def enabled_channels(self):
        return [i for i in range(NUM_CH) if self.ch_enabled[i].get()]

    def channel_name(self, i):
        name = self.ch_names[i].get().strip()
        return name if name else f"CH{i + 1}"

    def update_measure(self):
        a, b = self.cursors["A"], self.cursors["B"]
        cap = self.capture
        if a is None and b is None:
            self.measure_lbl.configure(
                text="Click the plot to place cursor A (left) and cursor B (right click or Shift+click).")
            return
        lines = []
        head = []
        if a is not None:
            head.append(f"A: {fmt_time(a)}")
        if b is not None:
            head.append(f"B: {fmt_time(b)}")
        if a is not None and b is not None:
            dt = abs(b - a)
            s = f"\u0394T: {fmt_time(dt)}"
            if dt > 0:
                s += f"   1/\u0394T: {fmt_freq(1.0 / dt)}"
            if cap is not None:
                s += f"   ({int(round(dt * cap.rate))} samples)"
            head.append(s)
        lines.append("    ".join(head))

        if cap is not None:
            en = self.enabled_channels()
            mask = sum(1 << c for c in en)
            for name in ("A", "B"):
                t = self.cursors[name]
                if t is None:
                    continue
                v = int(cap.data[cap.index_at(t)])
                bus = v & mask
                lines.append(
                    f"Bus@{name}  BIN {fmt_value(bus, 'Binary')} | DEC {fmt_value(bus, 'Decimal')} | "
                    f"HEX {fmt_value(bus, 'Hexadecimal')} | OCT {fmt_value(bus, 'Octal')}")
                lv = "  ".join(f"{self.channel_name(c)}={(v >> c) & 1}" for c in en)
                lines.append(f"Levels@{name}  {lv}")
        self.measure_lbl.configure(text="\n".join(lines))

    # --------------------------------------------------------- plotting -----
    def schedule_redraw(self, *_):
        if self._redraw_job is None:
            self._redraw_job = self.root.after(15, self._do_redraw)

    def _do_redraw(self):
        self._redraw_job = None
        self.redraw()

    def redraw(self, theme_name=None):
        th = THEMES[theme_name or self.current_theme()]
        fig, ax = self.fig, self.ax
        fig.set_facecolor(th["fig"])
        ax.clear()
        ax.set_facecolor(th["axes"])
        for sp in ax.spines.values():
            sp.set_color(th["grid"])
        ax.tick_params(colors=th["text"], labelsize=8)

        win = DIVISIONS * self.t_div
        x0, x1 = self.t_start, self.t_start + win
        ax.set_xlim(x0, x1)
        ax.xaxis.set_major_locator(MultipleLocator(self.t_div))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: fmt_time(v)))
        ax.grid(True, axis="x", color=th["grid"], lw=0.6)
        ax.set_xlabel(f"Time   \u2014   {fmt_time(self.t_div)}/div", color=th["text"], fontsize=9)

        cap = self.capture
        enabled = self.enabled_channels()
        show_bus = self.show_bus_var.get()
        lanes = len(enabled) + (1 if show_bus else 0)
        ax.set_ylim(-0.05, max(lanes, 1) + 0.65)

        if cap is None or lanes == 0:
            msg = ("No data yet.\nConnect a device (or choose the DEMO port) and press Run."
                   if cap is None else "No channels enabled.")
            ax.text(0.5, 0.5, msg, transform=ax.transAxes, ha="center", va="center",
                    color=th["text"], fontsize=11)
            ax.set_yticks([])
            self.canvas.draw_idle()
            return

        # shade the regions without data
        if cap.t_min > x0:
            ax.axvspan(x0, cap.t_min, color=th["nodata"], lw=0)
        if cap.t_max < x1:
            ax.axvspan(cap.t_max, x1, color=th["nodata"], lw=0)

        t = cap.times()
        tt = np.append(t, cap.t_max)
        yticks, ylabels, ycols = [], [], []

        # ---- digital traces
        for j, ch in enumerate(enabled):
            base = lanes - 1 - j
            col = th["colors"][ch]
            lvl = ((cap.data >> ch) & 1).astype(float)
            y = base + 0.12 + 0.62 * lvl
            ax.step(tt, np.append(y, y[-1]), where="post", color=col, lw=1.4)
            ax.axhline(base, color=th["grid"], lw=0.5)
            yticks.append(base + 0.43)
            ylabels.append(self.channel_name(ch))
            ycols.append(col)

        # ---- bus lane (numeric conversion)
        if show_bus:
            base = 0
            ax.axhline(base, color=th["grid"], lw=0.5)
            mask = sum(1 << c for c in enabled)
            vals = (cap.data & mask).astype(np.int32)
            change = np.flatnonzero(np.diff(vals)) + 1
            starts = np.concatenate(([0], change))
            ends = np.concatenate((change, [cap.n]))
            ts = (starts - cap.trig_idx) * cap.dt
            te = (ends - cap.trig_idx) * cap.dt
            lo_y, hi_y, mid_y = base + 0.12, base + 0.74, base + 0.43
            verts = []
            vis = []
            for k in range(len(starts)):
                if te[k] < x0 or ts[k] > x1:
                    continue
                d = min(0.15 * (te[k] - ts[k]), 0.004 * win)
                verts.append([(ts[k], mid_y), (ts[k] + d, hi_y), (te[k] - d, hi_y),
                              (te[k], mid_y), (te[k] - d, lo_y), (ts[k] + d, lo_y)])
                vis.append(k)
            if verts:
                ax.add_collection(PolyCollection(verts, facecolors="none",
                                                 edgecolors=th["text"], linewidths=1.0))
            ax_px = max(ax.bbox.width, 100.0)
            base_name = self.base_var.get()
            for k in vis:
                a0, a1 = max(ts[k], x0), min(te[k], x1)
                seg_px = (a1 - a0) / win * ax_px
                for pref in (True, False):             # full label, else compact one
                    label = fmt_value(vals[starts[k]], base_name, prefix=pref)
                    if seg_px > 6.8 * len(label) + 6:
                        ax.text((a0 + a1) / 2, mid_y, label, ha="center", va="center",
                                fontsize=8, family="monospace", color=th["text"])
                        break
            yticks.append(mid_y)
            ylabels.append(f"BUS ({base_name[:3].upper()})")
            ycols.append(th["text"])

        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, fontsize=9)
        for lbl, col in zip(ax.get_yticklabels(), ycols):
            lbl.set_color(col)
        ax.tick_params(axis="y", length=0)

        # ---- trigger marker
        if cap.triggered:
            ax.axvline(0.0, color=th["trig"], ls="--", lw=1.0)
            ax.text(0.0, lanes + 0.08, "T", color=th["trig"], ha="center", va="bottom",
                    fontsize=9, fontweight="bold")

        # ---- cursors
        for name, col in (("A", th["curA"]), ("B", th["curB"])):
            tc = self.cursors[name]
            if tc is not None:
                ax.axvline(tc, color=col, lw=1.3)
                ax.text(tc, lanes + 0.08, name, color=col, ha="center", va="bottom",
                        fontsize=10, fontweight="bold")
        a, b = self.cursors["A"], self.cursors["B"]
        if a is not None and b is not None and a != b:
            yy = lanes + 0.36
            ax.annotate("", xy=(a, yy), xytext=(b, yy),
                        arrowprops=dict(arrowstyle="<->", color=th["text"], lw=1.0))
            dtv = abs(b - a)
            ax.text((a + b) / 2, yy + 0.03,
                    f"\u0394T = {fmt_time(dtv)}  ({fmt_freq(1.0 / dtv)})",
                    ha="center", va="bottom", fontsize=8, color=th["text"],
                    bbox=dict(boxstyle="round,pad=0.2", fc=th["axes"], ec=th["grid"]))

        trig_txt = "triggered at t = 0" if cap.triggered else "not triggered"
        mode_txt = "analog threshold" if cap.analog else "digital"
        ax.set_title(f"{fmt_rate(cap.rate)}  |  {cap.n} samples  |  window {fmt_time(cap.duration)}"
                     f"  |  {mode_txt}  |  {trig_txt}  |  {cap.timestamp:%Y-%m-%d %H:%M:%S}",
                     color=th["text"], fontsize=9)
        self.canvas.draw_idle()

    # ----------------------------------------------------------- exports ----
    def _default_name(self, ext):
        return f"logic_capture_{datetime.datetime.now():%Y%m%d_%H%M%S}.{ext}"

    def _need_data(self):
        if self.capture is None:
            messagebox.showinfo("No data", "There is no capture to export yet.")
            return False
        return True

    def export_png(self):
        if not self._need_data():
            return
        path = filedialog.asksaveasfilename(
            title="Save plot as PNG", defaultextension=".png",
            initialfile=self._default_name("png"), filetypes=[("PNG image", "*.png")])
        if not path:
            return
        try:
            self.redraw()
            self.fig.savefig(path, dpi=150, facecolor=self.fig.get_facecolor())
            self.set_status(f"PNG saved: {path}")
        except Exception as exc:
            messagebox.showerror("Export error", str(exc))

    def export_pdf(self):
        if not self._need_data():
            return
        path = filedialog.asksaveasfilename(
            title="Export plot as PDF", defaultextension=".pdf",
            initialfile=self._default_name("pdf"), filetypes=[("PDF document", "*.pdf")])
        if not path:
            return
        try:
            self.redraw("light")                      # printable theme
            self.fig.savefig(path, format="pdf", facecolor="white",
                             metadata={"Title": "Logic analyzer capture",
                                       "Creator": APP_TITLE})
            self.set_status(f"PDF saved: {path}")
        except Exception as exc:
            messagebox.showerror("Export error", str(exc))
        finally:
            self.redraw()

    def export_csv(self):
        if not self._need_data():
            return
        path = filedialog.asksaveasfilename(
            title="Export data as CSV", defaultextension=".csv",
            initialfile=self._default_name("csv"), filetypes=[("CSV file", "*.csv")])
        if not path:
            return
        cap = self.capture
        en = self.enabled_channels()
        if not en:
            messagebox.showinfo("No channels", "Enable at least one channel to export.")
            return
        names, seen = [], set()
        for c in en:
            nm = self.channel_name(c)
            if nm in seen:
                nm = f"{nm}_{c + 1}"
            seen.add(nm)
            names.append(nm)
        mask = sum(1 << c for c in en)
        t = cap.times()
        try:
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["Sample", "Time_s"] + names +
                           ["Value_BIN", "Value_DEC", "Value_HEX", "Value_OCT"])
                for i in range(cap.n):
                    raw = int(cap.data[i])
                    bus = raw & mask
                    w.writerow([i, f"{t[i]:.9g}"] + [(raw >> c) & 1 for c in en] +
                               [f"{bus:08b}", bus, f"{bus:02X}", f"{bus:03o}"])
            self.set_status(f"CSV saved: {path}")
        except Exception as exc:
            messagebox.showerror("Export error", str(exc))


# ----------------------------------------------------------------------------
def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
