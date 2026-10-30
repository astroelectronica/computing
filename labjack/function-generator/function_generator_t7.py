"""
FUNCTION GENERATOR FOR LABJACK T7  (2 channels: DAC0 and DAC1)

Features
  - Waveforms: sine, square, triangle, sawtooth, reverse ramp, exponential rise/fall,
    gaussian, sinc, noise, DC and arbitrary (loaded from a CSV file).
  - Per-channel parameters: frequency, amplitude (Vpp), offset, phase, duty cycle /
    symmetry, inversion, output ON/OFF.
  - Modes: Continuous, Sweep (linear / logarithmic), Burst, AM and FM.
  - Both channels are generated in sync (same T7 stream clock).
  - Live waveform preview, save/load configuration, automatic apply of changes.

How it works
  One period of the signal is computed on the PC (up to 2048 samples) and loaded into the
  T7 STREAM-OUT buffer, which loops it with a hardware clock (no CPU load, no jitter).
  Output frequency = sample rate / number of samples per period.

T7 hardware limits (not limits of this program)
  - 12-bit DAC with a 0 to 5 V range (no negative voltage: use offset >= Vpp/2).
  - Practical maximum frequency: MAX_FS / 8 = about 2.5 kHz with the default settings.
  - If the signal leaves the 0-5 V range it is clipped (a warning is shown).

Requirements: pip install labjack-ljm numpy   (+ LabJack LJM driver)
"""

import json
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from labjack import ljm

# ------------------------------ Settings ---------------------------------
V_MIN, V_MAX = 0.0, 5.0      # T7 DAC range
MAX_FS = 20000.0             # Maximum stream-out sample rate (samples/s)
MIN_FS = 1.0                 # Minimum sample rate (samples/s)
N_MAX = 2048                 # Maximum samples per period
N_MIN = 8                    # Minimum samples per period
# --------------------------------------------------------------------------

SHAPES = ["Sine", "Square", "Triangle", "Sawtooth", "Reverse ramp",
          "Exp. rise", "Exp. fall", "Gaussian", "Sinc", "Noise", "DC", "Arbitrary"]
MODES = ["Continuous", "Sweep", "Burst", "AM", "FM"]
SHAPES_WITH_DUTY = ("Square", "Triangle")


# =========================================================================
#                    SIGNAL CALCULATION (no hardware needed)
# =========================================================================
def waveform(shape, phase, sym, arb, rng):
    """phase in cycles (array). Returns values between -1 and 1."""
    q = np.mod(phase, 1.0)
    if shape == "Sine":
        return np.sin(2 * np.pi * q)
    if shape == "Square":
        return np.where(q < sym, 1.0, -1.0)
    if shape == "Triangle":
        s = min(max(sym, 1e-6), 1 - 1e-6)
        return np.where(q < s, -1 + 2 * q / s, 1 - 2 * (q - s) / (1 - s))
    if shape == "Sawtooth":
        return 2 * q - 1
    if shape == "Reverse ramp":
        return 1 - 2 * q
    if shape == "Exp. rise":
        return 2 * (1 - np.exp(-5 * q)) / (1 - np.exp(-5)) - 1
    if shape == "Exp. fall":
        return 2 * (np.exp(-5 * q) - np.exp(-5)) / (1 - np.exp(-5)) - 1
    if shape == "Gaussian":
        return 2 * np.exp(-0.5 * ((q - 0.5) / 0.12) ** 2) - 1
    if shape == "Sinc":
        return np.sinc((q - 0.5) * 12)
    if shape == "Noise":
        return rng.uniform(-1, 1, len(q))
    if shape == "Arbitrary":
        xp = np.linspace(0, 1, len(arb), endpoint=False)
        return np.interp(q, xp, arb, period=1.0)
    return np.zeros(len(q))  # DC


def base_period(c):
    """Fundamental period (s) after which the signal repeats."""
    if c["shape"] == "Noise":
        return N_MAX / MAX_FS
    m = c["mode"]
    if m == "Continuous":
        return 1.0 / c["freq"]
    if m == "Sweep":
        return c["t_sweep"]
    if m == "Burst":
        return c["t_burst"]
    return 1.0 / c["f_mod"]          # AM, FM


def effective_carrier(c):
    """In AM/FM the carrier is rounded to an integer multiple of the modulating frequency."""
    k = max(1, int(round(c["freq"] / c["f_mod"])))
    return k * c["f_mod"]


def max_instant_freq(c):
    m = c["mode"]
    if m == "Sweep":
        return max(c["freq"], c["f_stop"])
    if m == "AM":
        return effective_carrier(c)
    if m == "FM":
        return effective_carrier(c) + c["dev"]
    return c["freq"]


def validate(c, name):
    if c["vpp"] < 0:
        raise ValueError(f"{name}: amplitude cannot be negative")
    if not 0 <= c["duty"] <= 100:
        raise ValueError(f"{name}: duty cycle / symmetry must be between 0 and 100 %")
    if c["shape"] == "Arbitrary" and c.get("arb") is None:
        raise ValueError(f"{name}: load a file for the arbitrary waveform")
    if c["shape"] in ("DC", "Noise"):
        return
    if c["freq"] <= 0:
        raise ValueError(f"{name}: frequency must be greater than 0")
    m = c["mode"]
    if m == "Sweep" and (c["f_stop"] <= 0 or c["t_sweep"] <= 0):
        raise ValueError(f"{name}: stop frequency and sweep time must be > 0")
    if m == "Burst":
        if c["ncyc"] < 1 or c["t_burst"] <= 0:
            raise ValueError(f"{name}: burst cycles must be >= 1 and burst period > 0")
        if c["ncyc"] / c["freq"] > c["t_burst"]:
            raise ValueError(f"{name}: the burst lasts longer than its period")
    if m in ("AM", "FM") and c["f_mod"] <= 0:
        raise ValueError(f"{name}: modulating frequency must be > 0")
    if m == "AM" and not 0 <= c["depth"] <= 100:
        raise ValueError(f"{name}: AM depth must be between 0 and 100 %")
    if m == "FM" and c["dev"] < 0:
        raise ValueError(f"{name}: FM deviation cannot be negative")


def generate(c, n, rng):
    """One fundamental period in n samples (voltage in volts, not clipped)."""
    shape, mode = c["shape"], c["mode"]
    sym = c["duty"] / 100.0
    if shape == "DC":
        return np.full(n, c["offset"])
    T0 = base_period(c)
    t = np.arange(n) * T0 / n
    f = c["freq"]
    if shape == "Noise":
        phase = t
    elif mode == "Sweep":
        f1, f2, T = f, c["f_stop"], c["t_sweep"]
        if c["log"] and abs(f2 / f1 - 1) > 1e-9:
            k = f2 / f1
            phase = f1 * T / np.log(k) * (k ** (t / T) - 1)
        else:
            phase = f1 * t + (f2 - f1) * t ** 2 / (2 * T)
    elif mode == "AM":
        phase = effective_carrier(c) * t
    elif mode == "FM":
        fm = c["f_mod"]
        phase = effective_carrier(c) * t + c["dev"] / (2 * np.pi * fm) * np.sin(2 * np.pi * fm * t)
    else:                              # Continuous, Burst
        phase = f * t
    phase = phase + c["phase"] / 360.0
    w = waveform(shape, phase, sym, c.get("arb"), rng)
    if shape != "Noise":
        if mode == "AM":
            m = c["depth"] / 100.0
            w = w * (1 + m * np.sin(2 * np.pi * c["f_mod"] * t)) / (1 + m)
        elif mode == "Burst":
            w = np.where(t < c["ncyc"] / f, w, 0.0)
    if c["invert"]:
        w = -w
    return c["offset"] + c["vpp"] / 2.0 * w


def solve(cfgs):
    """
    cfgs: list of (channel_index, config) for the channels with output enabled.
    Computes the common sample rate and the buffer of each channel.
    """
    plan = {"fs": None, "stream": {}, "dc": {}, "off": []}
    rng = np.random.default_rng()
    per = {}
    for i, c in cfgs:
        validate(c, f"CH{i + 1}")
        if c["shape"] == "DC":
            plan["dc"][i] = float(np.clip(c["offset"], V_MIN, V_MAX))
        elif c["shape"] == "Noise":
            per[i] = None
        else:
            per[i] = 1.0 / base_period(c)

    f0s = [x for x in per.values() if x]
    if f0s:
        fmax = max(f0s)
        n_hi = min(N_MAX, int(MAX_FS // fmax))
        if n_hi < N_MIN:
            raise ValueError(f"Frequency too high: maximum is {MAX_FS / N_MIN:.0f} Hz "
                             f"(signal repetition rate)")
        fs = n_hi * fmax
    elif per:
        fmax, fs = None, MAX_FS
    else:
        return plan
    if fs < MIN_FS:
        raise ValueError("Frequency too low for the T7 stream clock")
    plan["fs"] = fs

    for i, c in cfgs:
        if i not in per:
            continue
        if per[i] is None:
            n = N_MAX
        else:
            n = n_hi if per[i] == fmax else int(round(fs / per[i]))
            if n > N_MAX:
                raise ValueError("Frequency ratio between channels is too large "
                                 f"(CH{i + 1} would need {n} samples, max {N_MAX})")
            if fs / max_instant_freq(c) < 4:
                raise ValueError(f"CH{i + 1}: frequency too high for the current sample "
                                 f"rate ({fs:.0f} samples/s); reduce the frequency")
        v = generate(c, n, rng)
        clipped = bool(np.any(v < V_MIN - 1e-9) or np.any(v > V_MAX + 1e-9))
        plan["stream"][i] = {"n": n, "v": np.clip(v, V_MIN, V_MAX), "clip": clipped,
                             "f_rep": fs / n, "cfg": c}
    return plan


# =========================================================================
#                         HARDWARE (stream-out)
# =========================================================================
class Generator:
    def __init__(self, handle):
        self.handle = handle
        self.thread = None
        self.stop_ev = threading.Event()
        self.streaming = False
        self.error = None
        self.fs_real = None

    def _reader(self):
        # The stream input buffer must be drained, otherwise it overflows
        while not self.stop_ev.is_set():
            try:
                ljm.eStreamRead(self.handle)
            except ljm.LJMError as e:
                self.error = e
                break

    def _stop_stream(self):
        if self.thread is not None:
            self.stop_ev.set()
            self.thread.join(timeout=3)
            self.thread = None
        if self.streaming:
            try:
                ljm.eStreamStop(self.handle)
            except ljm.LJMError:
                pass
            self.streaming = False
        for i in (0, 1):
            try:
                ljm.eWriteName(self.handle, f"STREAM_OUT{i}_ENABLE", 0)
            except ljm.LJMError:
                pass

    def start(self, plan):
        h = self.handle
        self.error = None
        self._stop_stream()
        for i, v in plan["dc"].items():
            ljm.eWriteName(h, f"DAC{i}", v)
        for i in plan["off"]:
            ljm.eWriteName(h, f"DAC{i}", 0.0)
        if not plan["stream"]:
            self.fs_real = None
            return

        ljm.eWriteName(h, "STREAM_TRIGGER_INDEX", 0)
        ljm.eWriteName(h, "STREAM_CLOCK_SOURCE", 0)
        names = ["FIO_STATE"]              # dummy stream input channel
        for i, d in plan["stream"].items():
            n = d["n"]
            size = 16
            while size < 2 * n:
                size *= 2
            ljm.eWriteName(h, f"STREAM_OUT{i}_TARGET", 1000 + 2 * i)   # DAC0=1000, DAC1=1002
            ljm.eWriteName(h, f"STREAM_OUT{i}_BUFFER_SIZE", size)
            ljm.eWriteName(h, f"STREAM_OUT{i}_ENABLE", 1)
            ljm.eWriteNameArray(h, f"STREAM_OUT{i}_BUFFER_F32", n, [float(x) for x in d["v"]])
            ljm.eWriteName(h, f"STREAM_OUT{i}_LOOP_SIZE", n)
            ljm.eWriteName(h, f"STREAM_OUT{i}_SET_LOOP", 1)
            names.append(f"STREAM_OUT{i}")

        addresses = ljm.namesToAddresses(len(names), names)[0]
        scans_per_read = max(1, int(plan["fs"] / 10))
        self.fs_real = ljm.eStreamStart(h, scans_per_read, len(addresses),
                                        addresses, plan["fs"])
        self.streaming = True
        self.stop_ev.clear()
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def stop(self, zero=True):
        self._stop_stream()
        if zero:
            for i in (0, 1):
                try:
                    ljm.eWriteName(self.handle, f"DAC{i}", 0.0)
                except ljm.LJMError:
                    pass


# =========================================================================
#                                  GUI
# =========================================================================
BASE_FIELDS = [("freq", "Frequency", "Hz"), ("vpp", "Amplitude", "Vpp"),
               ("offset", "Offset", "V"), ("phase", "Phase", "°"),
               ("duty", "Duty / symmetry", "%")]
EXTRA_FIELDS = [("f_stop", "Stop frequency", "Hz"), ("t_sweep", "Sweep time", "s"),
                ("ncyc", "Burst cycles", ""), ("t_burst", "Burst period", "s"),
                ("f_mod", "Modulating freq.", "Hz"), ("depth", "AM depth", "%"),
                ("dev", "FM deviation", "Hz")]
EXTRA_BY_MODE = {"Continuous": [], "Sweep": ["f_stop", "t_sweep", "log"],
                 "Burst": ["ncyc", "t_burst"], "AM": ["f_mod", "depth"],
                 "FM": ["f_mod", "dev"]}
DEFAULTS = {"freq": "100", "vpp": "2", "offset": "2.5", "phase": "0", "duty": "50",
            "f_stop": "1000", "t_sweep": "1", "ncyc": "3", "t_burst": "0.1",
            "f_mod": "10", "depth": "50", "dev": "50"}
PREV_W, PREV_H, PREV_M = 340, 130, 34


class Panel:
    def __init__(self, parent, idx, callback, enabled, shape):
        self.idx, self.cb = idx, callback
        self.arb = None
        self.lf = ttk.LabelFrame(parent, text=f"Channel {idx + 1}  (DAC{idx})", padding=8)
        self.v, self.w = {}, {}

        self.v["enabled"] = tk.BooleanVar(value=enabled)
        ttk.Checkbutton(self.lf, text="Output enabled", variable=self.v["enabled"]).grid(
            row=0, column=0, columnspan=3, sticky="w")

        self.v["shape"] = tk.StringVar(value=shape)
        self.v["mode"] = tk.StringVar(value="Continuous")
        r = 1
        for key, label, values in (("shape", "Waveform", SHAPES), ("mode", "Mode", MODES)):
            ttk.Label(self.lf, text=label).grid(row=r, column=0, sticky="e", pady=2)
            cb = ttk.Combobox(self.lf, textvariable=self.v[key], values=values,
                              state="readonly", width=16)
            cb.grid(row=r, column=1, columnspan=2, sticky="w", padx=4)
            self.w[key] = cb
            r += 1

        for key, label, unit in BASE_FIELDS + EXTRA_FIELDS:
            self.v[key] = tk.StringVar(value=DEFAULTS[key])
            ttk.Label(self.lf, text=label).grid(row=r, column=0, sticky="e", pady=2)
            e = ttk.Entry(self.lf, textvariable=self.v[key], width=10, justify="right")
            e.grid(row=r, column=1, padx=4)
            ttk.Label(self.lf, text=unit).grid(row=r, column=2, sticky="w")
            self.w[key] = e
            r += 1

        self.v["log"] = tk.BooleanVar(value=False)
        self.w["log"] = ttk.Checkbutton(self.lf, text="Logarithmic sweep", variable=self.v["log"])
        self.w["log"].grid(row=r, column=0, columnspan=3, sticky="w"); r += 1
        self.v["invert"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.lf, text="Invert signal", variable=self.v["invert"]).grid(
            row=r, column=0, columnspan=3, sticky="w"); r += 1

        self.btn_arb = ttk.Button(self.lf, text="Load arbitrary waveform (CSV)...",
                                  command=self.load_arb)
        self.btn_arb.grid(row=r, column=0, columnspan=3, pady=3); r += 1
        self.lbl_arb = ttk.Label(self.lf, text="", foreground="#555")
        self.lbl_arb.grid(row=r, column=0, columnspan=3); r += 1

        self.cv = tk.Canvas(self.lf, width=PREV_W, height=PREV_H, bg="white",
                            highlightthickness=1, highlightbackground="#999")
        self.cv.grid(row=r, column=0, columnspan=3, pady=(6, 2)); r += 1
        self.lbl_info = ttk.Label(self.lf, text="", font=("Segoe UI", 8))
        self.lbl_info.grid(row=r, column=0, columnspan=3)

        for key, var in self.v.items():
            var.trace_add("write", lambda *a, k=key: self._changed(k))
        self.update_state()

    def _changed(self, key):
        if key in ("shape", "mode"):
            self.update_state()
        self.cb()

    def update_state(self):
        shape, mode = self.v["shape"].get(), self.v["mode"].get()
        special = shape in ("DC", "Noise")

        def state(k, on):
            self.w[k].config(state=("normal" if on else "disabled"))

        self.w["mode"].config(state=("readonly" if not special else "disabled"))
        state("freq", not special)
        state("vpp", shape != "DC")
        state("phase", not special)
        state("duty", shape in SHAPES_WITH_DUTY)
        extras = EXTRA_BY_MODE[mode] if not special else []
        for k, _, _ in EXTRA_FIELDS:
            state(k, k in extras)
        self.w["log"].config(state=("normal" if "log" in extras else "disabled"))
        self.btn_arb.config(state=("normal" if shape == "Arbitrary" else "disabled"))

    # ---- data ----
    def read(self):
        name = f"CH{self.idx + 1}"
        c = {k: self.v[k].get() for k in ("enabled", "shape", "mode", "log", "invert")}
        for key, label, _ in BASE_FIELDS + EXTRA_FIELDS:
            try:
                c[key] = float(self.v[key].get().replace(",", "."))
            except ValueError:
                raise ValueError(f"{name}: invalid value in '{label}'")
        c["arb"] = self.arb
        return c

    def get_state(self):
        d = {k: v.get() for k, v in self.v.items()}
        d["arb"] = None if self.arb is None else [float(x) for x in self.arb]
        return d

    def set_state(self, d):
        for k, v in self.v.items():
            if k in d:
                v.set(d[k])
        self.arb = None if d.get("arb") is None else np.array(d["arb"])
        self.lbl_arb.config(text="" if self.arb is None else f"{len(self.arb)} points loaded")

    def load_arb(self):
        path = filedialog.askopenfilename(
            title="Arbitrary waveform",
            filetypes=[("CSV / text", "*.csv *.txt *.dat"), ("All files", "*.*")])
        if not path:
            return
        try:
            values = []
            with open(path, encoding="utf-8-sig") as fh:
                for line in fh:
                    fields = [x for x in re.split(r"[,\s;]+", line.strip()) if x]
                    if fields:
                        try:
                            values.append(float(fields[-1]))   # last numeric column
                        except ValueError:
                            continue                           # header lines
            arr = np.array(values)
            if len(arr) < 2:
                raise ValueError("The file needs at least 2 numeric values")
            arr = arr - (arr.max() + arr.min()) / 2
            peak = np.max(np.abs(arr))
            self.arb = arr / peak if peak > 0 else arr
            self.lbl_arb.config(text=f"{len(arr)} points: {os.path.basename(path)}")
            self.cb()
        except (OSError, ValueError) as e:
            messagebox.showerror("Invalid file", str(e))

    # ---- preview ----
    def draw(self, v, message="", info=""):
        cv = self.cv
        cv.delete("all")
        W, H, M = PREV_W, PREV_H, PREV_M
        for volt in (0, 1.25, 2.5, 3.75, 5):
            y = H - 8 - volt / V_MAX * (H - 16)
            cv.create_line(M, y, W - 4, y, fill="#e0e0e0")
            if volt in (0, 2.5, 5):
                cv.create_text(M - 4, y, text=f"{volt:g} V", anchor="e", font=("Segoe UI", 7))
        if v is not None and len(v) > 1:
            xs = np.linspace(M, W - 4, len(v))
            ys = H - 8 - (np.asarray(v) - V_MIN) / (V_MAX - V_MIN) * (H - 16)
            pts = [c for xy in zip(xs, ys) for c in xy]
            cv.create_line(*pts, fill="#1565c0", width=1.5)
        if message:
            cv.create_text(W // 2, H // 2, text=message, fill="#c62828",
                           width=W - 50, font=("Segoe UI", 8, "bold"))
        self.lbl_info.config(text=info)


class App:
    def __init__(self, root):
        self.root = root
        self.handle = None
        self.gen = None
        self.running = False
        self._after = None
        self._ready = False
        root.title("Function Generator - LabJack T7")
        root.protocol("WM_DELETE_WINDOW", self.close)

        body = ttk.Frame(root, padding=8)
        body.pack()
        self.panels = [Panel(body, 0, self.schedule, True, "Sine"),
                       Panel(body, 1, self.schedule, False, "Square")]
        for i, p in enumerate(self.panels):
            p.lf.grid(row=0, column=i, padx=6, sticky="n")

        bar = ttk.Frame(body)
        bar.grid(row=1, column=0, columnspan=2, pady=(8, 0))
        self.btn = tk.Button(bar, text="OUTPUT: OFF", width=16, height=2,
                             font=("Segoe UI", 12, "bold"), bg="#c8e6c9", command=self.toggle)
        self.btn.pack(side="left", padx=6)
        self.auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Apply changes automatically",
                        variable=self.auto).pack(side="left", padx=6)
        ttk.Button(bar, text="Apply now", command=self.apply_now).pack(side="left", padx=4)
        ttk.Button(bar, text="Save config...", command=self.save).pack(side="left", padx=4)
        ttk.Button(bar, text="Load config...", command=self.load).pack(side="left", padx=4)

        self.lbl_status = ttk.Label(body, text="", font=("Segoe UI", 9, "bold"), wraplength=720)
        self.lbl_status.grid(row=2, column=0, columnspan=2, pady=(6, 0))

        self.connect()
        self._ready = True
        self.refresh()
        self.watch()

    # ---------------------------- connection ----------------------------
    def connect(self):
        try:
            self.handle = ljm.openS("T7", "ANY", "ANY")
            try:
                ljm.eStreamStop(self.handle)    # in case a previous stream was left running
            except ljm.LJMError:
                pass
            self.gen = Generator(self.handle)
            self.gen.stop(zero=True)
        except ljm.LJMError as e:
            messagebox.showerror("LabJack error", f"Could not connect to the T7:\n{e}")
            self.btn.config(state="disabled")

    # ------------------------------ logic -------------------------------
    def schedule(self):
        if not self._ready:
            return
        if self._after is not None:
            self.root.after_cancel(self._after)
        self._after = self.root.after(400, self.refresh)

    def build_plan(self):
        cfgs, off = [], []
        for p in self.panels:
            c = p.read()
            if c["enabled"]:
                cfgs.append((p.idx, c))
            else:
                off.append(p.idx)
        plan = solve(cfgs)
        plan["off"] = off
        return plan

    def refresh(self):
        self._after = None
        try:
            plan = self.build_plan()
        except ValueError as e:
            self.lbl_status.config(text=str(e), foreground="#c62828")
            for p in self.panels:
                p.draw(None, str(e))
            return
        warnings, parts = [], []
        for p in self.panels:
            i = p.idx
            if i in plan["stream"]:
                d = plan["stream"][i]
                info = f"repetition f = {d['f_rep']:.6g} Hz   ({d['n']} samples)"
                if d["clip"]:
                    info += "   CLIPPED (0-5 V)!"
                    warnings.append(f"CH{i + 1} clipped: adjust amplitude/offset to the 0-5 V range")
                p.draw(d["v"], info=info)
            elif i in plan["dc"]:
                p.draw(np.full(2, plan["dc"][i]), info=f"DC = {plan['dc'][i]:.3f} V")
            else:
                p.draw(None, info="Output disabled (0 V)")
        if plan["fs"]:
            parts.append(f"Sample rate: {plan['fs']:.6g} samples/s")
        text = "   |   ".join(parts + warnings) or "Ready"
        self.lbl_status.config(text=text, foreground="#c62828" if warnings else "#2e7d32")
        if self.running and self.auto.get():
            self.apply(plan)

    def apply(self, plan):
        try:
            self.gen.start(plan)
        except ljm.LJMError as e:
            self.stop_ui()
            messagebox.showerror("LabJack error", str(e))

    def apply_now(self):
        if not self.running:
            return
        try:
            self.apply(self.build_plan())
        except ValueError as e:
            messagebox.showerror("Invalid parameters", str(e))

    def toggle(self):
        if self.running:
            self.gen.stop(zero=True)
            self.stop_ui()
            return
        try:
            plan = self.build_plan()
            self.gen.start(plan)
        except ValueError as e:
            messagebox.showerror("Invalid parameters", str(e))
            return
        except ljm.LJMError as e:
            messagebox.showerror("LabJack error", str(e))
            return
        self.running = True
        self.btn.config(text="OUTPUT: ON", bg="#ffcdd2")

    def stop_ui(self):
        self.running = False
        self.btn.config(text="OUTPUT: OFF", bg="#c8e6c9")

    def watch(self):
        if self.gen is not None and self.gen.error is not None and self.running:
            err, self.gen.error = self.gen.error, None
            self.gen.stop(zero=True)
            self.stop_ui()
            messagebox.showerror("Stream error", str(err))
        self.root.after(500, self.watch)

    # ---------------------------- configuration ----------------------------
    def save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("Configuration", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump([p.get_state() for p in self.panels], fh, indent=1)

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("Configuration", "*.json")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            for p, d in zip(self.panels, data):
                p.set_state(d)
            self.refresh()
        except (OSError, ValueError, TypeError) as e:
            messagebox.showerror("Invalid configuration", str(e))

    def close(self):
        if self.gen is not None:
            self.gen.stop(zero=True)
        if self.handle is not None:
            try:
                ljm.close(self.handle)
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()