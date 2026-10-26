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

Not ported in M1, by design: calibration, gaze, voice, Game Packs, session report, launcher.

## Automated tests

| Capability | Status | Tests | Where observed |
| --- | --- | --- | --- |
| Intent signing; bad signatures, stale and replayed packets rejected | VERIFIED | `test_intent_and_log.py`, `test_governor.py`, `test_review_regressions.py` | CI (4 jobs) and MSI |
| **Signed ingress end to end**: `GovernorClient` → local ZMQ → `Governor.handle_raw` → policy → adapter. Valid player intent reaches output; companion intent denied without a delegation and allowed after a signed grant; wrong-key intents, a forged halt and a tampered message are rejected with no controller output and logged; the real `serve()` loop does the same and stops on a signed shutdown | VERIFIED | `test_signed_ingress.py` (added after review finding #1) | CI and MSI |
| Same tests fail if signature verification is removed | VERIFIED (author mutation check) | `verify_message` replaced by an accept-anything stub: 2 of the 4 ingress tests fail, as intended | MSI only |
| Policy: delegation, scopes, rate limits, menu buttons stripped from companion output, online rules | VERIFIED | `test_policy.py`, `test_governor.py` | CI and MSI |
| Player override pre-empts the companion; shared-control claims | VERIFIED (unit) | `test_shared_control.py`, `test_player_input.py` | CI and MSI |
| Hash chain and seal; tampering detected | VERIFIED | `test_intent_and_log.py` | CI and MSI |
| Motor model limits and timing | VERIFIED (unit) | `test_motor.py` | CI and MSI |
| Companion / Research mode validation | VERIFIED | `test_governor.py` | CI and MSI |
| Pad test covers every control and the read-back flags mismatches | VERIFIED | `test_cli.py` | CI and MSI |

## Virtual controller on the MSI (ViGEmBus, virtual X360, XInput read-back)

Two pad-test definitions have been run. They are reported separately; the first did not cover every control.

| Run set | Steps | Controls covered | Runs | Result |
| --- | --- | --- | --- | --- |
| A: original (2026-10-25 local, commit `6189ba8`) | 19 | Left stick 4 directions; right stick UP and RIGHT only; both triggers; 10 buttons (face, shoulders, D-pad); neutral. **Not covered:** right stick DOWN and LEFT; LEFT_THUMB, RIGHT_THUMB, START, BACK, GUIDE | 3 | 19/19 matched on each |
| B: expanded (2026-10-26 local, after review finding #2) | 26 | Both sticks 4 directions; both triggers; all 15 mapped buttons; neutral. GUIDE is read with `XInputGetStateEx` (ordinal 100) because `XInputGetState` does not report it | 3 | 26/26 matched on each |

| Check | Status | Result |
| --- | --- | --- |
| Full virtual X360 control surface through the Governor | VERIFIED (virtual, 3 runs, set B) | 26/26 steps on each run |
| STOP file halts a live session; pad held neutral | PARTIALLY VERIFIED (2 runs) | Run 1 (set A): halted in step 3, read back NEUTRAL. Run 2 (set B): halted in step 5, read back NEUTRAL, exit code 4 |
| Intent logs of these runs | VERIFIED | Set A: 4 logs; set B: 4 logs (3 full runs + stop run). `aether verify-log`: chain OK and seal OK on all 8 |

Virtual-controller results are not physical-hardware results. Three runs are screening evidence; ten are needed for a reliability claim.

## Not verified

| Capability | Status | Reason |
| --- | --- | --- |
| Pause hotkey trips the kill switch | UNVERIFIED in this repository | Verified in the reference on 2026-10-21; not re-run here |
| DS4 axis direction | UNVERIFIED | XInput cannot read a DS4 |
| Physical pad passthrough; live player override with a physical pad | BLOCKED | No physical pad connected to the MSI |
| NitroGen round trip and live ENV-01 play | UNVERIFIED in this repository | Backend ported; reference recorded 225 ms/chunk and poor play quality |

## Reproduce

```powershell
python -m pip install -e ".[windows,dev]"
python -m pytest -q
python -m aether padtest --output x360 --readback --report padtest.json
python -m aether verify-log <logs\padtest-*.jsonl>
```

`stop_file` and the log-sealing key stay at `~/.powder_ranger/` for continuity with the reference runtime (DECISIONS D-019).
