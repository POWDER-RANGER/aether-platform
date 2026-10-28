# Æther / PR-REX external research notes

**Retrieved:** 2026-10-28  
**Purpose:** Source map and conservative design implications for the capture, controller, model, accessibility and evaluation layers. This is not a performance validation of Æther on the owner's hardware.

## Capture: DXcam and Windows Graphics Capture

**Observed upstream source:** [ra1nty/DXcam](https://github.com/ra1nty/DXcam) (retrieved 2026-10-28).

The upstream repository lists a 0.3.0 release and a latest main-branch commit dated 2026-03-18 in the retrieved repository view. Its current README describes two selectable backends: DXGI Desktop Duplication (default) and Windows Graphics Capture (WinRT). It provides examples using `dxcam.create(backend="dxgi")` and `dxcam.create(backend="winrt")`. The README suggests DXGI as the general default and WinRT when cursor rendering or machine-specific behavior calls for it.

The upstream README also reports a benchmark (239.19 average FPS) on a Ryzen 5900X / RTX 3090 display setup. That is upstream's own test, not a comparable benchmark for the Æther workstation and not evidence of capture latency on an RTX 4060 laptop.

**Implementation note:** the present base implementation is `src/aether/capture/screen.py`; PR #5 proposes a threaded capture source. Before adopting new APIs, inspect the installed package version and its own current API. Compare DXGI and WinRT on the actual target machine, with actual selected display/window and focus conditions. Continue labelling all workstation-specific capture timing and reliability UNVERIFIED until hardware runs are documented.

**DXcam status/forks:** the retrieved upstream is actively maintained in 2026. This search result did not establish a complete, reliable census of forks; no fork is recommended on this evidence. Avoid describing DXcam as abandoned.

**Windows Graphics Capture:** Microsoft's API documentation is the platform reference: [Screen capture](https://learn.microsoft.com/windows/uwp/audio-video-camera/screen-capture). DXcam's WinRT backend is a possible Python integration route; direct WinRT integration is a separate implementation choice and should not be inferred to exist in this repository.

## Virtual controller and physical-controller isolation

The current base includes a vgamepad-backed virtual output adapter in `src/aether/control/adapters.py`; the existing verification record describes ViGEmBus-backed virtual X360 testing. A driver/library name in code does not establish that a presently maintained and appropriately signed driver distribution is available, installed, or safe on the target Windows build.

Research targets for further verification:
- [Nefarius ViGEmBus repository](https://github.com/nefarius/ViGEmBus)
- [Nefarius HidHide repository](https://github.com/nefarius/HidHide)
- [Nefarius project documentation](https://docs.nefarius.at/)
- [Microsoft driver signing policy](https://learn.microsoft.com/windows-hardware/drivers/install/kernel-mode-code-signing-requirements--windows-vista-and-later-)

**Evidence limitation:** the initial Firecrawl source batch did not complete a current official-source verification of successor driver status, HidHide maintenance, signing distribution channel, or device-conflict matrix. Therefore this note does not declare ViGEmBus replaced, recommend a successor, or recommend controller hiding. Those remain UNVERIFIED and require official release/documentation checks plus owner-hardware testing.

**Operational cautions to test before recommending HidHide or any equivalent:** identify the exact physical device instance; identify which applications must continue to see it; test reconnect, sleep/resume, device re-enumeration, virtual-device enumeration, and clean disable/uninstall recovery. Device hiding can change which application sees which HID interface; it is not a neutral “passthrough” switch. Do not change owner device visibility or install drivers as part of this documentation pass.

## NitroGen reflex backend and model constraints

The active repository references `src/prrex/backends/nitrogen.py`; its verification records label the backend UNVERIFIED on the active platform. PR #5 describes a nominal 16-action chunk but also lists request-schema and settings-path alignment as unresolved.

The brief supplies the governing licensing constraint: NitroGen is research-only; its weights and code must not be copied into this repository. Link-only reference is appropriate:
- [NVIDIA NitroGen research](https://research.nvidia.com/labs/gamegan/nitrogen/)
- [NVIDIA NitroGen GitHub](https://github.com/NVIDIA NitroGen)

**Do not infer 8 GB VRAM fit from parameter count or a model card.** Co-residency depends on weight format, precision/quantization, context, image preprocessing, runtime allocations, GPU display usage, and the selected supervisor. No RTX 4060 memory/latency test was run in this task. Chunk length 16 is a design parameter in the owner brief and draft, not proof of 16 successful actions per inference or sustained 120 Hz control.

## Local VLM / OCR

The open draft names `qwen2.5vl:3b` for a possible supervisor and OCR reader settings, but its own note labels the model choice and ROI definitions as placeholders. This base tree contains no perception/OCR/VLM implementation.

Potential primary references to inspect before choosing a model or OCR stack:
- [Qwen2.5-VL model family](https://huggingface.co/Qwen)
- [PaddleOCR project and documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [Tesseract OCR documentation](https://tesseract-ocr.github.io/)
- [Ollama model library](https://ollama.com/library)

This retrieval pass did not establish directly comparable published end-to-end latency figures for a specific OCR/VLM configuration on an 8 GB GPU. Do not insert latency numbers or state that a named model fits 8 GB in the absence of a source-matched configuration and target-hardware test. Required measurements include cold start, warm median/p95, image dimensions, batch size, precision/quantization, peak VRAM, and concurrent reflex load. The slow supervisory process must not block the reflex/output path.

## Pixel-based game agents and evaluation

Sources identified:
- [BALROG: Benchmarking Agentic LLM and VLM Reasoning On Games (OpenReview)](https://openreview.net/forum?id=fp6t3F669F) (retrieved 2026-10-28). The paper frames game tasks as long-horizon interactive evaluation and reports that visual inputs can reduce performance for several tested models; this supports measuring visual grounding rather than assuming VLM competence.
- [AgentQuest (OpenReview search source)](https://openreview.net/) (retrieved 2026-10-28). The search result surfaced benchmark discussion around consistent prompting, multiple environments, and fine-grained progression metrics. The exact paper record and final publication metadata need a targeted follow-up before citation as a specific study.
- [NVIDIA NitroGen research](https://research.nvidia.com/labs/gamegan/nitrogen/) (retrieved 2026-10-28), for the generalist gameplay-policy research direction; do not treat research demonstrations as PR-REX performance evidence.

**Evaluation implications:** define scenario ground truth separately from model interpretation; distinguish perception correctness from objective progression and action execution; record wall-clock and monotonic timing; include no-op/neutral outcomes, player override frequency, recoveries, failed attempts and confidence calibration; use repeated trials and disclose variance. Do not use a single successful demonstration as an evaluation result.

## Shared autonomy and control arbitration

Candidate primary-source literature and accessible research starting points:
- [Shared autonomy: A survey](https://arxiv.org/abs/1804.XXXX) — citation is intentionally not asserted: the search result did not verify a stable exact paper identifier during this pass.
- [Shared control for assistive robotics: literature search](https://scholar.google.com/scholar?q=shared+control+assistive+robotics+human+authority) (retrieved 2026-10-28).
- [Human-robot shared control and arbitration literature search](https://scholar.google.com/scholar?q=shared+autonomy+control+arbitration+human+authority) (retrieved 2026-10-28).

The governing design implication is consistent with the project principle: preserve a human's ability to interrupt or take over; make authority transitions explicit; do not conflate inferred intent with confirmed intent; ensure neutral output on stop/fault. This note does not claim a systematic literature review or assert a specific quantitative result.

## Fast/slow receding-horizon architecture

The PR-REX design target separates a fast reflex path from slower supervisory planning. This is a plausible systems architecture, but the draft's stated thread separation is not evidence that the real output loop is non-blocking under load. Any future validation should test queue saturation, inference stalls, backend exceptions, stale chunks and shutdown while the supervisor is busy. The fast path must remain capable of neutral output and timely Governor interaction independently of supervisory completion.

Candidate foundational source:
- [Receding horizon control overview (MathWorks)](https://www.mathworks.com/help/mpc/overview-of-model-predictive-control.html) (retrieved 2026-10-28). This is explanatory engineering documentation, not evidence for a gaming-agent performance claim.

## Motor accessibility and player-paced assistance

Accessibility research and guidance should inform remapping and adjustable assistance, but the repository should not implement unrequested input modalities or additional policy layers in this pass.

Starting references:
- [Xbox Accessibility Guidelines](https://learn.microsoft.com/gaming/accessibility/xbox-accessibility-guidelines/) (retrieved 2026-10-28).
- [Xbox Adaptive Controller](https://www.xbox.com/accessories/controllers/xbox-adaptive-controller) (retrieved 2026-10-28).
- [AbleGamers Player Panels](https://ablegamers.org/player-panels/) (retrieved 2026-10-28).
- [Game Accessibility Guidelines](https://gameaccessibilityguidelines.com/) (retrieved 2026-10-28).

Apply relevant principles by keeping player-facing remapping understandable, supporting adjustable timing/assistance where already in scope, ensuring assistance is visibly controllable and interruptible, and not treating disability-related adaptation as a lower-authority input. Do not claim conformance to a guideline without a documented audit of the actual interface and behavior.

## Retrieval accounting and gaps

- First Firecrawl batch: six searches; reported costs 7, 7, 7, 7, 7, and 7 credits (42 credits total).
- Second batch: rejected due to a per-minute request limit; no credit charge was returned for the rejected batch.
- This note contains source leads and clearly marked gaps; it is not a completed verification of every research question in the task brief.
- Current Firecrawl balance was 901 credits before research; exact balance should be rechecked before further calls.
- All source links above were retrieved or identified on 2026-10-28 unless marked as a candidate search link. Source-specific details not confirmed in the retrieved excerpts must remain unverified.
