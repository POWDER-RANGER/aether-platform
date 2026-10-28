# Failure taxonomy

Preserve every run, including failures. Player override and E-stop are not automatically defects.

| Class | Detection signal | Required run record | Failed run? |
|---|---|---|---|
| Capture failure | Missing/stale capture.heartbeat; source error | Last heartbeat, source error, frame seq/time, backend | Yes if required capture unavailable |
| Reader misread | perception.fact versus owner label | ROI/config hash, source frame, raw value/confidence, ground truth | Only against frozen scenario criterion |
| Planner timeout | Planner history timeout/replan flag | Active goal, timeout, world state, timestamps | Yes if frozen limit breached |
| Backend exception | lifecycle FAILED/exception | Traceback, backend/version, inputs, process logs | Yes |
| Stall | recovery.stall/stale heartbeat | Last progress, frame seq, intent, intervention, stack dump | Yes if frozen stall rule met |
| Governor rejection | Governor rejected decision/reason | Intent seq/source, reason, policy state, resulting output | Not alone; yes if valid intent wrongly rejected |
| Player override | Governor override/player input | Start/end, input ref, concurrent intent, output | No; preserve separately |
| E-stop | Governor estop/kill switch | Trigger source/time, neutral output, recovery | No by itself; preserve always |
| Recording gap | verifier nonmonotonic/missing frame or stream | Verifier output, missing range, drops, disk errors | Yes if required evidence incomplete |
| Crash | nonzero exit/lifecycle FAILED/no clean stop | stdout/stderr, exit, stack, manifest, partial streams | Yes |

If a signal is not emitted, record it unavailable; do not fabricate it or implement Governor hooks here.
