# M1 control foundation: verification record

What has run, where, and what has not. Status words: project instructions §10.

## Scope

Ported from `POWDER-RANGER/powder-ranger-bot` @ `ad15296` (read-only reference) into `src/aether/control/` (platform-owned controller authority), `src/aether/capture/`, and `src/prrex/backends/nitrogen.py`. The first commit on the M1 branch is the unmodified port apart from import paths, so later changes are reviewable as diffs.

| Module | Role |
| --- | --- |
| `intent.py` | `IntentPacket`, `GamepadFrame`, `Delegation`; HMAC-SHA256 signing and verification |
| `governor.py`, `policy.py`, `safety.py`, `client.py` | Governor (single path to the controller), rules, kill switch and focus check, client channel (ZMQ) |
| `intent_log.py` | Append-only hash-chained log; seal with a machine-local key |
| `motor.py`, `filters.py` | Human-limit motor model; One Euro filter |
| `adapters.py` | Virtual X360 / DS4 adapters (vgamepad) and the dry-run adapter |
| `player.py` | Player input channel (shared control) |
| `settings.py`, `default.yaml` | Settings; Companion and Research modes |
| `aether/cli.py` | `padtest` (with XInput read-back), `verify-log`, `stop` |

Not ported in M1, by design: calibration, gaze, voice, Game Packs, session report, launcher. They return with the milestones that need them.

## Evidence

| Capability | Status | Method | Result | Environment |
| --- | --- | --- | --- | --- |
| Intent signing; bad signatures, stale and replayed packets rejected | VERIFIED | `tests/control/test_intent_and_log.py`, `test_governor.py`, `test_review_regressions.py` | pass | MSI (Python 3.11.16) and CI |
| Policy: delegation required, scopes, rate limits, menu buttons stripped, online rules | VERIFIED | `tests/control/test_policy.py`, `test_governor.py` | pass | MSI and CI |
| Player override pre-empts the companion; shared-control claims | VERIFIED (unit) | `tests/control/test_shared_control.py`, `test_player_input.py` | pass | MSI and CI |
| Hash chain and seal; tampering detected | VERIFIED | `tests/control/test_intent_and_log.py`; `aether verify-log` on 4 real padtest logs | chain OK and seal OK on all 4 | MSI |
| Motor model limits and timing | VERIFIED (unit) | `tests/control/test_motor.py` | pass | MSI and CI |
| Companion / Research mode validation | VERIFIED | `tests/control/test_governor.py` | pass | MSI and CI |
| Virtual X360 pad: every axis, trigger and button, through the Governor | VERIFIED (virtual, 3 runs) | `aether padtest --output x360 --readback` | 19/19 steps matched on each of 3 runs | MSI, ViGEmBus |
| STOP file halts a live session and leaves the pad neutral | PARTIALLY VERIFIED (1 run) | `padtest --readback`, then `aether stop` after 4 s | halted during step 3; pad read back NEUTRAL; log chain and seal OK (60 records) | MSI |
| Pause hotkey trips the kill switch | UNVERIFIED in this repository | Verified in the reference on 2026-10-21; not re-run here | — | — |
| DS4 axis direction | UNVERIFIED | XInput cannot read a DS4 | — | — |
| Physical pad passthrough; live player override with a physical pad | BLOCKED | No physical pad connected to the MSI | — | — |
| NitroGen round trip and live ENV-01 play | UNVERIFIED in this repository | Backend ported; reference recorded 225 ms/chunk and poor play quality | — | — |

Virtual-controller results are not physical-hardware results. Three runs are screening evidence; ten are needed for a reliability claim.

## Reproduce

```powershell
python -m pip install -e ".[windows,dev]"
python -m pytest -q
python -m aether padtest --output x360 --readback --report padtest.json
python -m aether verify-log <logs\padtest-*.jsonl>
```

`stop_file` and the log-sealing key stay at `~/.powder_ranger/` for continuity with the reference runtime (DECISIONS D-019).
