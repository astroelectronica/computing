
---

# 0. MANDATORY CLAUDE FREE USAGE ASSESSMENT AND CONTROL

## 0.1 Execution environment and non-negotiable rule

The intended development environment is:

- Platform: Claude.ai.
- Subscription: Claude Free.
- Interface: Claude.ai web or desktop conversation.
- This is not an Anthropic API project and is not assumed to use Claude Code.

You must adapt the workflow to the actual capabilities and limits of Claude Free.

**ABSOLUTE RULE: Do not generate application source code, project scaffolding, or implementation files until the user has received and explicitly approved the pre-development feasibility report described in this section.**

You may perform analysis, research, estimation, planning, and produce the requested assessment documents before approval. Do not begin implementation prematurely.

Do not claim that Claude Free provides a fixed daily token allowance. Subscription usage may be governed by session or rolling limits and may vary with model, demand, conversation length, files, and tool usage. Do not equate a token estimate with a guaranteed number of Claude messages or a guaranteed amount of subscription usage.

## 0.2 Mandatory pre-development assessment

The target acquisition hardware is a Raspberry Pi 3 development board used as the eight-channel digital input front end. Unless the user specifies otherwise, treat the exact board revision as UNKNOWN; do not silently assume Raspberry Pi 3 Model B, B+, or A+. The first assessment must identify which exact model/revision, Raspberry Pi OS version, kernel, and 32-bit/64-bit userspace are intended.

The Raspberry Pi 3 is a Linux single-board computer, not a dedicated logic-analyzer DAQ or FPGA. GPIO sampling, timing determinism, CPU/RAM limits, DMA/peripheral conflicts, operating-system scheduling, and safe input voltage are central feasibility constraints. Do not promise the performance of a commercial logic analyzer.

Assume eight digital channels connected directly to GPIO only as the baseline. Do not assume an external ADC, FPGA, CPLD, RP2040, dedicated logic-analyzer IC, or level-shifter board is included. If an external acquisition front-end would materially improve performance, present it as an optional alternative with cost/complexity implications and wait for user approval before changing the hardware scope.

The application topology is not yet fixed: investigate both (A) acquisition and GUI running locally on the Raspberry Pi 3 and (B) a headless acquisition service on the Pi with the full GUI running on a separate Windows/Linux computer over Ethernet/Wi-Fi. Compare CPU/RAM use, latency, reliability, installation complexity, and user experience. Recommend one topology; do not assume remote operation is equivalent to deterministic acquisition.



Before implementation, perform all of the following:

1. Read and decompose the entire project specification.
2. Identify every major subsystem, deliverable, dependency, and acceptance test.
3. Identify technical uncertainties, especially those dependent on Raspberry Pi 3 GPIO sampling, Linux scheduling, DMA-based sampling, electrical safety, and exact board revision.
4. Separate essential MVP functionality from advanced and optional functionality.
5. Identify work that can be completed and validated independently.
6. Estimate the effort and token workload for every development stage.
7. Identify likely high-cost activities: large code generation, large file reviews, repeated debugging, GUI integration, protocol decoder validation, and documentation.
8. Propose a staged delivery plan designed to produce a usable application as early as possible.
9. Identify what usage information must be checked manually by the user in Claude.ai.
10. Present the report and wait for explicit user approval.

The assessment must be specific to this project, not a generic statement that the project is large.

## 0.3 Token estimation methodology

Estimate token consumption separately for each phase and for the project as a whole.

For every phase, provide:

- Estimated input tokens: project instructions, retained conversation context, source files, documentation, and other material Claude must process.
- Estimated output tokens: generated source code, tests, documentation, explanations, and reports.
- Estimated total tokens: input plus output, where meaningful.
- Expected number of Claude interactions or work sessions, expressed as a range rather than a promise.
- Expected debugging and revision allowance.
- Confidence level: high, medium, or low.
- Main assumptions and factors that could change the estimate.

If the platform exposes additional token categories, such as cached input or thinking tokens, report them separately. Do not invent categories or values that the interface does not expose.

Provide three scenarios:

- Optimistic: requirements are clear, hardware research resolves quickly, and few revisions are needed.
- Realistic: normal integration work and a moderate number of corrections.
- Pessimistic: hardware constraints, integration problems, and repeated debugging require substantial rework.

Include a contingency reserve of at least 25% over the realistic estimate. Explain why the reserve is needed.

Use token estimates as planning estimates, not as exact measurements. Do not claim to know the precise internal token count of an unsubmitted future conversation. If exact counting is unavailable in Claude.ai, explicitly label figures as estimates.

## 0.4 Required estimation tables

Create a phase-level table with at least these columns:

| Phase | Scope | Estimated input tokens | Estimated output tokens | Estimated total | Expected sessions/interactions | Confidence | Dependencies |
|---|---|---:|---:|---:|---:|---|---|

Also provide a summary table:

| Scenario | Estimated total tokens | Contingency | Estimated overall workload | Main assumptions |
|---|---:|---:|---:|---|
| Optimistic | ... | ... | ... | ... |
| Realistic | ... | ... | ... | ... |
| Pessimistic | ... | ... | ... | ... |

Do not leave estimates as unexplained placeholders. If the information is insufficient for a responsible estimate, state exactly what is missing and ask only for the information that materially affects the estimate.

## 0.5 Claude Free usage verification

Ask the user to inspect Claude.ai's current usage information, normally available under **Settings → Usage** (interface labels may change).

Ask the user to report what Claude actually displays, such as:

- Current session usage or remaining capacity, if shown.
- Whether a usage limit has been reached.
- Reset time or next available time, if shown.
- Any weekly or other rolling limit information displayed.
- The model selected for the work, if visible.

Do not ask the user to disclose account credentials, private billing information, or unrelated personal information.

Important limitations:

- You cannot assume you can inspect the user's Claude account or its remaining allowance.
- Do not invent the user's remaining usage, reset time, daily token quota, or number of messages.
- Do not state that a project will definitely fit into one session based only on a token estimate.
- If Claude's interface does not expose a numeric allowance, say so and make a qualitative feasibility assessment.
- If current usage information is unavailable, mark the quota comparison as **NOT VERIFIED** and request the minimum information needed from the user.
- Do not use Anthropic API pricing or API token quotas as a substitute for Claude Free subscription limits.
- Do not instruct the user to create an API key or incur API charges unless the user explicitly chooses to change to API usage.

## 0.6 Feasibility classification and go/no-go decision

After estimating the work and reviewing the usage information supplied by the user, classify the project:

- **FEASIBLE IN STAGED SESSIONS:** the scope can reasonably be delivered through multiple Claude Free usage periods, with saved project state between them.
- **CONDITIONALLY FEASIBLE:** the project is viable only if optional features are deferred, the MVP is prioritized, or the user accepts a longer multi-session schedule.
- **USAGE INFORMATION INSUFFICIENT:** the project estimate exists, but the available Claude Free allowance cannot be assessed from the information supplied.
- **NOT REASONABLY FEASIBLE UNDER CURRENT CONSTRAINTS:** explain which scope or workflow assumptions make completion impractical and propose a reduced MVP or a different user-approved approach.

Do not equate “not feasible in one session” with “not feasible overall.” Evaluate staged development across successive usage resets.

Provide a clear GO / NO-GO recommendation and explain the trade-offs. Wait for explicit approval before implementation.

## 0.7 Independent development stages and deliverable gates

The project must be divided into small, independently useful and verifiable stages. Each stage must have:

- A clearly bounded scope.
- Explicit prerequisites.
- A list of files expected to be created or modified.
- A definition of done.
- Relevant automated tests.
- A verification report.
- A checkpoint in the progress file.
- An estimate of remaining work.

Never attempt to generate the entire application in one enormous response.

Use this staged delivery strategy. The detailed technical workflow in Section 32 remains applicable; this section adds usage-management gates and MVP priorities.

### Stage 0 — Feasibility, token budget, and project plan

Deliver:

- `docs/DEVELOPMENT_FEASIBILITY_AND_TOKEN_BUDGET.md`
- `PROJECT_SPECIFICATION.md` (the approved project requirements, or a reference to this master specification)
- Initial `PROJECT_PROGRESS.md`
- Initial `DEVELOPMENT_LOG.md`
- A staged implementation plan.
- A GO / NO-GO recommendation.

No application source code may be generated in this stage.

### Stage 1 — Raspberry Pi 3 hardware research and acquisition feasibility

Deliver:

- `docs/HARDWARE_CAPABILITIES.md`
- `docs/ACQUISITION_FEASIBILITY.md`
- Verified official references and investigation date.
- Supported and unsupported acquisition approaches.
- A realistic MVP feature boundary based on the Raspberry Pi 3 GPIO subsystem and verified sampling method.

Do not proceed to a hardware implementation based on unverified assumptions.

Before the complete GUI, implement only after approval a tiny physical proof-of-concept that:
- identifies the exact Pi 3 model and OS/kernel;
- configures eight safe GPIO inputs;
- acquires either synchronized sample masks or timestamped edge events using the verified method;
- runs repeatable test patterns;
- measures sustained throughput, CPU, RAM, temperature, timing uncertainty, and missed-event/loss indicators;
- records a report and raw test capture.
The proof-of-concept must establish a realistic MVP performance envelope. It is not the final application.

### Stage 2 — Minimal architecture and project skeleton

Deliver:

- Validated directory structure.
- `pyproject.toml` and dependency strategy.
- Core data models.
- Hardware abstraction interface.
- Basic application entry point.
- Architecture documentation.
- Import and startup tests.

Keep the skeleton minimal. Do not create dozens of empty modules merely to reproduce the proposed directory tree.

### Stage 3 — Virtual backend and deterministic test signals

Deliver:

- Working virtual device backend.
- Eight-channel deterministic sample generation.
- Known test vectors.
- Backend contract tests.
- A minimal way to run and inspect the virtual backend.

This stage must allow meaningful development without physical Raspberry Pi hardware.

### Stage 4 — Core acquisition and data integrity

Deliver:

- Acquisition engine using the verified acquisition contract.
- Block and buffer handling.
- Timestamp model.
- Overflow and interruption reporting.
- Data integrity tests.
- Acquisition diagnostics.

The virtual backend must pass the core acquisition tests before real hardware integration is considered complete.

### Stage 5 — Minimal usable GUI and waveform viewer

Deliver:

- Launchable PyQt6 application.
- Eight-channel display model.
- Basic waveform rendering.
- Zoom, pan, time axis, and channel visibility.
- Simulation mode clearly identified.
- GUI responsiveness tests.

At the end of this stage, aim for the first usable MVP, even if advanced features are not yet implemented.

### Stage 6 — Raspberry Pi 3 GPIO integration

Deliver:

- Device discovery and connection.
- Configuration validation.
- Verified acquisition implementation.
- Safe disconnect and error recovery.
- Hardware-specific tests, clearly marked as not run if no physical Raspberry Pi 3 is available.
- Updated hardware limitations and test report.

Do not claim physical hardware validation unless it was actually performed.

### Stage 7 — Basic trigger and capture management

Deliver:

- Basic edge and level triggers where supported by the acquisition design.
- Capture state management.
- Pre-trigger/post-trigger only to the extent technically achievable.
- Trigger timing uncertainty documentation.
- Deterministic tests.

### Stage 8 — Measurements and edge analysis

Deliver:

- Edge detection.
- Period, frequency, pulse width, duty cycle, and transition counts.
- Cursor measurements.
- Accuracy and uncertainty warnings.
- Unit tests with known signals.

### Stage 9 — First protocol decoder: UART

Deliver:

- UART decoder interface and implementation.
- Configuration and error reporting.
- Known test vectors.
- Waveform-linked decoded events.
- Decoder tests.

UART is the first protocol priority. Do not start several protocol decoders simultaneously.

### Stage 10 — SPI and I2C decoders

Deliver and validate each decoder independently. A decoder is not complete until its supported modes, edge cases, and known test vectors are documented and tested.

### Stage 11 — Data and session management

Deliver:

- Native session save/load.
- CSV and VCD export where specified.
- Metadata and versioning.
- Import validation.
- Round-trip tests.

### Stage 12 — Advanced features

Implement optional features in separately estimated increments, such as:

- Advanced and sequential triggers.
- CAN and LIN decoding, subject to suitable signal conditioning and sample quality.
- Additional decoders.
- Automatic protocol suggestions.
- Advanced search.
- Jitter and correlation analysis.
- Extended diagnostics.

Each feature must have its own feasibility and test gate.

### Stage 13 — Integration, hardening, and performance

Deliver:

- Full integration tests.
- Regression tests.
- Performance measurements.
- Memory and responsiveness review.
- Error-path testing.
- Updated known limitations.

### Stage 14 — Documentation, packaging, and final delivery

Deliver:

- README and user guide matching the actual implementation.
- Installation instructions for Windows and Linux.
- Build scripts and packaging where practical.
- Final validation report.
- Complete source archive and ZIP package.

Optional features that cannot be completed within the available usage or project constraints must be explicitly listed as deferred, not represented as complete.

## 0.8 MVP-first strategy

Prioritize a useful, testable product before attempting the complete advanced feature set.

The initial MVP target is:

1. Application starts without hardware.
2. Virtual backend generates eight synchronized logical channels with known test data.
3. GUI displays eight channels and supports basic navigation.
4. Acquisition data model and timestamps are consistent.
5. Basic edge detection and timing measurements work.
6. Basic trigger behavior works within the verified implementation limits.
7. UART decoding works with deterministic test vectors.
8. Session save/load or a documented minimal capture export works.
9. Automated tests verify the MVP.
10. Hardware limitations are clearly displayed and documented.

After the MVP is verified, implement additional features incrementally. Do not delay a usable MVP while attempting optional CAN, LIN, automatic protocol detection, or elaborate trigger sequencing.

The MVP must not falsely imply that virtual acquisition validates the physical Raspberry Pi 3 GPIO backend.

## 0.9 Session and context management

Claude Free usage may be interrupted by session or rolling limits. Every work session must therefore end with a durable checkpoint.

Maintain these project-management files at the project root:

### `PROJECT_PROGRESS.md`

Must contain:

- Current project status.
- Current stage and subtask.
- Completed stages.
- Pending stages.
- Current verified working state.
- Files created, modified, or removed in the latest work session.
- Tests executed and their exact results.
- Known defects and limitations.
- Hardware validation status.
- Next three concrete actions.
- Current estimates of remaining work.
- Date of last update.

### `DEVELOPMENT_LOG.md`

Append concise entries recording:

- Date/session identifier.
- Stage and task.
- Important technical decisions and their reasons.
- Files changed.
- Tests and commands run.
- Failures and fixes.
- Deferred items.
- Any change to token/workload estimates.

Do not rewrite the entire log at every update. Append new entries.

### `docs/DEVELOPMENT_FEASIBILITY_AND_TOKEN_BUDGET.md`

Maintain:

- Initial estimate.
- Actual observed workload information, if Claude exposes it.
- Estimate revisions.
- Completed versus remaining phases.
- Risks and assumptions.
- Usage-related decisions.

Do not fabricate actual token consumption when the interface does not expose it.

## 0.10 Mandatory end-of-session procedure

At the end of every work session, or whenever the user says the usage limit is approaching:

1. Stop starting new features.
2. Finish the current safe operation or leave the code in a clearly documented state.
3. Save all modified files.
4. Run the smallest relevant test set that can be completed reliably.
5. Record exact test outcomes; never claim unexecuted tests passed.
6. Update `PROJECT_PROGRESS.md`.
7. Append to `DEVELOPMENT_LOG.md`.
8. Update remaining-work estimates.
9. List any incomplete or partially generated files.
10. Provide a concise continuation prompt for the next Claude.ai session.

The continuation prompt must tell the next session to read `PROJECT_PROGRESS.md`, `DEVELOPMENT_LOG.md`, and the relevant source files before changing anything. It must not ask the next session to regenerate completed code.

If a usage limit is reached unexpectedly, preserve the last known working state and resume only after the platform permits further use.

## 0.11 Context efficiency and anti-waste rules

To minimize unnecessary Claude Free usage:

- Do not paste the entire master specification into every follow-up message.
- Keep the master specification as a project file and refer to it by section.
- Read only the source files relevant to the current task.
- Do not regenerate complete files when a focused patch is sufficient.
- Avoid repeatedly explaining settled architectural decisions.
- Reuse existing interfaces and tests.
- Implement one bounded task at a time.
- Ask for the smallest useful diagnostic output rather than huge logs.
- Summarize long investigations into durable project documentation.
- Avoid speculative implementation before hardware research.
- Avoid creating optional features before the MVP passes.
- Do not produce lengthy explanations when a concise implementation report is sufficient.
- Do not repeatedly reformat or rewrite stable files without a reason.
- Do not run expensive or broad test suites after every trivial edit; select relevant tests, then run full regression suites at integration gates.
- Never remove tests or weaken assertions merely to obtain a passing result.

## 0.12 File delivery and code-generation discipline in Claude.ai

Claude.ai may not provide the same persistent local project workspace as a dedicated coding agent. Adapt delivery to the capabilities actually available in the current interface.

When creating code:

- Generate complete, internally consistent files, not disconnected fragments.
- Clearly identify each file by its relative path.
- Never say a file was saved to the user's computer unless the interface actually created a downloadable artifact.
- If the interface cannot maintain a project directory, provide files in manageable batches and instruct the user how to assemble them.
- Prefer downloadable project archives when the platform supports reliable file creation.
- Keep each delivery batch small enough to inspect and verify.
- Include a manifest of files in every batch.
- Never assume files from a previous Claude.ai conversation remain accessible. Ask the user to attach or provide the current project archive when required.
- Before replacing a file, inspect the current version or ask the user to provide it. Do not overwrite unknown user changes.

## 0.13 Change control and stage approval

The user gives one approval to begin the staged project after reviewing the feasibility report. That approval does not require repeated permission for ordinary implementation tasks within the agreed stage.

However:

- Stop and request approval if a material hardware limitation changes the project scope.
- Stop and request approval if the proposed approach introduces new costs, paid APIs, or a different subscription.
- Stop and request approval if a major architectural change invalidates previous work.
- Stop and request approval before dropping an agreed MVP feature.
- Report any feature that must be deferred because the usage budget or technical feasibility is insufficient.

At each stage gate, present a concise report and recommend whether to continue. The user may approve the next stage or ask for changes.

## 0.14 Required initial response from Claude

The first response after receiving this master specification must NOT contain generated application source code.

It must contain:

1. Confirmation that the target environment is Claude Free on Claude.ai.
2. A concise decomposition of the project into work packages.
3. The detailed token-estimation table.
4. Optimistic, realistic, and pessimistic workload scenarios.
5. The contingency reserve.
6. The limits of estimating tokens versus Claude Free subscription usage.
7. The exact usage information the user must inspect in Settings → Usage.
8. The MVP definition.
9. The independent stage plan and deliverables.
10. Key technical and usage risks.
11. A GO / NO-GO / INSUFFICIENT INFORMATION recommendation.
12. A request for explicit approval before code generation.

If the user has not supplied current usage information, complete the engineering workload estimate anyway, mark the subscription quota comparison as NOT VERIFIED, and ask the user to provide the displayed usage details. Do not block useful analysis merely because the quota display is unavailable.

Only after the user approves the plan may you begin Stage 1 or the next approved stage. No source code may be generated before approval.

---

# MASTER PROJECT SPECIFICATION
# PROFESSIONAL 8-CHANNEL DIGITAL LOGIC ANALYZER
## Python Application Using Raspberry Pi 3 GPIO

---

# 1. ROLE AND GENERAL OBJECTIVE

Act as a multidisciplinary senior engineering team consisting of:

- Senior Python software architect.
- Digital electronics engineer.
- GPIO data acquisition specialist.
- Raspberry Pi 3 GPIO and Linux acquisition specialist.
- Embedded systems engineer.
- Signal processing engineer.
- GUI/UX software developer.
- Digital communication protocol specialist.
- Software testing and quality assurance engineer.

Your task is to design, implement, test, document, and package a complete professional-grade eight-channel digital logic analyzer using the Raspberry Pi 3 as the GPIO acquisition platform.

The final application must provide the maximum functionality technically achievable with the Raspberry Pi 3 GPIO hardware, without claiming dedicated-logic-analyzer performance.

The baseline hardware is eight 3.3 V digital inputs sampled by the Raspberry Pi 3. The software must expose the actual acquisition mode (uniform sampled data or timestamped edge events), measured effective sample rate, timing uncertainty, minimum detectable pulse width, and all known loss conditions. If a requested feature requires an external front-end, identify it as optional and do not silently add it to the baseline hardware.

The software must offer functionality comparable to professional commercial logic analyzers, including advanced waveform visualization, triggering, protocol decoding, timing measurements, data analysis, acquisition management, and session recording.

The project must be developed as a complete, modular, maintainable, extensible Python application.

This is an engineering project, not a demonstration or educational prototype.

The final result must be a working software product.

## 1.1 Fundamental development principles

Follow these principles throughout the entire project:

1. Hardware accuracy takes priority over advertised performance.
2. Data integrity takes priority over acquisition speed.
3. All eight channels must share a consistent acquisition time reference.
4. No data loss may occur silently.
5. The GUI must never block during acquisition.
6. Hardware-dependent functionality must be isolated from the application core.
7. All acquisition limitations must be explicitly documented.
8. All measurements must include their effective time resolution and relevant uncertainty.
9. All features must be implemented and tested before being declared operational.
10. Never fabricate hardware capabilities, API functions, register names, or performance figures.

Do not simplify the requirements without explicitly explaining why a feature cannot be implemented.

If a requested feature is physically impossible or unsupported by the Raspberry Pi 3 GPIO/OS acquisition path, implement the closest technically valid alternative and document the limitation. Never disguise Linux user-space timing as deterministic hardware timing.

---

# 2. LANGUAGE AND DEVELOPMENT ENVIRONMENT

## 2.1 Programming language

Use:

- A Python version explicitly supported by the selected Raspberry Pi OS release and all chosen dependencies; verify compatibility before pinning it.
- Modern Python programming practices.
- Object-oriented programming.
- Type annotations.
- Dataclasses where appropriate.
- Abstract base classes for hardware interfaces.
- Modular architecture.

All source code must be written entirely in ENGLISH.

This includes:

- File names.
- Directory names.
- Class names.
- Function names.
- Variable names.
- Comments.
- Docstrings.
- Exception messages.
- Logging messages.
- GUI labels.
- Menus.
- Tooltips.
- Configuration files.
- README.md.
- Technical documentation.
- Test descriptions.

Use English consistently throughout the entire application.

## 2.2 Main libraries

Use the following libraries when appropriate:

| Purpose | Library |
|---|---|
| GUI | PyQt6 |
| High-performance waveform visualization | PyQtGraph |
| Hardware communication | Raspberry Pi GPIO interface library |
| Numerical processing | NumPy |
| Scientific computing | SciPy |
| Data management | Pandas |
| Configuration | PyYAML |
| Serialization | JSON |
| Binary storage | NumPy / structured binary formats |
| Testing | Pytest |
| Logging | Python logging |
| Packaging | PyInstaller |
| GPIO access | Verified Python/C GPIO binding or service API |
| Documentation | Markdown |

Avoid unnecessary dependencies.

Justify any additional dependency.

Use compatible and stable library versions.

Create a complete requirements.txt with pinned or bounded dependency versions.

---

# 3. FIRST TASK: COMPLETE RASPBERRY PI 3 GPIO AND ACQUISITION INVESTIGATION

IMPORTANT:

Do not start writing the acquisition engine until the Raspberry Pi 3 hardware investigation and a measurable acquisition feasibility study are complete.

Use current official Raspberry Pi documentation, the relevant BCM2837/BCM2837B0 documentation, Raspberry Pi OS/kernel documentation, and primary documentation/source code for any GPIO sampling library considered. Record document versions, URLs, access date, and the exact board/OS assumptions.

Official starting points (verify current pages and exact applicability):

- https://www.raspberrypi.com/products/raspberry-pi-3-model-b/
- https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
- https://www.raspberrypi.com/documentation/computers/processors.html
- https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio
- https://github.com/joan2937/pigpio
- https://abyz.me.uk/rpi/pigpio/
- https://docs.kernel.org/userspace-api/gpio/chardev.html

Do not assume that every library or kernel interface supports every Raspberry Pi OS release. Verify maintenance status, package availability, Python compatibility, kernel compatibility, and whether the library works on the selected Pi 3 revision.

## 3.1 Exact board and operating-system identification

Determine and document:

1. Exact model: Raspberry Pi 3 Model B, 3 Model B+, or 3 Model A+ (or another explicitly identified variant).
2. SoC revision: BCM2837 or BCM2837B0 as applicable.
3. CPU architecture and clock characteristics.
4. Available RAM and practical memory budget after OS and GUI overhead.
5. GPIO header and available GPIO lines.
6. Raspberry Pi OS release, kernel version, and 32-bit/64-bit status.
7. Python version supported by that OS image.
8. Whether the intended PyQt6/PyQtGraph versions are installable and performant on the Pi.
9. Power supply and thermal considerations during sustained acquisition.
10. Interfaces or pins reserved by boot, HAT EEPROM, I2C, SPI, UART, PWM, PCM/I2S, SDIO, Bluetooth, or other peripherals.

If the user has not specified the exact board revision or OS, provide a provisional assessment with clearly labelled assumptions and ask for the minimum details needed to finalize it.

## 3.2 GPIO electrical safety — mandatory

Verify the official electrical specifications for the exact board/SoC. At minimum, investigate and document:

- GPIO logic voltage (3.3 V domain).
- GPIO pins are NOT 5 V tolerant; never apply 5 V directly.
- Input-low and input-high threshold specifications and their conditions.
- Absolute maximum ratings, clamp/injection current limits, and power-off/back-powering risks where documented.
- Input leakage and capacitance where documented.
- Pull-up/pull-down behavior and resistor constraints.
- Common ground requirements.
- Signal source impedance, edge rate, ringing, overshoot, undershoot, and cable effects.
- Protection against ESD and accidental overvoltage.
- Safe use of external level shifters, buffers, series resistors, and voltage dividers, including their bandwidth and edge distortion.
- Whether input protection can degrade timing or signal integrity.

Never recommend connecting 5 V logic directly to a Pi GPIO. Do not assume a resistor divider alone is suitable for every high-speed digital signal. Do not connect differential CAN_H/CAN_L or RS-485 A/B signals directly to GPIO; an appropriate transceiver/receiver is required. Do not connect negative-voltage or industrial signals directly.

Create a clear pinout and safe wiring diagram/table for eight inputs plus ground. The user must be able to identify physical header pin numbers and BCM GPIO numbers separately.

## 3.3 Eight-channel pin allocation

Create a configurable eight-channel mapping based on BCM GPIO numbering, not physical header numbering alone.

Investigate conflicts with:

- GPIO2/GPIO3 (I2C and fixed board pull-up characteristics).
- GPIO7–GPIO11 (SPI0 functions).
- GPIO14/GPIO15 (UART functions).
- GPIO18–GPIO21 (PCM/I2S and alternate functions).
- GPIO0/GPIO1 (HAT ID EEPROM use).
- Any pins needed by the selected sampling peripheral or operating system.

Propose a conservative default set of eight GPIO inputs only after checking the exact model and the chosen acquisition library. A possible candidate set to investigate is BCM GPIO 4, 5, 6, 12, 13, 16, 17, and 22; this is NOT an unconditional guarantee and must be validated against the selected peripheral, HATs, and OS configuration. Make pin assignment configurable and reject conflicts.

## 3.4 Acquisition technology comparison

Investigate and compare at least:

1. `pigpio` DMA-based GPIO sampling, including its sample clock, DMA use, PCM/PWM peripheral conflicts, supported sample intervals, buffer limits, timestamp/tick behavior, notification/callback latency, and compatibility with the target Pi 3 OS.
2. Linux GPIO character-device/libgpiod edge events, including kernel event timestamps, event buffering, scheduling effects, event loss reporting, and suitability for dense digital waveforms.
3. `RPi.GPIO` or GPIO Zero polling/callbacks, only as lower-performance/control alternatives; do not assume Python callbacks are a deterministic high-speed sampler.
4. Direct Python polling or repeated `digitalRead` loops, as a baseline only; do not treat them as a high-speed synchronized acquisition method.
5. Any other well-supported method, but only with primary-source evidence and a reproducible test plan.

Do not assume that a callback-based edge API provides a complete uniformly sampled waveform. Distinguish sampled-level acquisition from timestamped edge-event acquisition. Explain which data model and analysis features each method can honestly support.

If `pigpio` is considered, verify its current maintenance and package status for the chosen Raspberry Pi OS release. Do not blindly rely on old installation instructions or assume it is preinstalled.

## 3.5 Sampling performance and data integrity

For the selected method, determine and separately report:

- Nominal/configurable sampling interval.
- Theoretical sample rate.
- Actual measured sample rate on the exact Pi 3 model.
- Sustainable sample rate with eight channels enabled.
- Minimum detectable pulse width under tested conditions.
- Timing quantization and timestamp uncertainty.
- Inter-channel skew (or evidence that all channels are represented by a common GPIO bank snapshot).
- CPU use, RAM use, temperature, and throttling under load.
- Buffer capacity and maximum capture duration.
- Data transfer overhead to the Python process.
- Loss/overflow detection and whether loss can be proven or only inferred.
- Effects of GUI rendering, Wi-Fi/Ethernet, disk I/O, and background processes.
- Long-run stability and repeatability.

Do not turn a library's configurable sampling interval into a claim of guaranteed end-to-end sustained acquisition. A 1 microsecond nominal sample interval, if supported by the selected library, is not proof of one million reliable samples per second delivered to the application for an unlimited duration.

Use an external signal generator or independently characterized test source if available. If none is available, design repeatable loopback tests using safe GPIO outputs or another suitable source, and clearly state the limits of self-testing. Never claim verified performance without actual execution on the physical target board.

## 3.6 Trigger feasibility

Separate:

- Hardware/peripheral-assisted trigger, if a verified mechanism exists.
- DMA/sample-block trigger evaluated against captured samples.
- Software trigger evaluated after samples/events reach the process.

Investigate whether the selected Pi 3 acquisition mechanism can preserve pre-trigger data, capture post-trigger data, and timestamp the trigger with known uncertainty. Do not claim hardware trigger capability merely because the library offers edge callbacks. Document latency, event coalescing, buffer behavior, and trigger-position uncertainty.

## 3.7 Acquisition feasibility deliverables

Before implementation, generate:

- `docs/HARDWARE_CAPABILITIES.md`
- `docs/ACQUISITION_FEASIBILITY.md`
- `docs/GPIO_PINOUT_AND_ELECTRICAL_SAFETY.md`
- `docs/PI3_PERFORMANCE_TEST_PLAN.md`

These must include verified references, date of investigation, supported/unsupported modes, exact hardware/OS assumptions, safe wiring, pin mapping, measured-versus-theoretical performance, and a realistic MVP feature boundary.

Mark every unverified capability as UNVERIFIED. Do not invent rates, timing accuracy, DMA guarantees, buffer sizes, API calls, or GPIO electrical limits.

# 4. PROJECT ARCHITECTURE

Implement a modular architecture with strict separation of responsibilities.

The application must support different acquisition backends without modifying the analysis engine or GUI.

## 4.1 Recommended project structure

Create the following project:

```text
raspberry_pi_logic_analyzer/
│
├── main.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── application_settings.py
│   ├── hardware_settings.py
│   ├── acquisition_settings.py
│   ├── channel_settings.py
│   └── protocol_settings.py
│
├── hardware/
│   ├── __init__.py
│   ├── hardware_interface.py
│   ├── raspberry_pi_gpio.py
│   ├── raspberry_pi_discovery.py
│   ├── gpio_pin_mapping.py
│   ├── digital_input.py
│   ├── hardware_validation.py
│   ├── hardware_monitor.py
│   └── hardware_exceptions.py
│
├── acquisition/
│   ├── __init__.py
│   ├── acquisition_engine.py
│   ├── acquisition_worker.py
│   ├── sample block_manager.py
│   ├── acquisition_buffer.py
│   ├── circular_buffer.py
│   ├── timestamp_manager.py
│   ├── sample_processor.py
│   ├── acquisition_statistics.py
│   └── acquisition_state.py
│
├── core/
│   ├── __init__.py
│   ├── application_controller.py
│   ├── event_manager.py
│   ├── signal_model.py
│   ├── channel_model.py
│   ├── measurement_model.py
│   ├── session_manager.py
│   └── application_exceptions.py
│
├── triggers/
│   ├── __init__.py
│   ├── trigger_engine.py
│   ├── trigger_conditions.py
│   ├── trigger_sequencer.py
│   ├── pattern_trigger.py
│   ├── edge_trigger.py
│   ├── pulse_width_trigger.py
│   └── trigger_configuration.py
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── application_toolbar.py
│   ├── acquisition_toolbar.py
│   ├── channel_panel.py
│   ├── waveform_view.py
│   ├── time_axis.py
│   ├── trigger_panel.py
│   ├── measurement_panel.py
│   ├── protocol_panel.py
│   ├── search_panel.py
│   ├── diagnostics_panel.py
│   ├── session_panel.py
│   ├── settings_dialog.py
│   ├── hardware_dialog.py
│   └── styles/
│
├── decoders/
│   ├── __init__.py
│   ├── decoder_interface.py
│   ├── decoder_manager.py
│   ├── uart_decoder.py
│   ├── spi_decoder.py
│   ├── i2c_decoder.py
│   ├── can_decoder.py
│   ├── lin_decoder.py
│   ├── manchester_decoder.py
│   ├── onewire_decoder.py
│   └── custom_decoder.py
│
├── analysis/
│   ├── __init__.py
│   ├── edge_detection.py
│   ├── timing_analysis.py
│   ├── frequency_analysis.py
│   ├── pulse_analysis.py
│   ├── jitter_analysis.py
│   ├── statistics.py
│   ├── signal_classification.py
│   ├── correlation_analysis.py
│   └── event_analysis.py
│
├── export/
│   ├── __init__.py
│   ├── csv_exporter.py
│   ├── vcd_exporter.py
│   ├── json_exporter.py
│   ├── binary_exporter.py
│   ├── session_exporter.py
│   ├── protocol_exporter.py
│   └── waveform_exporter.py
│
├── simulation/
│   ├── __init__.py
│   ├── virtual_device.py
│   ├── signal_generator.py
│   ├── protocol_generator.py
│   ├── noise_generator.py
│   └── test_scenarios.py
│
├── diagnostics/
│   ├── __init__.py
│   ├── performance_monitor.py
│   ├── data_integrity.py
│   ├── hardware_diagnostics.py
│   └── diagnostic_report.py
│
├── resources/
│   ├── icons/
│   ├── images/
│   └── themes/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── hardware/
│   ├── performance/
│   └── fixtures/
│
├── scripts/
│   ├── install_windows.ps1
│   ├── install_linux.sh
│   ├── run_application.py
│   ├── run_tests.py
│   └── build_release.py
│
└── docs/
    ├── HARDWARE_CAPABILITIES.md
    ├── ARCHITECTURE.md
    ├── ACQUISITION_ENGINE.md
    ├── TRIGGER_SYSTEM.md
    ├── PROTOCOL_DECODERS.md
    ├── TIMING_ANALYSIS.md
    ├── HARDWARE_SAFETY.md
    ├── TROUBLESHOOTING.md
    ├── TESTING.md
    └── USER_GUIDE.md
```

You may extend this structure when necessary.

Do not unnecessarily consolidate modules.

Each module must have a clear responsibility.

---

# 5. HARDWARE ABSTRACTION LAYER

Create a hardware-independent acquisition interface.

Define an abstract class such as:

`AcquisitionBackend`

It must define a consistent interface for:

- Board and GPIO backend detection.
- GPIO backend initialization.
- GPIO backend shutdown.
- Device configuration.
- Channel configuration.
- Acquisition initialization.
- Acquisition start.
- Acquisition stop.
- Acquisition data retrieval.
- Device status.
- Hardware diagnostics.

Implement at least two backends:

1. `RaspberryPi3GPIOBackend` (real GPIO acquisition using the selected, verified backend/library).
2. `VirtualDeviceBackend`.

The rest of the application must communicate with these backends through the common interface.

Never place Raspberry Pi-specific API calls inside GUI modules, protocol decoders, or measurement algorithms.

The architecture must permit future support for other acquisition devices.

---

# 6. RASPBERRY PI 3 GPIO HARDWARE MANAGEMENT

Implement complete Raspberry Pi 3 GPIO management for the exact supported board revision and OS.

Required functionality:

- Identify the local Raspberry Pi model and SoC revision where reliably available.
- Identify Raspberry Pi OS, kernel, architecture, and Python runtime.
- Check availability/version of the selected GPIO acquisition library and required daemon/service.
- Validate GPIO permissions and required privileges without running the whole GUI as root unnecessarily.
- Configure eight GPIO pins as digital inputs.
- Configure pull-up/pull-down/disabled state only where electrically appropriate and supported.
- Validate pin conflicts and alternate-function ownership.
- Initialize and safely stop the sampling subsystem.
- Detect acquisition service failure and recover safely.
- Report CPU, memory, temperature, throttling, and acquisition status where accessible.
- Support local operation and, if approved, a headless capture service with a remote GUI.
- Provide safe shutdown and resource cleanup.

## 6.1 Default channel mapping

Use the following only as a proposed mapping to validate on the selected board and acquisition method:

| Analyzer channel | BCM GPIO | Physical header pin (40-pin header) |
|---|---:|---:|
| CH0 | GPIO4 | 7 |
| CH1 | GPIO5 | 29 |
| CH2 | GPIO6 | 31 |
| CH3 | GPIO12 | 32 |
| CH4 | GPIO13 | 33 |
| CH5 | GPIO16 | 36 |
| CH6 | GPIO17 | 11 |
| CH7 | GPIO22 | 15 |

Do not treat this mapping as final until it has been checked against the exact Pi 3 revision, HATs, boot configuration, and sampling peripheral. The application must allow users to change assignments and must prevent duplicate or reserved/conflicting pin assignments.

## 6.2 Hardware configuration validation

Before starting acquisition:

- Verify the detected board model is supported.
- Verify the OS/kernel and GPIO library combination is supported.
- Verify all selected GPIO lines exist and are available.
- Verify pin numbering scheme (BCM versus physical) is unambiguous.
- Verify no selected pin is claimed by a conflicting peripheral/HAT.
- Verify electrical configuration and input-only operation.
- Verify selected sample interval/mode is supported.
- Verify memory/buffer requirements are acceptable.
- Verify permissions and daemon/service health.
- Warn that GPIO inputs are 3.3 V only and not 5 V tolerant.

Display meaningful warnings and refuse unsafe or unsupported configurations.

# 7. EIGHT-CHANNEL DIGITAL ACQUISITION ENGINE

This is one of the most critical components of the entire application.

The real backend must use the acquisition method verified in Section 3. Do not use eight independent Python polling loops. Prefer a common GPIO bank snapshot or a single synchronized sampling sample block if the chosen library exposes one. If the backend provides only edge events, represent them as timestamped events and do not fabricate a uniform sample matrix.

The design must support two distinct capture representations where justified:

- Uniform sampled snapshots (for example, compact bit masks for all eight channels at each sample instant).
- Timestamped transition events (per-edge timestamps, channel identity, state, sequence number, and uncertainty).

Do not merge these representations in a way that hides their different timing guarantees. Protocol decoders must declare which representation and minimum timing quality they require. The UI must show the acquisition mode and effective time resolution.

On Raspberry Pi 3, account for Linux scheduling, DMA/peripheral contention, thermal throttling, limited RAM, storage throughput, and CPU consumed by the GUI. A local GUI may reduce acquisition headroom; benchmark local and headless/remote modes separately.

Implement a robust and high-performance acquisition engine.

## 7.1 Acquisition modes

Support:

- Single acquisition.
- Continuous acquisition.
- Finite-duration acquisition.
- Repeated acquisition.
- Triggered acquisition.
- Pre-trigger acquisition.
- Post-trigger acquisition.
- Buffered acquisition.
- Manual acquisition stop.

Pause and resume only when supported by the actual acquisition implementation.

## 7.2 Channel synchronization

All eight channels must be acquired using the most synchronized acquisition mechanism supported by the hardware.

Do not implement eight independent software polling loops.

If the hardware acquisition mechanism provides a shared scan clock, use it.

Represent the acquired channels as a synchronized digital sample matrix or an equivalent compact bit-packed structure.

Document the synchronization characteristics and uncertainty.

## 7.3 Data representation

Internally, use efficient numerical representations.

Evaluate:

- NumPy arrays.
- uint8.
- uint16.
- uint32.
- Bit-packed digital samples.

Select the representation that provides the best combination of:

- Performance.
- Memory efficiency.
- Processing speed.
- Compatibility with waveform visualization.
- Compatibility with protocol decoders.

Each sample must represent the state of the eight channels at a common acquisition instant.

## 7.4 Timestamp system

Implement a consistent timestamp reference.

Support:

- Relative timestamps.
- Absolute session timestamps.
- Sample index.
- Trigger-relative timestamps.

Do not generate timestamps independently for every sample using repeated system-clock calls.

Use the actual acquisition timing information.

For regular sampling, derive timestamps from verified sample timing.

For irregular acquisition, preserve the actual timing information where available.

Never hide timing uncertainty.

## 7.5 Buffer management

Implement:

- Circular buffers.
- Block-based acquisition.
- Configurable buffer sizes.
- Preallocated memory where appropriate.
- Efficient memory reuse.
- Thread-safe access.
- Overflow detection.
- Buffer utilization monitoring.
- Data integrity checks.

Support large captures without unnecessary copying.

## 7.6 Acquisition reliability

Detect:

- Missing data.
- Buffer overflows.
- Sampling interruptions.
- Communication errors.
- Unexpected GPIO backend shutdown.
- Invalid samples.
- Incomplete captures.
- Timing discontinuities.

Never silently discard data.

When an acquisition is incomplete, explicitly mark the session as incomplete and identify the reason.

---

# 8. ADVANCED RING BUFFER AND PRETRIGGER SYSTEM

Implement a professional circular buffer system.

The analyzer must continuously preserve historical samples when continuous acquisition is active.

Required features:

- Configurable buffer duration.
- Configurable memory allocation.
- Configurable pre-trigger percentage.
- Configurable post-trigger percentage.
- Automatic trigger capture.
- Trigger position preservation.
- Buffer wraparound handling.
- Multi-channel synchronization.
- Capture completion detection.
- Memory usage estimation.
- Safe buffer access during simultaneous acquisition and processing.

Example:

Total acquisition duration: 1 second.

Pre-trigger: 25%.

Post-trigger: 75%.

The trigger must be placed at the correct position in the final acquisition.

Allow pre-trigger percentages from 0% to 99%, subject to the acquisition mode.

Provide visual indication of the trigger location.

IMPORTANT:

The application must account for hardware sampling latency, acquisition block latency, and software trigger processing delay.

Do not claim that software-triggered pre-trigger capture is equivalent to a hardware-triggered capture.

Document the actual trigger-position uncertainty.

---

# 9. ADVANCED TRIGGER SYSTEM

Develop a professional trigger engine.

## 9.1 Basic triggers

Implement:

- Rising edge.
- Falling edge.
- Either edge.
- HIGH level.
- LOW level.
- Single-channel trigger.
- Multi-channel trigger.

## 9.2 Pattern triggers

Allow users to define digital patterns across all eight channels.

Support:

- Exact HIGH.
- Exact LOW.
- Don't-care states.
- Bit masks.
- Pattern matching.
- Repeated pattern detection.

Example:

- CH0 = HIGH
- CH1 = LOW
- CH2 = HIGH
- CH3 = Don't Care
- CH4 = Don't Care

## 9.3 Logical conditions

Support:

- AND.
- OR.
- NOT.
- XOR.

Allow combined trigger expressions.

## 9.4 Sequential triggers

Implement a trigger sequencer.

Example:

1. CH0 rising edge.
2. CH1 rising edge within 10 microseconds.
3. CH2 falling edge within 50 microseconds.

Support:

- Configurable sequence steps.
- Time windows.
- Minimum pulse widths.
- Maximum pulse widths.
- Trigger timeout.
- Trigger holdoff.
- Repeated event detection.

## 9.5 Trigger interface

Create a visual trigger configuration panel.

Display the configured trigger logic in a readable format.

Allow saving and loading trigger configurations.

## 9.6 Hardware versus software triggering

Use hardware-assisted triggering only if supported and verified.

Otherwise, implement software triggering.

Explicitly document:

- Trigger latency.
- Trigger uncertainty.
- Pre-trigger limitations.
- Maximum sustainable processing rate.

---

# 10. PROFESSIONAL GRAPHICAL USER INTERFACE

Create a polished desktop application using PyQt6.

The visual design should resemble professional commercial logic analyzer software.

Use a modern, clean, dark-theme interface by default.

Allow switching between dark and light themes.

The interface must be intuitive and suitable for prolonged engineering work.

## 10.1 Main application layout

Include:

### Main toolbar

- New session.
- Open session.
- Save session.
- Save as.
- Initialize GPIO acquisition.
- Stop GPIO acquisition.
- Start acquisition.
- Stop acquisition.
- Single capture.
- Continuous acquisition.
- Export.
- Settings.

### Channel panel

Display eight channels.

For each channel provide:

- Channel identifier.
- Channel name.
- Hardware pin.
- Visibility.
- Enable state.
- Color.
- Signal inversion.
- Trigger indicator.
- Protocol assignment.

Allow channel reordering.

### Waveform panel

Display all eight channels simultaneously.

Each waveform must be visually distinguishable.

Use high-performance rendering.

### Measurement panel

Display live and selected-region measurements.

### Protocol panel

Display decoded protocol transactions.

### Acquisition status panel

Display:

- GPIO backend initialization.
- Sampling rate.
- Acquired samples.
- Capture duration.
- Buffer utilization.
- Trigger state.
- Acquisition status.
- Error indicators.

## 10.2 Waveform visualization

Implement:

- Digital HIGH and LOW states.
- Horizontal zoom.
- Vertical zoom.
- Mouse-wheel zoom.
- Panning.
- Horizontal scrolling.
- Automatic fit.
- Time-axis scaling.
- Grid.
- Channel grouping.
- Channel hiding.
- Channel reordering.
- Signal inversion.
- Trigger marker.
- Event markers.
- Cursor markers.
- Search markers.
- Measurement overlays.

Support large acquisitions efficiently.

Implement intelligent rendering and decimation.

Preserve narrow pulses and transitions during zoomed-out visualization.

Never discard original samples from the underlying acquisition data because of display decimation.

## 10.3 Time navigation

Implement:

- Time cursor A.
- Time cursor B.
- Trigger position navigation.
- First transition.
- Last transition.
- Next event.
- Previous event.
- Time selection.
- Region selection.
- Zoom to selection.
- Zoom to entire capture.

## 10.4 User interface responsiveness

The GUI must remain responsive during:

- Continuous acquisition.
- Large data processing.
- Protocol decoding.
- Data export.
- Measurement calculations.

Use appropriate worker threads and Qt signals/slots.

Never manipulate GUI widgets directly from acquisition threads.

Implement cancellation and clean shutdown mechanisms for long-running operations.

---

# 11. ADVANCED MEASUREMENT AND TIMING ANALYSIS

Develop a complete signal analysis engine.

All algorithms must work independently of the GUI.

## 11.1 Basic measurements

Implement:

- Frequency.
- Period.
- Duty cycle.
- HIGH pulse width.
- LOW pulse width.
- Rising edge count.
- Falling edge count.
- Total transition count.
- Average period.
- Minimum period.
- Maximum period.
- Average HIGH time.
- Average LOW time.

## 11.2 Advanced measurements

Implement:

- Edge-to-edge delay.
- Inter-channel delay.
- Propagation delay.
- Relative phase.
- Pulse width statistics.
- Jitter estimation.
- Clock stability.
- Signal activity.
- Transition density.
- Minimum pulse width.
- Maximum pulse width.
- Standard deviation.
- Mean.
- Median.
- Percentiles.

## 11.3 Advanced timing analysis

Provide:

- Setup time estimation.
- Hold time estimation.
- Clock-to-data delay.
- Data-to-clock delay.
- Clock period variation.
- Rising-edge interval analysis.
- Falling-edge interval analysis.
- Channel correlation.

Do not claim that setup and hold times are verified specifications of the connected circuit. They are measurements or estimates based on the captured signals.

## 11.4 Time cursors

Implement two or more independent cursors.

Calculate:

- Cursor A timestamp.
- Cursor B timestamp.
- Delta time.
- Equivalent frequency.
- Number of samples between cursors.
- Pulse width.
- Period.
- Edge-to-edge delay.

Support snapping cursors to transitions.

## 11.5 Measurement accuracy

Every measurement must consider:

- Sampling interval.
- Acquisition timing uncertainty.
- Edge quantization.
- Missing samples.
- Jitter in the acquisition clock.
- Signal threshold limitations.

Display appropriate accuracy warnings.

Do not imply sub-sample timing precision unless the hardware actually supports it.

---

# 12. DIGITAL EDGE DETECTION

Implement a dedicated edge detection engine.

Support:

- Rising edges.
- Falling edges.
- Both edges.
- Edge counting.
- Edge timestamps.
- Pulse extraction.
- Pulse classification.
- Glitch identification.
- Minimum pulse width filtering.
- Maximum pulse width filtering.

Implement efficient algorithms for large datasets.

Avoid unnecessarily processing every sample repeatedly.

Cache calculated edge positions where appropriate.

Allow recalculation when acquisition data changes.

---

# 13. PROFESSIONAL PROTOCOL DECODERS

Create a reusable protocol decoder architecture.

Every decoder must implement a common interface.

Each decoder must receive:

- Channel data.
- Sampling information.
- Timestamps.
- Decoder configuration.

Each decoder must return structured decoded events.

Every decoded event must contain:

- Start timestamp.
- End timestamp.
- Start sample index.
- End sample index.
- Decoded value.
- Protocol information.
- Error flags.
- Human-readable description.

## 13.1 UART DECODER

Implement:

- Configurable baud rate.
- Automatic baud-rate estimation when possible.
- Data bits.
- Parity.
- Stop bits.
- LSB first.
- MSB first where applicable.
- Idle polarity.
- Start bit detection.
- Stop bit validation.
- Parity checking.
- Framing error detection.
- Break detection.
- ASCII interpretation.
- Hexadecimal interpretation.
- Binary interpretation.
- Packet search.
- Error highlighting.

Support common baud rates and custom baud rates.

## 13.2 SPI DECODER

Implement:

- Clock channel.
- MOSI channel.
- MISO channel.
- Chip select channel.
- Multiple chip selects.
- CPOL.
- CPHA.
- All four SPI modes.
- Configurable word length.
- Bit order.
- Chip select polarity.
- Transaction grouping.
- Data extraction.
- Hexadecimal representation.
- Binary representation.
- Transaction search.

## 13.3 I2C DECODER

Implement:

- SDA selection.
- SCL selection.
- START detection.
- STOP detection.
- Repeated START detection.
- Address decoding.
- 7-bit addressing.
- 10-bit addressing where the complete transaction can be decoded.
- Read/write detection.
- ACK detection.
- NACK detection.
- Data extraction.
- Transaction grouping.
- Address filtering.
- Data filtering.
- Error identification.

## 13.4 CAN DECODER

Implement an optional CAN decoder.

Support, where sampling quality permits:

- CAN frame identification.
- Standard identifiers.
- Extended identifiers.
- Data extraction.
- CRC checking.
- Bit stuffing validation.
- Error frame identification.

IMPORTANT:

A CAN decoder must receive a suitable logic-level signal, normally from a CAN transceiver.

Never connect CAN_H or CAN_L directly to a Raspberry Pi digital input.

Document that the Raspberry Pi 3 does not replace a CAN transceiver or a dedicated CAN interface.

Clearly document the sampling-rate requirements.

## 13.5 LIN DECODER

Implement an optional LIN decoder.

Support:

- Break detection.
- Sync byte.
- Identifier.
- Data bytes.
- Checksum validation.
- Frame identification.

## 13.6 ADDITIONAL DECODERS

Design the decoder architecture to permit:

- Manchester.
- 1-Wire.
- Custom protocols.
- PWM-based protocols.
- Parallel bus decoding.

Implement these only when technically feasible.

## 13.7 Protocol visualization

Display decoded packets directly over the waveform.

Allow users to:

- Click a decoded packet.
- Jump to its waveform position.
- Inspect individual bits.
- Inspect bytes.
- Search decoded values.
- Filter packets.
- Export protocol data.

All protocol decoders must operate independently of the GUI.

---

# 14. PROTOCOL ANALYSIS AND AUTOMATIC DETECTION

Implement an optional protocol analysis assistant.

Analyze captured signals and attempt to identify:

- Clock signals.
- UART-like signals.
- SPI-like activity.
- I2C-like activity.
- PWM.
- Periodic signals.
- Pulse trains.
- Manchester-like patterns.

Provide:

- Candidate protocol.
- Estimated parameters.
- Confidence score.
- Evidence supporting the classification.
- Possible alternative interpretations.

Never present automatic identification as guaranteed.

Require user confirmation before activating a proposed decoder configuration.

---

# 15. ADVANCED WAVEFORM SEARCH

Implement a dedicated search engine.

Support:

- Rising-edge search.
- Falling-edge search.
- Either-edge search.
- HIGH-level search.
- LOW-level search.
- Pulse-width search.
- Pattern search.
- Digital sequence search.
- Protocol packet search.
- Data-byte search.
- Address search.
- Error packet search.

Allow users to:

- Find next.
- Find previous.
- Find all occurrences.
- Filter by channel.
- Filter by time range.
- Navigate between events.

Search results must be synchronized with the waveform viewer.

---

# 16. DATA EXPORT AND IMPORT

Implement a comprehensive export system.

## 16.1 Supported export formats

CSV:

- Timestamp.
- Sample index.
- Eight digital channel values.
- Optional decoded protocol information.

VCD:

- Standard Value Change Dump format.
- Channel declarations.
- Time resolution.
- Initial states.
- Digital transitions.

JSON:

- Structured acquisition information.
- Metadata.
- Channel configuration.
- Trigger information.
- Measurement results.

Binary:

- Compact storage.
- Documented format.
- Version identification.
- Efficient reading and writing.

Protocol export:

- CSV.
- JSON.
- Human-readable reports.

Waveform images:

- PNG.
- SVG where appropriate.

## 16.2 Import functionality

Allow loading:

- Native application sessions.
- CSV captures.
- VCD files.
- Supported binary captures.

Imported data must be validated before being accepted.

Clearly identify missing timing information or unknown metadata.

## 16.3 Native session format

Create a versioned session format.

Each session must preserve:

- Raw acquired data.
- Sampling configuration.
- Actual sampling information.
- Channel assignments.
- Channel names.
- Channel colors.
- Trigger configuration.
- Trigger position.
- Acquisition timestamps.
- Hardware identification.
- Connection type.
- Decoder settings.
- Decoded protocol events.
- Measurement results.
- Acquisition diagnostics.
- Software version.

Use a format that supports large acquisitions efficiently.

Consider chunked storage or an appropriate container format instead of placing millions of samples inside a single JSON file.

Support session validation and backward compatibility.

---

# 17. VIRTUAL RASPBERRY PI GPIO DEVICE

Implement a fully functional virtual acquisition backend.

The application must be usable without physical hardware.

The virtual device must implement the same application-facing acquisition contract as the real Raspberry Pi 3 GPIO backend, while clearly distinguishing simulated timing from physical GPIO timing.

Generate configurable signals:

- Square waves.
- Clock signals.
- PWM.
- Pulse trains.
- Single pulses.
- Random digital sequences.
- Asynchronous serial data.
- UART.
- SPI.
- I2C.
- CAN.
- LIN.
- Custom digital patterns.

Allow configuration of:

- Frequency.
- Period.
- Duty cycle.
- Pulse width.
- Phase.
- Channel relationships.
- Noise.
- Timing offsets.
- Protocol parameters.
- Signal start time.

Generate known test sequences for protocol validation.

The simulator must support all eight channels simultaneously.

Provide predefined test scenarios.

Include a simulation mode indicator in the GUI.

---

# 18. ACQUISITION PERFORMANCE AND DIAGNOSTICS

Implement a dedicated diagnostics subsystem.

Continuously monitor:

- Requested sample rate.
- Configured sample rate.
- Effective sample rate.
- Acquired samples.
- Missing samples.
- Buffer utilization.
- Memory usage.
- CPU usage.
- Acquisition latency.
- Communication errors.
- Device status.
- Sampling interruptions.
- Processing performance.
- GUI update performance.

Display these measurements in a diagnostics panel.

## 18.1 Performance benchmarks

Create benchmarking tools.

Measure:

- Maximum sustained acquisition rate.
- Acquisition stability.
- Buffer throughput.
- Data processing throughput.
- Waveform rendering performance.
- Memory consumption.
- CPU consumption.

Benchmark both simulation and the physical Raspberry Pi 3. Record exact board revision, OS/kernel, GPIO library version, sampling configuration, and thermal state.

Clearly distinguish simulation results from hardware results.

## 18.2 Diagnostic reports

Allow exporting a diagnostic report containing:

- Raspberry Pi model and revision.
- Firmware version.
- Driver version.
- Operating system.
- Python version.
- Application version.
- Acquisition topology (standalone or headless/network).
- Acquisition settings.
- Performance statistics.
- Errors.
- Warnings.
- Hardware limitations.

---

# 19. SIGNAL INTEGRITY AND DATA VALIDATION

Implement data integrity verification.

Check:

- Sample count consistency.
- Channel alignment.
- Buffer continuity.
- Timestamp continuity.
- Acquisition block continuity.
- Unexpected state transitions.
- Missing data.
- Invalid samples.
- Data corruption.

Do not confuse a stable digital signal with missing acquisition data.

Distinguish between:

- A signal that remained unchanged.
- A missing sample.
- An acquisition interruption.
- An invalid timestamp.
- An actual buffer overflow.

Where the hardware cannot independently prove that no sample was lost, explicitly state this limitation.

---

# 20. GPIO ELECTRICAL SAFETY AND SIGNAL CONDITIONING

Create a complete safety guide specific to the Raspberry Pi 3 GPIO interface.

Explain and verify from official documentation:

- 3.3 V GPIO logic domain.
- GPIO inputs are NOT 5 V tolerant.
- Input-high/input-low thresholds and their specified conditions.
- Absolute maximum ratings and current/injection constraints.
- Common ground requirements.
- Pull-up and pull-down resistors.
- Input protection and ESD precautions.
- Series resistors, buffers, dividers, and logic-level translators.
- Signal edge integrity, ringing, overshoot, undershoot, cable length, and grounding.
- Safe connection of 3.3 V CMOS signals.
- Safe conversion of 5 V logic signals using a suitable level-shifting/protection circuit.
- Why differential buses such as CAN and RS-485 require suitable transceivers/receivers.
- Why negative-voltage, automotive, industrial, or unknown signals must not be connected directly.

Never state that a GPIO pin tolerates 5 V. Never connect a 5 V signal directly to a GPIO. Do not present a simple resistor divider as universally suitable for high-speed signals. Specify the bandwidth, propagation delay, threshold, and edge effects of any recommended conditioning circuit.

Provide a wiring table identifying both BCM GPIO number and physical header pin number. Include at least one shared ground connection and explain that all external signals must remain within the verified electrical limits. Recommend current-limiting/protection and level shifting when required.

The hardware safety document must be reviewed before any physical test. If input voltage or source characteristics are unknown, do not connect the signal until measured or conditioned safely.

# 21. CONFIGURATION AND USER PREFERENCES

Implement persistent settings.

Save:

- Last used device.
- Acquisition topology (standalone or headless/network).
- Device identifier.
- Channel mapping.
- Channel names.
- Channel colors.
- Channel visibility.
- Acquisition configuration.
- Trigger configuration.
- Decoder configuration.
- GUI preferences.
- Window layout.
- Theme.
- Recent sessions.

Provide configuration profiles.

Allow users to save and restore complete analyzer configurations.

Validate configuration files when loading them.

Provide default configuration recovery.

---

# 22. LOGGING AND ERROR MANAGEMENT

Implement a professional logging system.

Support:

- DEBUG.
- INFO.
- WARNING.
- ERROR.
- CRITICAL.

Log:

- Application startup.
- Board and GPIO backend detection.
- GPIO backend initialization.
- Hardware configuration.
- Acquisition start.
- Acquisition stop.
- Trigger events.
- Buffer errors.
- Protocol decoder errors.
- Data export.
- Session loading.
- Unexpected exceptions.

Implement rotating log files.

Provide a GUI log viewer.

Never expose raw exceptions to ordinary users without a useful explanation.

Preserve technical diagnostic information for developers.

---

# 23. THREADING AND CONCURRENCY

Design the application to prevent blocking operations.

Use suitable worker threads and asynchronous processing where appropriate.

Recommended separation:

1. Hardware communication worker.
2. Acquisition worker.
3. Buffer management.
4. Data processing worker.
5. Protocol decoding worker.
6. Measurement worker.
7. GUI rendering.

Use thread-safe communication mechanisms.

Use Qt signals and slots for GUI updates.

Avoid unnecessary locks.

Avoid deadlocks.

Implement controlled shutdown.

Ensure the Raspberry Pi GPIO backend is safely disconnected when the application closes.

---

# 24. PERFORMANCE OPTIMIZATION

The software must efficiently handle large acquisitions.

Implement:

- Preallocated buffers.
- Block processing.
- Efficient NumPy operations.
- Bitwise operations.
- Cached edge detection.
- Cached measurements.
- Intelligent waveform decimation.
- Memory-efficient data storage.
- Background decoding.
- Background export.

Avoid unnecessary Python loops over individual samples when vectorized operations are suitable.

Use compiled acceleration only when justified by profiling.

Do not optimize blindly.

Provide performance benchmarks before and after significant optimizations.

---

# 25. APPLICATION USER EXPERIENCE

Implement a professional engineering workflow.

The application must support the following sequence:

1. Start application.
2. Select hardware or simulation mode.
3. Initialize the Raspberry Pi 3 GPIO backend.
4. Configure eight channels.
5. Configure acquisition.
6. Configure trigger.
7. Start acquisition.
8. Capture digital signals.
9. Navigate waveforms.
10. Perform measurements.
11. Decode protocols.
12. Search events.
13. Save session.
14. Export data.
15. Reopen previous sessions.

Provide contextual help.

Use meaningful error messages.

Include tooltips for technical controls.

Provide keyboard shortcuts for frequent operations.

Implement confirmation dialogs for destructive operations.

---

# 26. TESTING STRATEGY

Implement a complete automated testing system using Pytest.

## 26.1 Unit tests

Test independently:

- Hardware interface.
- Channel configuration.
- Acquisition engine.
- Buffer management.
- Timestamp generation.
- Trigger detection.
- Trigger sequences.
- Edge detection.
- Timing measurements.
- Jitter calculations.
- UART decoding.
- SPI decoding.
- I2C decoding.
- CAN decoding.
- Data export.
- Data import.
- Session management.
- Configuration management.

## 26.2 Integration tests

Test:

- Virtual device to acquisition engine.
- Acquisition engine to waveform viewer.
- Acquisition engine to trigger engine.
- Acquisition engine to protocol decoders.
- Measurement engine to waveform data.
- Session save and reload.
- Export and import.
- GUI responsiveness.

## 26.3 Hardware tests

Create optional tests that require a physical Raspberry Pi 3 board and safe test signals.

Test:

- Board and GPIO backend detection.
- Connection.
- Channel configuration.
- Eight-channel acquisition.
- Acquisition stability.
- Effective sampling rate.
- Buffer operation.
- Disconnection recovery.

Hardware tests must be clearly marked.

Never claim that they have passed without physical execution.

## 26.4 Performance tests

Test:

- Large acquisition buffers.
- Long acquisition sessions.
- Sustained acquisition.
- High-density transitions.
- Large waveform visualization.
- Protocol decoding performance.
- Export performance.

## 26.5 Data integrity tests

Use known digital patterns with predetermined expected results.

Verify exact sample counts, channel values, timestamps, and decoded protocol data where the test backend permits it.

---

# 27. ACCEPTANCE TESTS

The project must pass the following acceptance tests.

| ID | Requirement |
|---|---|
| AT01 | Application starts without hardware. |
| AT02 | Simulation mode operates correctly. |
| AT03 | Eight channels can be configured. |
| AT04 | Eight channels are acquired through the verified Raspberry Pi 3 GPIO sampling/event mechanism. |
| AT05 | Channels use a common time reference. |
| AT06 | Rising and falling edges are detected correctly. |
| AT07 | Circular buffer operates correctly. |
| AT08 | Pre-trigger and post-trigger work correctly. |
| AT09 | Basic triggers work correctly. |
| AT10 | Sequential triggers work correctly. |
| AT11 | UART decoding works with known test vectors. |
| AT12 | SPI decoding works with known test vectors. |
| AT13 | I2C decoding works with known test vectors. |
| AT14 | Measurements produce expected results. |
| AT15 | Large acquisitions remain navigable. |
| AT16 | CSV export works. |
| AT17 | VCD export works. |
| AT18 | Native sessions can be saved and reopened. |
| AT19 | GUI remains responsive during acquisition. |
| AT20 | Missing-data conditions are reported. |
| AT21 | GPIO backend/service failure and, in remote mode, network disconnection are handled safely. |
| AT22 | Application logs errors correctly. |
| AT23 | Configuration profiles can be saved and restored. |
| AT24 | Documentation matches the actual implementation. |
| AT25 | Windows installation instructions work. |
| AT26 | Linux installation instructions work. |

For every test, record:

- Test identifier.
- Description.
- Procedure.
- Expected result.
- Actual result.
- Pass/fail status.
- Execution environment.
- Whether physical hardware was used.

---

# 28. RASPBERRY PI OS, LINUX, AND HOST-COMPUTER SUPPORT

The primary hardware target is Raspberry Pi 3 running a verified Raspberry Pi OS release. Support the exact 32-bit or 64-bit OS variant selected during Stage 0/1; do not assume all current packages support both.

Investigate two deployment modes:

A. **Standalone mode:** acquisition engine and PyQt6 GUI run locally on the Raspberry Pi 3. Verify installation, memory use, responsiveness, thermal behavior, and sustained acquisition with the GUI active.

B. **Headless acquisition mode:** a lightweight acquisition service runs on the Pi; a separate Windows/Linux computer runs the full PyQt6 GUI and analysis interface over a documented network protocol. Protect the service, authenticate connections where appropriate, handle disconnects, and preserve acquisition data locally if the network drops.

Recommend a default only after comparing measured feasibility. Do not assume a Windows PC can access the Pi GPIO directly; GPIO acquisition occurs on the Pi. The Windows/Linux host is optional and must communicate with the Pi service.

Provide installation and operation instructions for:

- Raspberry Pi OS image and first boot.
- OS updates and kernel identification.
- Python and virtual environment.
- GPIO acquisition library/daemon installation and configuration.
- Required permissions and service setup.
- PyQt6 and PyQtGraph compatibility if using standalone mode.
- Remote service startup and network configuration if using headless mode.
- Windows/Linux GUI client setup if remote mode is supported.
- Troubleshooting and safe shutdown.

Do not retain instructions or dependencies for the previous data-acquisition hardware. Verify every command against the selected OS release.

# 29. APPLICATION PACKAGING AND DISTRIBUTION

Prepare the project for distribution.

Generate:

- Windows executable using PyInstaller.
- Linux executable or distribution package where practical.
- Complete source distribution.
- requirements.txt.
- Installation scripts.
- Version information.
- Release notes.

The application must support running from source.

Include all required resources.

Test the packaged application.

Document any external GPIO acquisition library or GPIO interface library installation prerequisites.

---

# 30. COMPLETE README.md REQUIREMENTS

Generate a comprehensive README.md written entirely in English.

It must include:

1. Project overview.
2. Project objectives.
3. Main features.
4. Hardware requirements.
5. Electrical requirements.
6. Hardware capabilities.
7. Verified acquisition limitations.
8. Software requirements.
9. Installation instructions.
10. Windows installation.
11. Linux installation.
12. GPIO library and service installation.
13. GPIO interface library installation.
14. Python dependency installation.
15. Project architecture.
16. Complete directory tree.
17. Explanation of every module.
18. Explanation of every major class.
19. Main functions and responsibilities.
20. Hardware connection instructions.
21. Channel configuration.
22. Acquisition configuration.
23. Sampling rate limitations.
24. Trigger configuration.
25. Pre-trigger and post-trigger operation.
26. Waveform navigation.
27. Measurement tools.
28. UART decoding.
29. SPI decoding.
30. I2C decoding.
31. Additional protocol decoders.
32. Data export.
33. Data import.
34. Session management.
35. Simulation mode.
36. Diagnostics.
37. Logging.
38. Running tests.
39. Performance benchmarks.
40. Troubleshooting.
41. Known limitations.
42. Hardware safety.
43. Future development.
44. Version history.
45. License.

Explain every module's:

- Purpose.
- Main classes.
- Main functions.
- Dependencies.
- Inputs.
- Outputs.
- Relationship with other modules.

The README must describe the actual implementation, not an intended future implementation.

---

# 31. ADDITIONAL TECHNICAL DOCUMENTATION

Generate the following documents:

## ARCHITECTURE.md

Explain:

- Application architecture.
- Hardware abstraction.
- Module relationships.
- Data flow.
- Threading model.
- Communication between components.

Include architecture diagrams using Mermaid.

## HARDWARE_CAPABILITIES.md

Explain all verified Raspberry Pi 3 board, GPIO, OS, sampling-library capabilities and limitations.

## ACQUISITION_ENGINE.md

Explain:

- Acquisition mechanism.
- Sampling.
- Timestamps.
- Buffer management.
- Data integrity.
- Synchronization.
- Performance limitations.

## TRIGGER_SYSTEM.md

Explain all trigger modes and their timing limitations.

## PROTOCOL_DECODERS.md

Explain each decoder and its supported parameters.

## TIMING_ANALYSIS.md

Explain the measurement algorithms and accuracy limitations.

## HARDWARE_SAFETY.md

Explain safe electrical connections.

## TESTING.md

Explain automated tests and hardware validation.

## USER_GUIDE.md

Provide a practical operating guide.

## TROUBLESHOOTING.md

Provide solutions to common installation, hardware, and software problems.

---

# 32. DEVELOPMENT WORKFLOW

Do not generate the entire application in one unverified code-generation operation.

Follow these phases in order.

## PHASE 1 — TECHNICAL RESEARCH

Investigate the exact Raspberry Pi 3 model, GPIO electrical constraints, GPIO sampling libraries, DMA/peripheral sampling options, Linux GPIO events, and verify the eight-channel acquisition feasibility.

Deliver:

- Hardware capabilities document.
- Acquisition feasibility report.
- Technical limitations.
- Initial performance estimates.

## PHASE 2 — SOFTWARE ARCHITECTURE

Design:

- Directory structure.
- Hardware abstraction.
- Data models.
- Threading architecture.
- Acquisition flow.
- Buffer architecture.
- GUI architecture.

Deliver architecture documentation.

## PHASE 3 — HARDWARE BACKEND

Implement:

- Board and GPIO backend detection.
- GPIO backend initialization.
- Configuration.
- Digital input acquisition.
- Error handling.
- Diagnostics.

## PHASE 4 — VIRTUAL DEVICE

Implement the complete simulator.

Validate the architecture without physical hardware.

## PHASE 5 — ACQUISITION ENGINE

Implement:

- Acquisition workers.
- Data buffers.
- Circular buffers.
- Timestamps.
- Data integrity.
- Performance monitoring.

## PHASE 6 — TRIGGER SYSTEM

Implement basic, advanced, and sequential triggers.

## PHASE 7 — GRAPHICAL INTERFACE

Implement the complete application GUI.

## PHASE 8 — SIGNAL ANALYSIS

Implement measurements, edge detection, timing analysis, and statistics.

## PHASE 9 — PROTOCOL DECODERS

Implement UART, SPI, I2C, and technically feasible additional decoders.

## PHASE 10 — DATA MANAGEMENT

Implement:

- Session saving.
- Session loading.
- CSV.
- VCD.
- JSON.
- Binary export.
- Protocol export.

## PHASE 11 — ADVANCED FEATURES

Implement search, signal classification, diagnostics, and performance tools.

## PHASE 12 — TESTING

Run all available tests.

Fix all failures.

## PHASE 13 — INTEGRATION

Verify that all modules work together.

## PHASE 14 — DOCUMENTATION

Generate all required documentation.

## PHASE 15 — PACKAGING

Generate the complete ZIP archive and distribution packages.

---

# 33. STRICT CODE QUALITY REQUIREMENTS

All source code must comply with professional development standards.

Mandatory requirements:

- PEP 8.
- Type hints.
- Meaningful identifiers.
- Comprehensive docstrings.
- Modular functions.
- Small, focused classes.
- Explicit dependencies.
- Robust exception handling.
- No unnecessary global variables.
- No duplicated code.
- No hidden hardware assumptions.
- No blocking GUI operations.
- No unnecessary memory copying.
- No silent error suppression.
- No unexplained magic numbers.
- No circular imports.
- No unnecessary dependencies.

Use static analysis and formatting tools where appropriate:

- Ruff.
- Mypy.
- Pytest.

Create suitable configuration for these tools.

Do not leave:

- TODO placeholders.
- Empty functions.
- Pseudocode.
- Fake hardware interfaces.
- Unimplemented menu options.
- Buttons without functionality.
- Dummy measurement results.
- Simulated results presented as real measurements.

If a feature cannot be implemented, explicitly mark it as unsupported rather than providing a misleading placeholder.

---

# 34. CRITICAL RULES FOR AI CODE GENERATION

These instructions are mandatory.

1. Never invent Raspberry Pi API functions.
2. Never invent register names.
3. Never assume unsupported hardware capabilities.
4. Never advertise unverified sampling rates.
5. Never silently discard samples.
6. Never independently poll eight channels and claim hardware synchronization.
7. Never generate timestamps that imply greater precision than the acquisition mechanism provides.
8. Never block the GUI.
9. Never mix hardware-specific code with protocol decoders.
10. Never confuse simulation results with real hardware measurements.
11. Never claim tests passed without executing them.
12. Never claim physical hardware validation without physical hardware.
13. Never leave incomplete source files.
14. Never generate a superficial README.
15. Never omit dependencies.
16. Never ignore acquisition errors.
17. Never silently substitute an unsupported acquisition method.
18. Never assume that every commercial analyzer feature can be reproduced using the Raspberry Pi 3.
19. Never sacrifice data integrity for graphical rendering performance.
20. Never modify working modules unnecessarily when implementing new features.

When a requested feature cannot be implemented with the available hardware, explain the limitation and propose an alternative.

---

# 35. FINAL DELIVERABLES

The final project must include:

1. Complete Python source code.
2. Complete modular directory structure.
3. Professional PyQt6 GUI.
4. Eight-channel waveform viewer.
5. Raspberry Pi 3 hardware backend.
6. Virtual acquisition backend.
7. Digital acquisition engine.
8. Circular buffer system.
9. Pre-trigger and post-trigger.
10. Advanced trigger system.
11. Time cursors.
12. Timing measurements.
13. Edge detection.
14. UART decoder.
15. SPI decoder.
16. I2C decoder.
17. Additional feasible protocol decoders.
18. Waveform search.
19. Data export.
20. Data import.
21. Session management.
22. Acquisition diagnostics.
23. Performance monitoring.
24. Automated tests.
25. Windows installation scripts.
26. Linux installation scripts.
27. requirements.txt.
28. pyproject.toml.
29. README.md.
30. Complete technical documentation.
31. Windows executable where possible.
32. Linux distribution where practical.
33. Complete ZIP archive.

The ZIP archive must contain the entire project.

The ZIP archive must not contain unnecessary temporary files, Python cache files, virtual environments, or large development artifacts.

---

# 36. FINAL VALIDATION AND DELIVERY REPORT

Before delivery, perform a complete project review.

Verify:

- All Python files compile.
- All modules import successfully.
- All required dependencies are documented.
- All automated tests pass.
- Simulation mode starts correctly.
- GUI opens correctly.
- Eight channels are displayed.
- Acquisition works in simulation.
- Trigger system works in simulation.
- Decoders work with known test vectors.
- Measurements produce expected results.
- Export and import work.
- Session saving and loading work.
- Error handling works.
- Documentation matches the code.
- Packaging works.

Create:

`docs/FINAL_VALIDATION_REPORT.md`

This report must contain:

- Completed features.
- Implemented modules.
- Test results.
- Failed tests.
- Known limitations.
- Hardware validation status.
- Performance measurements.
- Installation verification.
- Outstanding issues.

Clearly separate:

A. Features fully implemented and software-tested.

B. Features tested using simulated hardware.

C. Features tested using physical Raspberry Pi 3 GPIO hardware.

D. Features requiring additional hardware validation.

Never mark an untested feature as completed.

---

# 37. EXECUTION AND PROJECT MANAGEMENT INSTRUCTIONS

You must act as an autonomous software development agent.

Do not stop after generating the architecture or a few example files.

Continue implementing the complete project.

After each phase:

1. Save all generated files.
2. Run relevant tests.
3. Review errors.
4. Correct problems.
5. Verify module compatibility.
6. Update documentation.
7. Preserve the working project state.

If you encounter a limitation:

- Investigate it.
- Document it.
- Implement the best valid alternative.
- Continue with the remaining development.

Do not repeatedly ask the user for permission to implement ordinary engineering decisions.

Use sensible engineering defaults.

Ask questions only when a decision genuinely requires missing hardware or user-specific information.

If execution limits prevent completing everything in one session, preserve all files and progress, generate a detailed progress report, and continue from the last verified phase in subsequent sessions.

Do not replace working code with incomplete rewrites.

Maintain consistent naming, architecture, and interfaces across all development phases.

---

# 38. FINAL PROJECT OBJECTIVE

The final goal is to deliver a professional, reliable, extensible, eight-channel digital logic analyzer using the Raspberry Pi 3 as its GPIO acquisition platform.

The software must provide the maximum functionality technically achievable with the hardware.

It must combine:

- Reliable digital acquisition.
- Accurate timing.
- Advanced triggering.
- Professional waveform visualization.
- Protocol decoding.
- Timing analysis.
- Measurement tools.
- Data management.
- Diagnostics.
- Hardware abstraction.
- Simulation.
- Automated testing.
- Complete documentation.

The result must be a genuine engineering application, not a proof of concept. However, the first physical milestone must be a deliberately small, measurable GPIO acquisition proof-of-concept before the full application is built.

Prioritize technical correctness, reliability, data integrity, usability, and maintainability.

BEGIN BY COMPLETING PHASE 1: RASPBERRY PI 3 GPIO, ELECTRICAL SAFETY, AND ACQUISITION FEASIBILITY INVESTIGATION.

DO NOT WRITE THE ACQUISITION ENGINE UNTIL GPIO ELECTRICAL SAFETY, THE ACQUISITION METHOD, AND REALISTIC PERFORMANCE LIMITS HAVE BEEN VERIFIED.

Once the investigation is complete, proceed through all development phases until the complete project has been implemented, tested, documented, and packaged.

FINAL OUTPUT:

Provide the complete project as a downloadable ZIP archive, together with a concise development report and clear instructions for installation and operation.


---

# 39. RASPBERRY PI 3-SPECIFIC NON-NEGOTIABLE LIMITATIONS

1. The Raspberry Pi 3 is not an FPGA or dedicated logic analyzer. Do not claim equivalent timing determinism.
2. GPIO inputs are 3.3 V and not 5 V tolerant. Unsafe voltage configurations must be rejected.
3. Eight channels must be acquired from a common sampling mechanism where possible; never claim synchronization from independent Python polling loops.
4. A GPIO edge callback is not automatically a complete waveform recorder. Callback delivery latency and event buffering must be distinguished from the timestamp of the physical edge.
5. A library's nominal sample interval is not a guaranteed sustained application-level sample rate.
6. Any advertised sample rate, minimum pulse width, capture duration, or timing precision must be backed by measurements on the exact Pi 3 revision and OS/kernel combination.
7. If the selected method cannot reliably support a protocol's baud/clock rate, disable or warn for that decoder rather than returning plausible but incorrect data.
8. The software must clearly identify whether capture data are uniformly sampled or edge-event based. Never synthesize missing sample points without marking them as reconstructed.
9. Local GUI rendering, networking, disk writes, thermal throttling, and background processes can reduce acquisition headroom. Benchmark the complete operating mode.
10. Any optional external front-end (level shifter, buffer, comparator, FPGA, CPLD, RP2040, or dedicated logic analyzer IC) changes the hardware scope and requires explicit user approval before implementation.
11. The first physical deliverable is a small GPIO acquisition proof-of-concept and performance report, not the full GUI.
12. The first response to this prompt must still be the complete Claude Free workload/token assessment. It must not generate application source code.
