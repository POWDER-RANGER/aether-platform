# Æther runtime: slice 1

Package `aether.runtime`. Software only: no hardware, no controller output of its own.

## What it is

| Part | File | Role |
| --- | --- | --- |
| Settings schema | `aether/control/settings.py` | `schema_version: 1`; unknown keys, other versions and invalid values raise `ConfigError` before anything is built (fail closed) |
| Event bus | `runtime/events.py` | Typed, versioned events (`aether.event/1`): unique id, UTC and monotonic timestamps, session id, correlation id, causation id, source, data. Each type declares its required fields; unknown types, missing fields and non-JSON data are refused. Written to a hash-chained, sealed log before subscribers see them. Secret-looking fields are redacted. A failing subscriber is isolated and reported as `bus.subscriber_error` |
| Agents | `runtime/agents.py` | Registration (unique id, name, role, capabilities, version), lifecycle state machine, discovery by capability, exclusive resource ownership released on stop or failure |
| Tasks | `runtime/tasks.py` | Create, assign to a capable available agent, start, complete, fail, cancel, timeout. The task id is the correlation id of every event about it |
| Governor observation | `runtime/governor_bridge.py` | Turns the Governor's own intent-log records into events; wraps the output adapter to report delivered output and adapter failures |
| Evidence | `runtime/evidence.py` | Work receipt: each log's SHA-256, record count, chain and seal result, event counts; `ok` only if everything verifies |
| Session | `runtime/runtime.py` | `Runtime(settings, session_dir, seal_key)`: one session's bus, agents, tasks; `observe_governor`, `observe_adapter`, `correlate`, `close`, `receipt` |

## Authority boundary

The Governor remains the only authority over companion-controlled output. The runtime observes it and never decides:

- Observation is attached to the Governor's `IntentLog` as a read-only observer: it gets a deep copy of each record after the record is written, runs outside the log lock, and its exceptions are swallowed and counted (`observer_errors`).
- Nothing in `aether.runtime` calls the Governor, its policy or an adapter's output path. `ObservedAdapter` forwards every call unchanged and re-raises every error.
- Tested: the same scenario (denied, allowed, player override, focus loss, halt) produces identical controller output and Governor statistics with and without observation, and with an observer that raises on every record.

Agents and tasks are records of who is doing what. Holding the `controller.output` resource or a running task does not authorize output; only a player delegation in the Governor does.

## Event catalog (v1)

`session.started`, `session.ended`; `agent.registered`, `agent.state`; `resource.claimed`, `resource.released`, `resource.conflict`; `task.created`, `task.assigned`, `task.state`; `governor.session`, `governor.decision`, `governor.override`, `governor.focus_block`, `governor.rejected`, `governor.grant`, `governor.revoke`, `governor.halt`, `governor.resume`, `governor.watchdog`, `governor.player_command`, `governor.record`; `adapter.active`, `adapter.neutral`, `adapter.error`; `bus.subscriber_error`. Required fields: `EVENT_TYPES` in `runtime/events.py`.

Governor events carry `intent_log_n`, the record number in the Governor's own log, so each event points back to the primary record.

## Costs and limits

- Observation runs synchronously on the Governor's thread. Measured on the MSI: `Governor.handle("intent")` median 41 µs without observation, 128 µs with it; p99 about 0.11–0.16 ms vs 0.33–0.36 ms (2 runs × 2,000 intents). Well under the 8.3 ms tick and 400 ms intent lifetime. If it ever matters, the observer can hand records to a queue instead.
- One process, one session, in-memory history capped at 50,000 events (the log on disk keeps everything).
- No event replay or recovery across restarts yet; no task retries or dependencies; no permission engine beyond the Governor.
