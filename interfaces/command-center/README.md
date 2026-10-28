# Command Center read-only views

The server binds only to \`127.0.0.1\` and implements GET routes only.

- \`/runs/<id>\`: manifest, stream counts, duration summary and E-10 verdict when present.
- \`/replay/<id>\`: frame timeline scrubber with event context; intended, commanded, delivered and observed streams remain separate.
- \`/scorecard\`: E-01..E-10 status, value, evidence link and PROPOSED, NOT FROZEN threshold.
- \`/overlay\`: polls \`/api/events\` every 500 ms for latest supervisor assessment and reflex chunk. Null backend is explicitly labelled.
- \`/calibrate\`: local-image or recorded-frame ROI calibration; exports a YAML snippet and never writes configuration.

The interface uses shared design token CSS, has phone-width layout rules, and uses “no data” for empty measurements. It does not issue controller commands or mutate run records.
