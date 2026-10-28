# Run record template

Copy to \`evidence/<criterion-or-tool>/<run_id>.json\` after replacing fields with measured values. Do not use example or estimated values. Use \`null\` for unavailable measurements and explain why in \`notes\`.

\`\`\`json
{
  "run_id": "REQUIRED_ACTUAL_RUN_ID",
  "timestamp_utc": "REQUIRED_ACTUAL_ISO8601_TIMESTAMP",
  "git_rev": "REQUIRED_GIT_REV_OR_unknown",
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
  "observations": {},
  "raw_samples": [],
  "outcome": "UNVERIFIED",
  "evidence_paths": [],
  "notes": ""
}
\`\`\`

## Rules

- Allowed outcome labels: \`VERIFIED\`, \`PARTIALLY VERIFIED\`, \`UNVERIFIED\`, \`FAILED\`, \`BLOCKED\`, \`NOT IMPLEMENTED\`.
- Keep intended, commanded, delivered and observed values in separate fields.
- Identify synthetic fixtures and replay data explicitly; never label them as live capture.
- Preserve raw samples and link source files.
- A defect is RESOLVED only after a reproduced cause, evidence-backed diagnosis, fix, and ten subsequent clean runs.
- Scorecard thresholds remain PROPOSED, NOT FROZEN until the owner freezes them.
