# Bulk scaffold — 2026-10-28

Status of everything in this drop: **NOT VERIFIED.** Written in one pass at the owner's request (bulk rough work,
refine later; tests deliberately skipped). Only check run: `python -m compileall` (syntax). Nothing here changes the
verified M1 control code (`src/aether/control/`). Do not cite any of it as implemented capability until refined and tested.

## What was added

| Area | Files | Purpose | Milestone |
| --- | --- | --- | --- |
| Runtime | `src/aether/runtime/{events,lifecycle,config,identity}.py` | Event bus + JSONL sink, component lifecycle, versioned platform settings, run identity/provenance | M1 step 1 |
| Recording | `src/aether/recording/{session,replay}.py` | Run dir with manifest, distinct intended/commanded/delivered/observed/player_input streams, sampled frames, merged replay | M1 step 2 |
| Capture | `src/aether/capture/source.py` | dxcam component into FrameBuffer; replay source (labelled replay) | M1/M2 |
| Perception | `src/aether/perception/{frame_buffer,preprocess,world_state,readers,pipeline}.py` | Ring buffer, 256×256 reflex view, ROI crops, bar/OCR/template readers, WorldState with confidence + provenance + observed/interpreted | M2 |
| Backends | `src/prrex/backends/{base,ollama_vlm,nitrogen_reflex}.py` | Reflex/Supervisor protocols + registry; local Ollama VLM supervisor; NitroGen adapter; null backends (never evidence) | M1/M2 |
| Planning | `src/prrex/supervisor/{planner,recovery}.py` | Subgoal queue, success-check evaluator, timeouts → replan; stall detector | M2 |
| Companion loop | `src/prrex/runtime.py` | Reflex thread (receding horizon, Governor-only output) + non-blocking supervisor thread | M2 |
| Evaluation | `src/aether/evaluation/{scorecard,scenarios}.py` | E-01..E-10 proposed definitions + ledger; SCN/DG loader; threshold freeze/check | M1/M2/M3 |
| Command Center | `src/aether/server/app.py`, `interfaces/command-center/index.html` | Read-only local web view: health, scorecard, runs, live events | M1 step 3 (D-006 pending) |
| CLI | `src/aether/cli_ext.py` | serve, runs, replay, scorecard, record, scenarios, freeze, check, companion | — |
| Config | `configuration/platform/ENV-0{1,2}.yaml`, `configuration/scenarios/{SCN-01..05,DG-01..04}.yaml` | Platform settings; neutral scenario definitions | — |

## Needed for production status (in order)

1. **Interface checks against verified code** (marked `REFINE:` in source): `send_frames` kwargs and `Source.REFLEX` already aligned to `client.py`/`intent.py`; still open: frame_dt/TTL from control settings, intent key path from `control.settings`; NitroGen request schema in `prrex/backends/nitrogen.py`.
2. **Governor → event bus:** Governor decisions/state changes published as events (commanded / delivered streams). Needs a small hook in `governor.py` — touches verified code, so add tests first.
3. **Tests** for every new module (unit: bus overflow, lifecycle order/failure, config unknown-key rejection, recording layout, replay ordering, readers on fixture crops, planner checks/timeouts, stall detector, scorecard status validation, scenario freeze/check, server path traversal). Then ruff check/format; CI green on Ubuntu+Windows.
4. **Owner decisions:** D-006 (UI tech; this draft assumes local web), scorecard E-01..E-10 definitions/thresholds (proposed only), scenario thresholds, supervisor model choice.
5. **Hardware verification on the MSI:** capture latency (E-07), reflex non-blocking under VLM load (E-08), ENV-01 session reliability (E-09), recording completeness (E-10), VRAM budget reflex + supervisor on 8 GB.
6. **ENV-02 calibration** on owner-controlled recordings: ROI boxes and reader colours are placeholders.
7. Merge `cli_ext` into `cli.py`; add `pytesseract`/`opencv-python` as an optional `perception` extra in `pyproject.toml`; update `docs/STATUS.md` only with verified results.

Not started (milestone discipline): M4 player adaptation, M5 learning, M6 generalization, audio, persistent memory.
