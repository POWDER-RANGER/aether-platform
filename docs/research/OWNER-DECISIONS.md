# Owner decisions and non-decisions — 2026-10-28

This file records decisions intentionally left to the owner. None is silently resolved by this branch.

| Topic | Current evidence | Owner decision / action |
|---|---|---|
| Draft scaffold PR #5 | Open draft; says tests deliberately skipped; 41 changed files | Decide whether to keep the broad draft as the integration target, split it into smaller slices, or close/re-scope it after review. No action taken here. |
| Governor event bridge | PR #5 notes a required Governor hook; current Governor is the authority for controller output | Approve a minimal read-only observation hook only after the proposed test proves byte-for-byte identical output and timing behavior is adequately measured. |
| Command Center technology | Existing decision D-006 is owner-only; draft assumes a local web UI | Decide whether to accept the local read-only web UI direction. Not implemented or approved here. |
| Evaluation scorecard E-01..E-10 | Definitions/thresholds appear proposed in the draft; frozen thresholds must not change | Owner to approve definitions and freeze thresholds through the existing governance process. No threshold values changed here. |
| SCN / DG formalization | Draft scenario content is placeholder and uncalibrated | Owner to approve ground-truth definitions, calibration data and thresholds before formal evaluation. |
| ENV-02 ROIs and HUD readers | Draft uses example coordinates and colour heuristics | Calibrate against owner-controlled captures and label all fixture/replay evidence; no placeholder treated as live data. |
| Supervisor model | Draft references a Qwen VLM option; no comparable 8 GB target-hardware measurement established in this pass | Select only after measuring peak VRAM and warm/cold latency alongside the reflex process on the MSI. |
| Capture backend | DXcam upstream advertises DXGI and WinRT; no local comparison performed | Choose based on owner hardware tests and required capture behavior; no dependency or code change proposed here. |
| Virtual driver and physical pad visibility | This research pass did not verify successor driver status, official distribution/signing or HidHide conflicts | Owner to authorize any driver installation/device-hiding experiment after official source verification and rollback plan. |
| Branch protection | Main branch API metadata reported protection disabled; D-017 is still proposed | Owner decision to configure PR/CI protections in repository settings. This branch does not alter settings. |

## Explicitly unchanged

- No frozen evaluation threshold.
- No milestone order or M1–M6 scope.
- No requirement beyond player override, emergency stop, hardware protection and reliable shutdown.
- No new input method.
- No NitroGen weights or code added.
- No file under `history/` changed.
- No changes to the retired reference repository.
- No merge into `main`.
