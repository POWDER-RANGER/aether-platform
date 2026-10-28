from __future__ import annotations

"""Owner workstation soak harness; hardware path is UNVERIFIED until an MSI run is recorded."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=2, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _stop_child(child: subprocess.Popen, grace_s: float = 10.0) -> None:
    if child.poll() is not None:
        return
    try:
        if os.name == "nt" and hasattr(signal, "CTRL_BREAK_EVENT"):
            child.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            child.send_signal(signal.SIGINT)
        child.wait(timeout=grace_s)
    except (OSError, subprocess.TimeoutExpired):
        child.terminate()
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


def _has_stall_event(events_path: Path) -> bool:
    if not events_path.is_file():
        return False
    try:
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("topic") == "recovery.stall":
                return True
    except (OSError, json.JSONDecodeError):
        return False
    return False


def run_one(settings: str, minutes: float, heartbeat_timeout: float, evidence_root: Path, run_root: Path) -> dict:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    work = evidence_root / run_id
    work.mkdir(parents=True, exist_ok=True)
    heartbeat = work / "heartbeat.json"
    dump_request = work / "dump.request"
    stacks = work / "faulthandler.log"
    stdout_path = work / "stdout.log"
    stderr_path = work / "stderr.log"
    events_path = run_root / run_id / "events.jsonl"

    env = os.environ.copy()
    env.update(
        {
            "PYTHONFAULTHANDLER": "1",
            "AETHER_SOAK_RUN_ID": run_id,
            "AETHER_RECORDING_ROOT": str(run_root),
            "AETHER_HEARTBEAT_PATH": str(heartbeat),
            "AETHER_DUMP_REQUEST": str(dump_request),
            "AETHER_FAULTHANDLER_PATH": str(stacks),
        }
    )
    command = [sys.executable, "-m", "aether.cli_ext", "companion", "--settings", settings]
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    started_wall = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    classification = "completed"
    hang_age = None
    exit_code = None
    heartbeat_samples = []
    last_heartbeat = None

    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        deadline = started + minutes * 60
        try:
            while child.poll() is None:
                now = time.monotonic()
                if now >= deadline:
                    _stop_child(child)
                    break
                if heartbeat.exists():
                    age = time.time() - heartbeat.stat().st_mtime
                    try:
                        heartbeat_data = json.loads(heartbeat.read_text(encoding="utf-8"))
                        sample = heartbeat_data.get("t_mono")
                        if sample is not None and sample != last_heartbeat:
                            heartbeat_samples.append(sample)
                            last_heartbeat = sample
                    except (OSError, json.JSONDecodeError):
                        pass
                else:
                    age = now - started
                if age > heartbeat_timeout:
                    classification = "hung"
                    hang_age = age
                    dump_request.write_text("dump stacks", encoding="utf-8")
                    time.sleep(0.5)
                    _stop_child(child, grace_s=2.0)
                    break
                time.sleep(0.25)
        finally:
            if child.poll() is None:
                _stop_child(child)
            exit_code = child.poll()

    if classification == "completed" and exit_code not in (0, -signal.SIGINT):
        classification = f"crashed({exit_code})"
    elif classification == "completed" and _has_stall_event(events_path):
        classification = "stalled"

    result = {
        "run_id": run_id,
        "timestamp_utc": started_wall,
        "git_rev": _git_revision(),
        "command": command,
        "minutes_requested": minutes,
        "heartbeat_timeout_s": heartbeat_timeout,
        "wall_time_s": time.monotonic() - started,
        "exit_code": exit_code,
        "classification": classification,
        "heartbeat_age_at_stop_s": hang_age,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "faulthandler": str(stacks),
        "events": str(events_path),
        "recording_present": events_path.is_file(),
        "raw_samples": {"heartbeat_t_mono": heartbeat_samples},
    }
    try:
        from aether.bench import hardware_info

        result["hardware"] = hardware_info()
    except ImportError:
        result["hardware"] = {"status": "unavailable"}
    result_path = evidence_root / f"{run_id}.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    result["evidence_path"] = str(result_path)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run and diagnose an ENV-01 companion soak session.")
    parser.add_argument("--settings", required=True)
    parser.add_argument("--minutes", type=float, default=30)
    parser.add_argument("--heartbeat-timeout", type=float, default=10)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/E-09"))
    parser.add_argument("--run-root", type=Path, default=Path("runs"))
    args = parser.parse_args(argv)
    if args.minutes <= 0 or args.heartbeat_timeout <= 0 or args.repeat < 1:
        parser.error("minutes, heartbeat-timeout and repeat must be positive")

    results = [
        run_one(args.settings, args.minutes, args.heartbeat_timeout, args.evidence_root, args.run_root)
        for _ in range(args.repeat)
    ]
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_rev": _git_revision(),
        "repeat": args.repeat,
        "classifications": {
            label: sum(result["classification"] == label for result in results)
            for label in sorted({result["classification"] for result in results})
        },
        "runs": results,
    }
    summary_path = args.evidence_root / f"summary-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({**summary, "summary_path": str(summary_path)}, indent=2))
    return 0 if all(result["classification"] == "completed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
