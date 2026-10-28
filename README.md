# Æther platform

Repository: [POWDER-RANGER/aether-platform](https://github.com/POWDER-RANGER/aether-platform)

> The player is the legend. PR-REX is the body double.

Æther is the platform. PR-REX is its principal application. AACP governs how agents build both. Start with `docs/vision/CHARTER.md`.

## Status

Full build status with evidence: `docs/STATUS.md`.

| Part | Status |
| --- | --- |
| Charter, ecosystem map, decision register, reference inventory | Draft for owner review |
| Design system (tokens, components, gallery, tests) | VERIFIED: tests pass, rendering checked |
| Repository hygiene (secrets policy, boundary tests, workstation setup) | VERIFIED: boundary tests in CI (PR #1) |
| AACP | Proposed specification |
| Control foundation (`aether.control`): signed intent, Governor, hash-chained log, motor model, virtual pads | Ported in M1; see `docs/verification/M1-CONTROL.md` |
| Keyboard/mouse output (`aether.control.kbm`) | M1.1; see `docs/verification/M1.1-KEYBOARD-MOUSE.md` |
| Platform runtime (agents, tasks, policy engine, events), PR-REX perception and intelligence | NOT IMPLEMENTED |

## Layout (directories appear when their first file does)

| Path | Contents |
| --- | --- |
| `docs/vision/` | `CHARTER.md`, `BRAND.md` |
| `docs/architecture/` | `ECOSYSTEM.md`, `RESOURCE-INDEX.md`, `LEGACY-REFERENCE.md` |
| `docs/decisions/` | `DECISIONS.md` |
| `docs/security/` | `SECRETS-POLICY.md`: what is never committed, and how that is enforced |
| `docs/workstation/` | `SETUP.md`: reproducible workstation setup and the `ENVIRONMENT.md` template |
| `scripts/workstation/` | `Test-Workstation.ps1`: workstation verification |
| `protocols/aacp/specification/` | `AACP.md` |
| `interfaces/shared/design/` | Design system: `DESIGN-SYSTEM.md`, tokens, components, gallery, fonts |
| `scripts/brand/` | `build_tokens.py` |
| `tests/interfaces/` | Design-token tests |
| `tests/repo/` | Repository-boundary tests |

## Install and test

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"          # add ,windows for virtual pads and capture
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m aether padtest --output x360 --readback   # Windows + ViGEmBus
.venv\Scripts\python -m aether kbmtest                            # Windows; opens its own test window
```

## Design system in one minute

Link `interfaces/shared/design/tokens.css`, then `components.css`; put `class="ae"` on `<body>`; set `data-product` to `aether`, `prrex` or `aacp`. Every capability shows an evidence status, every running part an operational state; mock data only inside `.demo-frame`. Change a value in `tokens.json`, run `python scripts/brand/build_tokens.py`, then `pytest`.

## License

MIT for Æther's own code (`LICENSE`). Third-party components keep their own licenses; see `THIRD-PARTY.md`. NitroGen, the current reflex backend, is licensed for non-commercial research only and is not included here.


## Implementation evidence boundary (2026-10-28)

The runtime, perception, recording, supervisor, scorecard and Command Center status is recorded in [the project status document](docs/STATUS.md). See [the dated repository inventory](docs/research/2026-10-28-inventory-and-evidence.md) for a subsystem-by-subsystem classification. Do not treat a draft PR, successful syntax compilation, or a passing unit test as hardware verification.
