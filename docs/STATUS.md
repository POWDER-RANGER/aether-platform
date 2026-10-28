# Æther build status

Snapshot 2026-10-26. Living document: update it with every merged milestone. Status words: project instructions §10. Every claim points at its evidence.

## 1. Repository and history

| Item | State |
| --- | --- |
| Repository | `POWDER-RANGER/aether-platform`, public, MIT (`LICENSE`); third-party terms in `THIRD-PARTY.md` (NitroGen: NVIDIA non-commercial research only, never committed) |
| Reference | `POWDER-RANGER/powder-ranger-bot`: retired, read-only; ported from `ad15296`; never modified |
| `main` | `939f8bd` foundation → `0fc63c2` PR #1 → `4ab4390` PR #2 → `ea25d12` PR #3 (all merged; CI green on each) |
| PR #2 `m1/control-foundation` | Merged as `4ab4390` (squash). Reviewed by the second AI agent (approved; findings 1–5 fixed; flaky-test fix) |
| PR #3 `m1.1/keyboard-mouse` | Merged as `ea25d12` (squash), review findings 1–2 fixed first |
| CI | GitHub Actions: Ubuntu + Windows × Python 3.11 + 3.13: install, token check, pytest, ruff check, ruff format |
| Repository protections | Secret scanning, push protection, Dependabot security updates on. Branch protection for `main` proposed (D-017), not applied |

## 2. Capability status

| Area | Status | Evidence |
| --- | --- | --- |
| Charter, ecosystem map, decisions, reference inventory | Draft for owner review (D-013) | `docs/vision/CHARTER.md`, `docs/architecture/`, `docs/decisions/DECISIONS.md` (D-000 – D-021) |
| Design system: tokens, components, gallery | CI verified | `interfaces/shared/design/`, `tests/interfaces/` |
| Repository boundaries (no weights, keys, STOP, `.env`, workstation records, personal paths) | CI verified | `tests/repo/`, `docs/security/SECRETS-POLICY.md`, `SECURITY.md` |
| Workstation setup and check | Locally verified (MSI) | `docs/workstation/SETUP.md`, `scripts/workstation/Test-Workstation.ps1` |
| Signed intent (HMAC-SHA256); stale, replayed, forged, tampered rejected | CI verified | `tests/control/test_intent_and_log.py`, `test_signed_ingress.py` (real ZMQ + `serve()`), mutation check |
| Governor policy: delegation, scopes, rate, focus, confidence, menu strip, online rules; player override | CI verified (unit) | `tests/control/test_policy.py`, `test_governor.py`, `test_shared_control.py` |
| Kill switch / STOP → neutral output | CI verified (unit); hardware verified on MSI: pad 2 runs, keyboard/mouse 1 run | `docs/verification/M1-CONTROL.md`, `M1.1-KEYBOARD-MOUSE.md` |
| Hash-chained, sealed intent log | CI verified; every MSI run log verified | `aether verify-log` |
| Motor model (human limits) | CI verified (unit) | `tests/control/test_motor.py` |
| Research / Companion modes | CI verified | `tests/control/test_governor.py` |
| Virtual X360 pad: both sticks ×4 directions, both triggers, all 15 buttons, neutral | Hardware verified (virtual, 3 runs); screening, not reliability | `M1-CONTROL.md` run set B |
| Keyboard/mouse output behind the Governor | Hardware verified (test window, clean set of 10 runs, 27/27 each) | `M1.1-KEYBOARD-MOUSE.md` |
| Focus gate: keyboard/mouse releases and blocks when the window loses focus; fails closed without a focus check | CI verified + hardware verified | `tests/control/test_kbm.py`, set of 10 |
| Pause hotkey kill switch | UNVERIFIED here (verified in the reference, 2026-10-21) | — |
| DS4 axis direction | UNVERIFIED | XInput cannot read a DS4 |
| Physical pad passthrough; live player override with a physical pad | BLOCKED | No physical pad connected |
| Input reaching a real game (pad or keyboard/mouse) | UNVERIFIED | No game run in this repository |
| NitroGen reflex backend | Ported; UNVERIFIED here | Reference: 225 ms/chunk synthetic, play quality poor |
| Capture (dxcam) | Ported; UNVERIFIED here | Reference: 3.3 ms median |
| Runtime slice 1: versioned settings, event bus, agent identity/lifecycle, tasks, Governor observation, work receipts | Implemented on `runtime/slice-1` (PR #4); CI verified once merged | `docs/architecture/RUNTIME.md`, `tests/runtime/` |
| Policy engine beyond the Governor, task retries/dependencies, event replay across restarts | NOT IMPLEMENTED | — |
| AACP runtime records | PARTIAL: work receipts (`runtime/evidence.py`); session records and handoffs not yet | `protocols/aacp/specification/AACP.md` |
| Resource and model management, capability registry | NOT IMPLEMENTED | — |
| Perception, world state, supervision, planning | NOT IMPLEMENTED | — |
| Recording and replay, scorecards (E-01 – E-10), scenarios (SCN, DG) | NOT IMPLEMENTED | — |
| Application interface (Command Center etc.) | NOT IMPLEMENTED (design system only) | — |

## 3. Numbers

- Tests: 136 with M1.1 (113 for M1 alone); full suite 10/10 repeated runs clean on the MSI after the flaky-test fix.
- Hardware runs on the MSI: pad 6 full + 2 stop runs; keyboard/mouse 11 exploratory + 10 clean + 1 stop run; every intent log chain + seal OK.

## 4. Open decisions (owner)

| ID | Decision |
| --- | --- |
| D-017 | Protect `main` (PR + CI required, admins not locked out) |
| D-013 | Accept or amend the charter |
| D-006 | Application interface technology (recommendation: local web UI served by the runtime, read-only first) |
| D-004 | Product accent colors |
| AACP | Adopt, amend or reject the protocol (class C) |

## 5. Next engineering steps (in order)

1. First runtime slice: versioned settings schema, a local event bus, agent identity and lifecycle, with the Governor publishing its decisions and state changes as events.
2. Recording: synchronized frames, player input, intended / commanded / delivered actions, from the event bus.
3. Engineering scorecard E-01 – E-10 and the first Command Center view reading real runtime state.
4. Hardware gaps when the owner can: Pause hotkey, physical pad passthrough and live override, DS4 axes, one ENV-01 session through each output path.
