# Run record template

Copy this file to `evidence/<criterion-or-tool>/<run_id>.json` as JSON after replacing fields with measured values. Do not fill unknown values with examples or estimates. Use `null` for unavailable measurements and explain why in `notes`.

```json
{
  "run_id": "REQUIRED_ACTUAL_RUN_ID",
  "timestamp_utc": "REQUIRED_ACTUAL_ISO8601_TIMESTAMP",
  "git": {
    "revision": "REQUIRED_GIT_REV_OR_unknown",
    "dirty": true
  },
  "mode": "research",
  "environment": "ENV-01",
  "scenario": null,
  "hardware": {
    "computer": null,
    "os": null,
    "cpu": null,
    "gpu": null,
    "gpu_driver": null,
    "controller": null,
    "virtual_driver": null,
    "capture_backend": null
  },
  "software": {
    "python": null,
    "aether_revision": null,
    "dxcam": null,
    "ollama": null,
    "models": []
  },
  "observations": {},
  "raw_samples": [],
  "outcome": "UNVERIFIED",
  "evidence_paths": [],
  "notes": ""
}
```

## Rules

- Allowed outcome labels: `VERIFIED`, `PARTIALLY VERIFIED`, `UNVERIFIED`, `FAILED`, `BLOCKED`, `NOT IMPLEMENTED`.
- Keep intended, commanded, delivered and observed values in distinct fields.
- Identify synthetic fixture/replay data explicitly; never label it as capture.
- Preserve raw samples and link their source files.
- A defect is RESOLVED only after reproduced cause, evidence-backed diagnosis, fix, and ten subsequent clean runs.
- Scorecard thresholds remain PROPOSED, NOT FROZEN until the owner freezes them.
