# Scenario run wrapper

Commands:

- Formal run: `python -m aether.cli_ext scenario run SCN-01 --mode research --settings configuration/platform/ENV-02.yaml`
- Screening run without a frozen lock: add `--screening`.
- Report: `python -m aether.cli_ext scenario report SCN-01`.

Formal runs are refused if `evidence/thresholds.lock.json` is absent or `check_frozen()` reports changed scenario files. Screening runs are written with `outcome: screening`, retain owner-entered raw metric values and are excluded from formal research/companion aggregates. The report separates research and companion counts and raw values and does not compute pass/fail. Thresholds remain PROPOSED, NOT FROZEN.
