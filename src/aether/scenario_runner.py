from __future__ import annotations

import json
import os
import subprocess
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from aether.evaluation.scenarios import check_frozen, load_scenarios

OUTCOMES = {
    "VERIFIED",
    "PARTIALLY VERIFIED",
    "UNVERIFIED",
    "FAILED",
    "BLOCKED",
    "NOT IMPLEMENTED",
}


def run_scenario(
    scenario_id: str,
    mode: str,
    settings: str,
    screening: bool = False,
    root: str | Path = "configuration/scenarios",
    lock: str | Path = "evidence/thresholds.lock.json",
    evidence_root: str | Path = "evidence/scenarios",
    input_fn: Callable[[str], str] = input,
    pipeline_runner: Callable[[list[str]], int] | None = None,
) -> dict:
    scenarios = load_scenarios(root)
    if scenario_id not in scenarios:
        raise ValueError(f"unknown scenario: {scenario_id}")
    scenario = scenarios[scenario_id]
    if mode not in scenario.modes:
        raise ValueError(f"{mode} mode is not allowed for {scenario_id}")
    if scenario.kind == "formal" and not screening:
        if not Path(lock).is_file():
            raise RuntimeError("formal scenario blocked: no threshold/scenario lock exists; use --screening for a non-formal run")
        changed = check_frozen(root, lock)
        if changed:
            raise RuntimeError(f"formal scenario blocked: frozen scenario files changed: {changed}")

    print(scenario.setup)
    if input_fn("Restore the start state and confirm with 'y': ").strip().lower() != "y":
        raise RuntimeError("scenario start was not confirmed")

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    old_id = os.environ.get("AETHER_SOAK_RUN_ID")
    os.environ["AETHER_SOAK_RUN_ID"] = run_id
    try:
        args = [
            "companion",
            "--settings",
            settings,
            "--scenario",
            scenario_id,
            "--mode",
            mode,
            "--environment",
            scenario.environment,
            "--duration",
            str(scenario.time_limit_s),
        ]
        if pipeline_runner is None:
            from aether.cli_ext import main

            pipeline_runner = main
        exit_code = pipeline_runner(args)
    finally:
        if old_id is None:
            os.environ.pop("AETHER_SOAK_RUN_ID", None)
        else:
            os.environ["AETHER_SOAK_RUN_ID"] = old_id

    metrics = {}
    for metric in scenario.metrics:
        metrics[metric] = input_fn(f"{metric}: ")
    reported_outcome = input_fn("Outcome (VERIFIED | PARTIALLY VERIFIED | UNVERIFIED | FAILED | BLOCKED | NOT IMPLEMENTED): ").strip()
    if reported_outcome not in OUTCOMES:
        raise ValueError(f"invalid outcome label: {reported_outcome}")
    outcome = "screening" if screening else reported_outcome
    notes = input_fn("Notes: ")

    try:
        git_rev = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        git_rev = "unknown"
    try:
        from aether.bench import hardware_info

        hardware = hardware_info()
    except ImportError:
        hardware = {"status": "unavailable"}
    record = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_rev": git_rev,
        "hardware": hardware,
        "scenario": scenario_id,
        "mode": mode,
        "environment": scenario.environment,
        "formal": scenario.kind == "formal" and not screening,
        "screening": screening,
        "outcome": outcome,
        "reported_outcome": reported_outcome,
        "metrics": metrics,
        "raw_samples": {"owner_entered_metrics": metrics},
        "notes": notes,
        "companion_exit_code": exit_code,
        "time_limit_s": scenario.time_limit_s,
    }
    directory = Path(evidence_root) / scenario_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    record["evidence_path"] = str(path)
    return record


def scenario_report(
    scenario_id: str,
    evidence_root: str | Path = "evidence/scenarios",
) -> dict:
    directory = Path(evidence_root) / scenario_id
    runs = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if record.get("scenario") == scenario_id:
                runs.append(record)
    grouped = {}
    for mode in ("research", "companion"):
        selected = [run for run in runs if run.get("mode") == mode and not run.get("screening")]
        grouped[mode] = {
            "count": len(selected),
            "raw_values": [
                {"run_id": run.get("run_id"), "metrics": run.get("metrics", {}), "outcome": run.get("outcome")}
                for run in selected
            ],
        }
    screening = [run for run in runs if run.get("screening")]
    return {
        "scenario": scenario_id,
        "research": grouped["research"],
        "companion": grouped["companion"],
        "screening_count": len(screening),
        "screening_runs": [run.get("run_id") for run in screening],
        "note": "Raw values only. No pass/fail is computed because thresholds are not frozen.",
    }
