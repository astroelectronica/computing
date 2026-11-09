# Feasibility Report — Eight-Channel Logic Analyser Using a Raspberry Pi 3

**Document analysed:** `Raspberry_Pi_3_Logic_Analyzer_Master_Prompt_Claude_Free_Enhanced.md` (2,851 lines, about 12,300 words, about 90 KB, 39 sections)
**Date of study:** 9 November 2026
**Target environment according to the prompt:** Claude.ai, Claude Free plan, web/desktop conversation (no API, no Claude Code)
**Status:** preliminary study. No application code has been generated or executed. The prompt was read and two web searches were made to check the current state of `pigpio`.

---

## 1. Executive summary

| Question | Answer |
|---|---|
| Classification (§0.6 of the prompt) | **CONDITIONALLY FEASIBLE** |
| Comparison with the Claude Free allowance | **NOT VERIFIED** (the Settings → Usage screen has not been supplied) |
| Recommendation | **Conditional GO**: only for a **reduced, staged MVP**. **NO-GO** for the full scope ("comparable to a commercial analyser") as currently worded |
| Estimated workload (realistic scenario, whole project) | ≈ 3.7 M tokens (input + output) → ≈ 4.9 M with a 30% reserve |
| Estimated workload (MVP only) | ≈ 1.9 M tokens → ≈ 2.5 M with reserve |

Main reasons:

1. **The hardware is the tighter constraint, not Claude.** A Raspberry Pi 3 running Linux and sampling via GPIO is not a general-purpose analyser. The prompt acknowledges this (§39), but sections 9, 13, 14 and 38 ask for functions "comparable to a commercial analyser", which contradicts that acknowledgement.
2. **Claude Free cannot validate most of the product.** It cannot touch the Pi, probably cannot run a GUI reliably, probably has no network access for installing dependencies, and cannot build a Windows `.exe`. Many acceptance criteria (AT04, AT19, AT21, AT25, AT26, etc.) depend on the user.
3. **The prompt contradicts itself on flow control.** Section 0 requires stopping and asking for approval; sections 37 and 38 call for acting as an autonomous agent and "continuing until everything is complete".
4. **The staged plan is sound** and is what makes the project feasible: MVP first, a physical proof of concept (PoC) before the GUI, and checkpoints in `PROJECT_PROGRESS.md`.

---

## 2. What this study covered and how reliable it is

**Done:**
- Full reading of section 0 (usage control), sections 1–3 (role, environment, GPIO investigation), 7 (acquisition engine), 26–29 (testing, OS, packaging) and 33–34 (quality), plus a keyword review of sections 4–6, 9–25, 30–32 and 35–39.
- Two web searches on the state of `pigpio` and its sampling parameters.

**Deliberately not done:** no code execution, no scaffolding, no measurements.

**Reliability labels used in this report:**
- **[VERIFIED]** checked against a source consulted today (see Annex A).
- **[UNVERIFIED]** comes from general knowledge or inference and must be confirmed in Stage 1.
- **[DERIVED]** calculated from verified values; not a measurement.

---

## 3. Breakdown of the project into work packages

| # | Package | Main content | Depends on | Verifiable without the Pi |
|---|---|---|---|---|
| WP0 | Feasibility and plan | This report, `PROJECT_PROGRESS.md`, `DEVELOPMENT_LOG.md` | — | Yes |
| WP1 | Hardware research | Pinout, electrical safety, acquisition methods, test plan | Exact Pi model and OS | Partly (documentary) |
| WP1b | Physical PoC | Minimal capture of 8 GPIOs, rate measurement, CPU, losses | WP1 + Pi + signal source | **No** |
| WP2 | Minimal architecture | `pyproject.toml`, data models, backend interface | WP1 | Yes |
| WP3 | Virtual backend | Deterministic 8-channel generator | WP2 | Yes |
| WP4 | Acquisition engine | Blocks, buffers, timestamps, overflows | WP3 | Yes (simulated) |
| WP5 | Minimal GUI | PyQt6, waveform viewer, zoom/pan | WP4 | **Limited** (see §6) |
| WP6 | Real GPIO backend | Integration with the verified method | WP1b, WP4 | **No** |
| WP7 | Basic trigger | Edge/level, limited pre/post capture | WP4 | Yes |
| WP8 | Measurements | Period, frequency, pulse width, duty cycle, cursors | WP4 | Yes |
| WP9 | UART decoder | First protocol | WP8 | Yes |
| WP10 | SPI + I2C | One decoder at a time | WP9 | Yes |
| WP11 | Sessions and export | Native session, CSV, VCD | WP4 | Yes |
| WP12 | Advanced features | Sequential trigger, CAN, LIN, auto-detection, jitter, search | MVP | Yes/No, depending on the feature |
| WP13 | Integration and performance | Regression, memory, performance | Everything | **Partly** |
| WP14 | Documentation and packaging | README, guides, PyInstaller, ZIP | Everything | **Partly** |

---

## 4. Technical feasibility on the Raspberry Pi 3

### 4.1 Verified facts about `pigpio`

- **[VERIFIED]** Its sampling period is 1, 2, 4, 5, 8 or 10 µs, with 5 µs as the default, and it is fixed when the daemon starts.
- **[VERIFIED]** It provides state-change notifications for GPIO 0–31 via a bit mask, and the `level` field reports the level of all GPIOs at once. This fits the prompt's requirement for a "common GPIO bank snapshot" (§7, §39.3).
- **[VERIFIED]** It does not work on the Raspberry Pi 5; the project's own repository rejects that board by design.
- **[VERIFIED]** The version packaged in Debian is listed as 1.78.
- **[VERIFIED, secondary sources: forums]** It is regarded as a "legacy", Raspberry Pi-specific library compared with `libgpiod`/`lgpio`; some users reinstall it manually on newer systems and others migrate to alternatives. Stage 1 must confirm whether the package exists in the chosen Raspberry Pi OS release.

### 4.2 Comparison of acquisition methods

| Method | Data model | Advantages | Risks | Preliminary assessment |
|---|---|---|---|---|
| `pigpio` (DMA + notifications) | Timestamped events with the level of 32 GPIOs (equivalent to sampling every 1–10 µs; **[UNVERIFIED]** how they are generated internally) | The only method evaluated that is likely to give a common snapshot of the 8 channels | Legacy library; conflicts with PWM/PCM if those are used; the timestamp is a 32-bit counter that wraps periodically **[UNVERIFIED]**; a slow reader can lose events | **Leading candidate** |
| `libgpiod` / character device | Per-line events with a kernel timestamp | Maintained; installable via apt; kernel timestamp **[UNVERIFIED]** | Each channel produces its own event stream; no common snapshot; the queue can overflow with dense signals | Fallback for slow signals |
| `RPi.GPIO` / GPIO Zero | Python callbacks | Simple | Unpredictable latency and scheduling. According to one forum post, `RPi.GPIO` no longer works on Bookworm without the `rpi-lgpio` shim | Control only, not capture |
| Python polling | Repeated reads | None in practice | High jitter; no synchronisation | Rejected (the prompt already limits it to a baseline) |
| C extension (own daemon) | To be defined | Better determinism and lower CPU use | Goes beyond the "Python only" scope and complicates distribution | Option if the PoC fails |

### 4.3 Realistic performance envelope **[DERIVED, not measured]**

With a nominal sampling period of 5 µs (200 kS/s) or 1 µs (1 MS/s), and requiring at least 8 samples per bit as a prudent minimum:

| Protocol | At 200 kS/s (5 µs) | At 1 MS/s (1 µs) |
|---|---|---|
| UART | up to ~25 kbaud (9,600 and 19,200 yes; 115,200 no) | up to ~125 kbaud (115,200 only just) |
| I2C | not advisable even at 100 kHz | 100 kHz marginal; 400 kHz no |
| SPI | only clocks of tens of kHz | a few hundred kHz at most |
| LIN (19.2 kbps) | yes | yes |
| CAN (125 kbps, after a transceiver) | no | marginal |
| CAN (≥500 kbps) | no | no |

A library's nominal rate does **not** guarantee a sustained end-to-end rate (the prompt itself demands this in §3.5). These figures are theoretical ceilings and must be measured with a signal generator in Stage 1b.

**Consequence:** the MVP should be centred on slow-to-medium UART, pulse measurements and low-speed signal capture. Promising fast SPI/I2C, CAN or reliable "jitter" analysis on this hardware would be misleading.

### 4.4 Electrical safety (summary)

- The GPIOs are 3.3 V and **not 5 V tolerant** **[UNVERIFIED in this session, but it is the rule the prompt itself sets and is consistent with the official documentation as generally known]**.
- A common ground is required, and 5 V or industrial signals need a level shifter or buffer with a known bandwidth.
- CAN and RS-485 are differential: they need a transceiver and must never be connected directly to the GPIOs.
- The prompt's candidate pins are BCM 4, 5, 6, 12, 13, 16, 17 and 22. They lie within GPIO 0–31, which is compatible with `pigpio` notifications. Conflicts still need checking against the exact model, any HATs and the boot configuration (§3.3 of the prompt).

### 4.5 Trigger and pre-trigger

Without a hardware trigger mechanism, triggering is **software-based, on data that has already been captured**. Pre-trigger is possible only while the circular buffer still holds the data, and the trigger position will carry an uncertainty equal to the delivery latency plus the sampling period. The "sequential trigger" of §9.4 is feasible as logic over captured data, but not as a hardware trigger.

---

## 5. Topology: recommendation

The prompt asks for a comparison of (A) everything on the Pi and (B) a headless service on the Pi with the GUI on a PC.

| Criterion | A. Everything on the Pi 3 | B. Pi service + remote GUI |
|---|---|---|
| CPU/RAM | The GUI competes with acquisition on a machine with 1 GB of RAM (Pi 3 B/B+) **[UNVERIFIED]** | The Pi only captures and transmits |
| Acquisition headroom | Lower; risk of losing events when redrawing | Higher |
| Installation | PyQt6 and PyQtGraph must be installed on ARM; compatibility to be checked | The GUI is installed on a PC with standard wheels; the Pi needs only the service |
| Control latency | Minimal | Local network; irrelevant for deferred capture |
| Reliability | No network dependency | Network drops must be handled (the prompt requires local data preservation, AT21) |
| User experience | Screen and keyboard on the Pi | Comfortable on a PC |

**Recommendation: B (headless service + GUI on a PC)**, with buffered capture held locally on the Pi and transferred once the capture finishes. This is most consistent with "do not compromise data integrity" and reduces the risk in WP5. It must be confirmed by measurements in the PoC. Option A remains as an experimental mode.

Impact on scope: B adds a network protocol, basic authentication and disconnection handling. I estimate +10–15% work compared with A, already included in the totals in section 8.

---

## 6. Feasibility of the Claude Free environment

### 6.1 What cannot be assumed

The following points are **not verified** and affect feasibility:

1. **Does Claude Free have code execution and file creation in this environment?** The prompt requires running `pytest`, `ruff` and `mypy`, and producing files and a ZIP. If these are unavailable, Claude can only write code in the conversation, and the user would have to run it and paste back the results. This multiplies the number of iterations.
2. **Network.** In the current session the execution environment has network access disabled. If the same holds for the project, `pip install PyQt6 pyqtgraph numpy scipy pandas pytest` will not work in Claude's environment, and the GUI and its tests cannot be run there.
3. **Allowance.** Claude Free limits usage per session and over rolling windows, with no publicly fixed figure. A project of millions of tokens will need many separate sessions with waiting periods between them.
4. **Context.** A prompt of ~22–28 thousand tokens resent in every session consumes a noticeable share of the context. The prompt itself warns of this (§0.11): keep it as a file and cite it by section.

### 6.2 What Claude can and cannot validate

| Acceptance criterion | Can Claude validate it? |
|---|---|
| AT01–03, AT06–07, AT09, AT11–14, AT16–18, AT20, AT22–23 | Yes, with the virtual backend and pytest (if execution is available) |
| AT19 (responsive GUI), AT15 (large captures navigable) | Only partly: requires PyQt6 and a graphical environment |
| AT04, AT05 (real acquisition), AT21 | **No**: require the physical Pi and real signals |
| AT08, AT10 (pre/post-trigger, sequential) | Yes in simulation; on real hardware it depends on the hardware |
| AT24 (documentation = code) | Yes, by review |
| AT25, AT26 (installation on Windows/Linux) | **No**: the user must run them on their own machines |

PyInstaller cannot build Windows executables from a Linux environment, so the `.exe` of §29 **cannot be produced by Claude**; it can only supply the build script for the user to run on Windows.

**Consequence:** the criterion in §27 ("the project must pass all acceptance tests") is unattainable with Claude Free alone. It should be rewritten as "passes the tests verifiable in simulation; the rest remain pending user validation".

---

## 7. Problems found in the prompt

### 7.1 Contradictions

| Where | Problem | Proposed resolution |
|---|---|---|
| §0.1 and §0.14 versus §37 and §38 | §0 forbids generating code until approval is given; §37 orders "continue implementing the complete project" and §38 ends with "begin with Phase 1… proceed through all phases". | Keep §0 as the overriding rule. Rewrite §37/§38 so that each stage ends at an approval gate |
| §0.14 versus §3 and §38 | §0.14 asks for the usage report as the first response; §3 and §38 ask for the GPIO investigation first | Order: report (this phase) → investigation → PoC |
| §0.7 (Stage 2: minimal skeleton, "do not create dozens of empty modules") versus §4.1 (a tree with dozens of modules, including `can_decoder.py` and `lin_decoder.py`) | The full tree should not be created all at once | Treat §4.1 as the destination, not the starting template |
| §0.13 (one approval per stage) versus §37 (never ask) | Two decision rules | Keep §0.13 |
| §27 (pass AT01–AT26) versus §6.2 of this report | Some ATs cannot be executed by Claude | Label each AT with who can run it |
| §1 and §38 ("functionality comparable to commercial analysers", "the maximum technically possible") versus §39 and §34.18 | Commercial equivalence is requested while promising it is prohibited | Replace with "the maximum the measured envelope allows" |

### 7.2 Leftovers and ambiguities

- **§28, line 2321:** "Do not retain instructions or dependencies for the previous data-acquisition hardware". There is no previous hardware in this prompt; it appears to be a leftover from an earlier version. It should be removed or clarified.
- **§2.1:** everything in English, including the GUI, documentation and README, whereas you work in Spanish. This is consistent if intended, but it should be confirmed. The repository documentation and this report would then be in different languages.
- **§2.2:** requires SciPy and Pandas as well as NumPy. On a Pi 3 these are heavy to install; if topology B is adopted, they should be client-only. I recommend marking them "client-only" or "optional".
- **§0.4 and §0.3** ask for "sessions" to be estimated without knowing the allowance; this report does so only qualitatively (see §8.3).
- **§3.1** leaves the exact model (3 B, 3 B+ or 3 A+) and the OS unspecified. The RAM of the 3 A+ is smaller than that of the 3 B/B+ **[UNVERIFIED]**, which would change the topology recommendation.

### 7.3 Scope risks

- **Too many decoders at once** (UART, SPI, I2C, CAN, LIN, plus "additional" ones in §13.6). The prompt already puts UART first; that priority should be kept.
- **Automatic protocol detection (§14) and jitter/correlation analysis (§11.3):** with a 1–10 µs resolution and no determinism guarantee, the results would be of low reliability. I recommend deferring them.
- **Advanced search (§15), additional export formats (§16.1) and a full virtual GPIO device (§17):** valuable but not necessary for the MVP.

---

## 8. Token estimate

### 8.1 Method and caveats

- Input and output are estimated separately for each stage.
- **Input** = prompt and files resent + accumulated conversation context + search and tool results. This is the part that grows most, because the previous context is reprocessed on every turn. **No distinction is made between fresh and cached input**, because Claude.ai does not expose that figure to the user.
- **Output** = code, tests, documentation, reports and explanations. Working assumptions: ~10 tokens per line of code, ~13–15 thousand lines of application Python, ~7–9 thousand lines of tests, ~60–80 thousand tokens of documentation.
- These are **planning estimates**, not measurements. They do not equate to a guaranteed number of messages or to subscription usage.
- "Sessions" = continuous blocks of work, **not** Claude Free allowance periods (their size is unknown).

### 8.2 Table by phase (figures in thousands of tokens, realistic scenario)

| Phase | Scope | Input | Output | Total | Sessions/interactions | Confidence | Dependencies |
|---|---|---:|---:|---:|---|---|---|
| 0 | Feasibility, plan, progress files | 30 k | 12 k | 42 k | 1–2 | High | — |
| 1 | Hardware research and feasibility documents | 120 k | 30 k | 150 k | 3–5 | Medium | Pi model and OS |
| 1b | Physical PoC (capture script, report) | 40 k | 25 k | 65 k | 3–6 (with user measurement cycles) | **Low** | Pi, wiring, generator |
| 2 | Skeleton and data models | 60 k | 35 k | 95 k | 2–3 | Medium | Phase 1 |
| 3 | Virtual backend and test vectors | 80 k | 45 k | 125 k | 2–4 | Medium | Phase 2 |
| 4 | Acquisition engine and integrity | 150 k | 70 k | 220 k | 4–6 | Medium | Phase 3 |
| 5 | Minimal GUI and viewer | 250 k | 110 k | 360 k | 6–10 | **Low** | Phase 4; PyQt6 |
| 6 | Real GPIO integration | 150 k | 60 k | 210 k | 4–8 | **Low** | Phases 1b and 4 |
| 7 | Basic trigger and capture | 100 k | 40 k | 140 k | 3–5 | Medium | Phase 4 |
| 8 | Measurements and edge detection | 120 k | 50 k | 170 k | 3–5 | Medium | Phase 4 |
| 9 | UART decoder | 90 k | 40 k | 130 k | 2–4 | Medium-high | Phase 8 |
| 10 | SPI and I2C | 180 k | 80 k | 260 k | 4–6 | Medium | Phase 9 |
| 11 | Sessions, CSV, VCD | 150 k | 70 k | 220 k | 3–5 | Medium | Phase 4 |
| 12 | Advanced features (each with its own gate) | 450 k | 200 k | 650 k | 10–20 | **Low** | MVP |
| 13 | Integration, regression, performance | 400 k | 120 k | 520 k | 6–12 | **Low** | Everything |
| 14 | Documentation, packaging, delivery | 250 k | 130 k | 380 k | 5–8 | Medium | Everything |
| **Total** | | **≈ 2,620 k** | **≈ 1,117 k** | **≈ 3,740 k** | **≈ 60–110** | | |

**MVP (§0.8): phases 0 to 9 and 11** → input ≈ 1,340 k, output ≈ 587 k, total ≈ **1,930 k**, with ≈ 38–65 interactions.

### 8.3 Summary by scenario

| Scenario | Estimated total | Reserve | Overall workload with reserve | Main assumptions |
|---|---:|---:|---:|---|
| Optimistic | ≈ 2.4 M | 25% (≈ 0.6 M) | ≈ 3.0 M | Pi and OS defined early; `pigpio` works without surprises; few corrections; code execution available |
| Realistic | ≈ 3.7 M | 30% (≈ 1.1 M) | ≈ 4.9 M | Normal integration; GUI needing iterations; PoC needing 1–2 rounds of adjustment |
| Pessimistic | ≈ 6.0 M | 25% (≈ 1.5 M) | ≈ 7.5 M | `pigpio` unavailable or unreliable on the chosen OS (method must change); GUI problematic for lack of a graphical environment; many debugging cycles with results pasted in by hand |
| MVP only (realistic) | ≈ 1.9 M | 30% (≈ 0.6 M) | ≈ 2.5 M | No phase 12 and no full packaging |

**Why the reserve:** (1) phases 1b, 5, 6, 12 and 13 have low confidence; (2) debugging in Claude.ai without integrated execution forces repeated cycles; (3) the accumulated context makes every turn more expensive; (4) real hardware may invalidate decisions already taken (§0.13: an architecture change requires re-approval).

**What could change the figures substantially:** availability of code execution; pasting long logs; the size of files that are re-read; a change of topology; a change of acquisition method; asking for "rewrite the whole file" instead of patches.

### 8.4 Token categories not reported

Claude.ai does not expose cached or reasoning tokens to the user. No figures have been invented for them.

---

## 9. Recommended staged plan

1. **Stage 0 (this one):** report + open decisions (§12). No code.
2. **Stage 1:** documentary research on `pigpio`/`libgpiod`/OS, and the `docs/*` of §3.7. No acquisition code.
3. **Stage 1b:** minimal physical PoC on the Pi. **Gate:** real performance report. If it fails, change of method with re-approval.
4. **Stages 2–4:** minimal skeleton, virtual backend, acquisition engine. First automated tests.
5. **Stage 5 with topology B:** minimal viewer on the PC.
6. **Stage 6:** integration with the real Pi.
7. **Stages 7–9 and 11:** basic trigger, measurements, UART, sessions/CSV/VCD.
8. **MVP gate.**
9. **Afterwards, one at a time:** SPI/I2C → VCD → sequential trigger → CAN/LIN (only with a transceiver and a sufficient rate) → the rest.

**Proposed MVP (stricter than §0.8):**
- 8-channel capture with a measured, declared rate.
- Viewer with zoom and scrolling.
- Edges and basic measurements with the uncertainty shown.
- Edge/level trigger with an uncertainty warning.
- UART at speeds the measured envelope allows.
- Session saving and CSV.
- A losses-and-limits report visible in the interface.

**Explicitly deferred:** CAN, LIN, automatic protocol detection, correlation/jitter, sequential trigger, advanced search, automatic `.exe`.

---

## 10. What you need to check manually

In Claude.ai, **Settings → Usage** (the name may vary). Report only what is displayed:

1. Usage or remaining capacity for the current session, if shown.
2. Whether any limit has been reached.
3. Reset time or next availability.
4. Any weekly or rolling limit.
5. The selected model.

It is also worth checking in your account:
- Whether **code execution and file creation** are available (Settings → Capabilities, or the current name).
- Whether you can **attach files** in a new conversation, and how many.

There is no need to share credentials, billing details or personal data. Until you do, the allowance comparison remains **NOT VERIFIED**.

---

## 11. Main risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| `pigpio` unavailable or unstable on the chosen OS | Medium | High | Choose an OS with a verified package; plan B with `libgpiod`; plan C with an own daemon in C |
| Real sustained rate far below the nominal one | High | High | PoC before the GUI; publish only measured figures |
| Event loss with dense signals | Medium | High | Sequence counters and warnings; limit channels or rate |
| GUI cannot be tested in Claude's environment | High | Medium | Separate logic from presentation; tests without the GUI; user validation |
| Claude Free allowance insufficient per session | **Unknown** | High | Small stages, checkpoints, do not resend the whole prompt |
| No signal generator available | Medium | Medium | GPIO output-to-input loopback with declared limits |
| Electrical damage (5 V on a GPIO) | Low | **Critical** | Safe wiring table; level shifting; reject unsafe configurations |
| Scope drift towards "commercial" | High | High | Frozen MVP and re-approval for every extra |
| Prompt contradictions (autonomy vs. approval) | High | Medium | Correct the prompt before continuing |

---

## 12. GO / NO-GO recommendation and decisions needed

**Recommendation: conditional GO.**
- **GO** for stages 0 to 4 and the physical PoC, with the reduced MVP in section 9.
- **NO-GO** for the full 39-section scope as a single deliverable under Claude Free.
- **Conditions:** (a) fix the contradictions in §7.1; (b) confirm your account's capabilities (§10); (c) accept a multi-session schedule separated by usage limits; (d) accept that part of the validation will be done by you.

**Minimum information needed to refine the study:**
1. **Exact Pi model** (3 B, 3 B+ or 3 A+) and the **OS/kernel** you intend to use (32-bit or 64-bit).
2. **Do you have a signal generator or reference analyser** to measure the real rate?
3. **Do you approve topology B** (service on the Pi + GUI on the PC)? Which operating system does the PC run?
4. **Language:** should all code and documentation remain in English (§2.1)?
5. What **Settings → Usage** shows, and whether you have code execution and file creation.

**Next step, only after your explicit approval:** Stage 1 (documentary research), still without acquisition code.

---

## Annex A — Sources consulted today

| Source | What it supports |
|---|---|
| `pigpiod_if2` documentation (Debian man page) | Sampling periods of 1/2/4/5/8/10 µs, 5 µs by default; notifications by GPIO mask with the level of all pins |
| `pigpio.py` 1.78 source (sources.debian.org) | Library version; notification flags; `notify_open/begin/pause/close` |
| `joan2937/pigpio` repository, issue #589 | `pigpio` does not support the Raspberry Pi 5 |
| Node-RED, DietPi and openHAB forums (secondary sources) | Legacy status of `pigpio`; changes to `RPi.GPIO` and GPIO device names in recent OS releases; migration to `lgpio`/`rgpio` |

**To be verified in Stage 1 (everything marked [UNVERIFIED]):** availability of `pigpio` on the chosen OS, the exact notification format and the behaviour of the time counter, `libgpiod` v2 capabilities, GPIO voltage and current limits in the official datasheet, RAM and clock of each Pi 3 variant, PyQt6 compatibility with 32/64-bit ARM.

---

*This report is a planning estimate. No performance figure has been measured, and no token figure is a commitment of consumption.*
