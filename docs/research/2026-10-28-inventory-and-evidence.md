# Æther / PR-REX implementation inventory

**Retrieved:** 2026-10-28  
**Base:** `main` at `ea25d12678d40b8aea03d6326b12866bac95e6df`  
**Scope:** Repository tree and tracked documentation/code at that revision. This is a GitHub-source inspection, not a local checkout, execution, or hardware test.

## Status vocabulary

- **NOT IMPLEMENTED** — no implementation found in the inspected `main` tree.
- **DOC ONLY** — described in documentation/specification, with no corresponding implementation found.
- **CODE PRESENT** — implementation files exist; no matching automated test was established during this inventory.
- **CODE + TESTS** — implementation and corresponding test files exist. This does not imply hardware verification.

## Subsystem inventory at base revision

| Subsystem | Classification | Evidence paths / notes |
|---|---|---|
| App shell / Command Center | NOT IMPLEMENTED | Design system exists under `interfaces/shared/design/`; no application shell or server in `main`. PR #5 proposes these; it is an open draft, not part of this base. |
| Configuration | CODE + TESTS | `src/aether/control/settings.py`, `src/aether/control/default.yaml`, `configuration/profiles/*.yaml`, `tests/control/test_cli.py` and settings-related checks in existing control tests. Platform runtime configuration is not present on this base. |
| Logging / storage | CODE + TESTS | `src/aether/control/intent_log.py`, `tests/control/test_intent_and_log.py`; append-only log, chain and seal. Runtime event store and recording storage are not on this base. |
| Governor | CODE + TESTS | `src/aether/control/governor.py`, `policy.py`, `safety.py`, `tests/control/test_governor.py`, `test_policy.py`, `test_shared_control.py`, `test_review_regressions.py`. |
| IntentPacket + HMAC | CODE + TESTS | `src/aether/control/intent.py`, `client.py`, `tests/control/test_intent_and_log.py`, `test_signed_ingress.py`. |
| Hash-chained log | CODE + TESTS | `src/aether/control/intent_log.py`, `tests/control/test_intent_and_log.py`. |
| Watchdog / neutral output | CODE + TESTS | Governor tick path in `src/aether/control/governor.py`; kill/neutral behavior tests in `tests/control/test_governor.py` and `test_review_regressions.py`. Confirmed behavior is limited to the tested unit paths. |
| Player override / E-stop | CODE + TESTS | `src/aether/control/player.py`, `safety.py`, `governor.py`; `tests/control/test_player_input.py`, `test_shared_control.py`, `test_governor.py`. |
| Virtual controller output | CODE + TESTS | `src/aether/control/adapters.py`; `tests/control/test_cli.py`. Physical MSI read-back evidence is recorded separately in `docs/verification/M1-CONTROL.md` and is owner-reported evidence, not independently repeated here. |
| Physical passthrough | DOC ONLY | Hardware gap noted in `docs/STATUS.md` and `docs/verification/M1-CONTROL.md`; no implementation file for a physical passthrough bridge was found in this tree. |
| Capture | CODE PRESENT | `src/aether/capture/screen.py`. Hardware-dependent capture remains UNVERIFIED in the active status record; no direct capture test file was found. |
| Perception / world state | NOT IMPLEMENTED | No `src/aether/perception/` package in base tree. Proposed in open draft PR #5 only. |
| OCR / HUD readers | NOT IMPLEMENTED | No reader or OCR package in base tree. Proposed in open draft PR #5 only. |
| Reflex path | CODE PRESENT | `src/prrex/backends/nitrogen.py`. Backend port is documented as UNVERIFIED in `docs/STATUS.md` and `docs/verification/M1-CONTROL.md`; no backend-specific test file found. |
| Supervisory planner | NOT IMPLEMENTED | No `src/prrex/supervisor/` package in base tree. Proposed in open draft PR #5 only. |
| Backend interface / registry | CODE PRESENT | `src/prrex/backends/nitrogen.py`; a generalized backend contract/registry is proposed in PR #5, not in base. |
| Recording / replay | NOT IMPLEMENTED | No `src/aether/recording/` package in base tree. Proposed in open draft PR #5 only. |
| E-01..E-10 scorecard | DOC ONLY | Scorecard is referenced in project-level docs, but no scorecard implementation found on base. PR #5 proposes one. |
| ENV-01 / ENV-02 | DOC ONLY | Identifier convention in `docs/decisions/DECISIONS.md`; full environment configuration files not present on base. PR #5 proposes them. |
| SCN-01..05 / DG-01..04 | DOC ONLY | Scenario definitions are specified by the task brief and PR #5 draft additions; none are present on base. |

## Contradictions and reconciliation guidance

1. **README vs open PR #5:** README describes runtime, perception, and application intelligence as NOT IMPLEMENTED. PR #5 proposes a bulk scaffold for these areas but explicitly labels it NOT VERIFIED and says tests were skipped. Do not change README capability status until the PR #5 additions are merged and tested.
2. **STATUS snapshot vs repository evolution:** `docs/STATUS.md` labels its snapshot 2026-10-26 and describes runtime as NOT IMPLEMENTED. Open PR #4 proposes a tested runtime slice, but is not merged in the inspected `main`. Keep branch/base status separate; do not present PR content as mainline.
3. **PR #5 implementation notes vs code:** the draft explicitly lists unresolved interface alignment, Governor event bridging, tests, command integration, optional OCR dependencies, and hardware checks. Keep all those items PARTIALLY VERIFIED / UNVERIFIED / NOT IMPLEMENTED until evidence is produced.
4. **Status taxonomy:** the current STATUS file refers to “project instructions §10” and includes mixed labels such as “CI verified” and “hardware verified”. For new research notes and inventory, use the six explicit evidence labels from the owner brief, and distinguish automated tests from hardware execution.

## Authority and evidence boundaries

- The Governor remains the only permitted path for companion output.
- Passing unit tests do not verify capture/display acquisition, virtual-driver installation, physical passthrough, real-game input, the MSI RTX 4060 performance envelope, or 8 GB VRAM coexistence.
- Do not mark a defect RESOLVED without a reproduced cause, evidence-backed diagnosis, fix, and ten subsequent clean runs.
- The base tree has no local test execution evidence from this inspection. No CI result is asserted here.
- `history/` was absent from the inspected tracked tree; it remains out of scope regardless.
- The reference repository remains read-only and was not modified.

## PR and CI state observed

- Base `main`: `ea25d12678d40b8aea03d6326b12866bac95e6df`.
- Open PR #4: runtime slice; it is separate concurrent work and not part of the base.
- Open draft PR #5: bulk scaffold, explicitly not verified and tests deliberately skipped.
- CI workflow on base: `.github/workflows/ci.yml` runs Ubuntu and Windows against Python 3.11 and 3.13; install, generated-token check, pytest, Ruff lint and format.
- This inventory makes no claim that these jobs are currently passing.
