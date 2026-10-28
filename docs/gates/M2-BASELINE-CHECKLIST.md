# M2 baseline completion checklist

M2 is not complete until every required item has an evidence artifact and owner review. Labels are the project's six evidence labels: VERIFIED, PARTIALLY VERIFIED, UNVERIFIED, FAILED, BLOCKED, NOT IMPLEMENTED.

| Required item | Minimum evidence label | Evidence expected |
|---|---|---|
| Run identity and reproducible environment | VERIFIED | Manifest with commit, dirty state, settings hash, OS/Python/hardware/backend identity. |
| Capture source and heartbeat | VERIFIED | Raw timestamped frame samples and heartbeat stream; synthetic evidence clearly separated. |
| Perception readers and ROI configuration | VERIFIED | Ground-truth labels, raw reader outputs, scoring report, ROI/config hashes. |
| Planner behavior and plan validation | VERIFIED | Scripted inputs, accepted/rejected plans, raw outputs and regression results. |
| Governor client protocol integration | VERIFIED | Signed-intent tests and recorded client submissions; Governor remains sole output authority. |
| Recording integrity and replay | VERIFIED | Run verifier output, matching frame index/files, monotonic streams and preserved failures. |
| Safety behavior (override, E-stop, neutral output) | VERIFIED | Existing control evidence plus owner-approved hardware verification; CI alone is insufficient. |
| Failure preservation and run classification | VERIFIED | Failed-run fixture and retained real failed-run evidence. |
| Documentation and frozen baseline | VERIFIED | Owner-reviewed checklist, frozen files and commit hash. |

A synthetic-only test can establish software behavior for synthetic fixtures, not real capture, hardware, controller passthrough, or gameplay capability. M2 status must remain the weakest applicable evidence label until each required item is supported.
