# Governor observation hook

**PROPOSED — requires owner approval (see OWNER-DECISIONS.md).** Documentation only. No implementation is authorized by this proposal.

**Overlap note (2026-10-28):** PR #4 (`runtime/slice-1`) already implements a read-only Governor observer: `src/aether/runtime/governor_bridge.py` attaches to the Governor's `IntentLog` and publishes `governor.*` events on the typed `aether.runtime.events.EventBus`, with an output-equivalence test (`tests/runtime/test_governor_bridge.py`); see `docs/architecture/RUNTIME.md`. Review this proposal as a comparison against that implementation, not as a separate design to build.

## Interface proposal

A read-only observer receives an immutable record after the Governor has completed its decision and output path. One event per decision: accepted, rejected, neutralised, player override, or E-stop. Suggested fields:

- `event_id`, `t_mono_ns`, `tick_index`, `decision`, `reason_code`
- `source`, `producer`, `intent_seq`, `delegation_id`, `claims`
- `accepted_frame_count`, `rejected_frame_count`, `neutralised`, `override_active`, `estop_active`
- `output_frame_sha256` (hash of canonical emitted controller-frame bytes; never a mutable frame reference)
- `policy_revision`, `observer_schema_version`

No key material, raw HMAC, personal input payload, or mutable Governor object is exposed.

## Non-interference invariant

The observer is downstream of the final decision and output call. It has no reference to the adapter, policy, kill switch, or client. The Governor does not await it, query it, or branch on its result. Observer exceptions are contained outside the decision path. A bounded queue drops observer records on overflow and increments an out-of-band dropped counter; it must never block, retry synchronously, or back-pressure controller output. A dedicated worker serializes immutable records to the event bus. Queue size and drop accounting must be observable without a Governor callback.

## Equivalence test plan

On an isolated dry-run adapter, execute the same scripted intent sequence twice from identical initial state: once with no observer and once with observer enabled. Capture controller frame bytes at the adapter boundary and tick timestamps. Require byte-for-byte equality of the emitted frame sequence. Compare tick timestamp sequences with a predeclared tolerance derived from the existing tick jitter baseline; report raw deltas and do not relax the tolerance after seeing results. Include accepted, rejected, neutralised, override and E-stop cases. Repeat on Windows and Linux CI, then on the MSI; preserve scripts, raw traces, hashes, and failed runs. Timing tolerance is not a frozen threshold in this proposal.

## Threading and back-pressure

Use a single-producer/single-consumer bounded queue where possible. The producer performs only immutable-record construction and nonblocking enqueue; no JSON encoding, disk I/O, logging, callbacks, or allocations proportional to frame count in the tick. Worker owns serialization and publication. On full queue: drop the observation record, increment a lock-free/atomic or otherwise nonblocking counter, continue output. Shutdown drains only within a bounded deadline; leftovers are counted, not awaited by the Governor.

## MSI approval checklist

Before owner approval, inspect actual tick path and adapter call ordering; measure observer-on/off CPU and allocation overhead; test queue saturation and worker crash; test exception containment; verify E-stop/override precedence and neutral output unchanged; compare controller-frame bytes and tick timestamps; verify no key or personal data leakage; verify shutdown and recovery; record OS, Python, controller backend, GPU/capture load and exact commit. Owner must approve the interface and timing tolerance before any code change.
