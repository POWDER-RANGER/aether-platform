from __future__ import annotations

import json
import math
import platform
import shutil
import statistics
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if not 0 <= p <= 100:
        raise ValueError("percentile must be in [0, 100]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * p / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize_samples(samples: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(samples),
        "median": statistics.median(samples) if samples else None,
        "p95": percentile(samples, 95),
        "p99": percentile(samples, 99),
        "max": max(samples) if samples else None,
    }


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]


def hardware_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "gpu_query": None,
    }
    executable = shutil.which("nvidia-smi")
    if executable:
        try:
            result = subprocess.run(
                [executable, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
            )
            info["gpu_query"] = result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            info["gpu_query"] = "query_failed"
    return info


def write_evidence(category: str, run_id: str, payload: dict, root: str | Path = "evidence") -> Path:
    if not category or Path(category).is_absolute() or ".." in Path(category).parts:
        raise ValueError("invalid evidence category")
    directory = Path(root) / category
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return path


def _git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=2, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _base_record(tool: str, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "git_rev": _git_revision(),
        "hardware": hardware_info(),
        "raw_samples": [],
    }


def run_tick(duration_s: float, root: str | Path = "evidence") -> dict:
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    from aether.control.adapters import DryRunAdapter
    from aether.control.governor import Governor
    from aether.control.intent_log import IntentLog
    from aether.control.motor import MotorModel, MotorProfile
    from aether.control.policy import GovernorConfig
    from aether.control.safety import KillSwitch

    run_id = new_run_id()
    record = _base_record("E-06 tick", run_id)
    intervals: list[float] = []
    with __import__("tempfile").TemporaryDirectory(prefix="aether-tick-") as temp_dir:
        log = IntentLog(Path(temp_dir) / "governor.jsonl")
        governor = Governor(
            GovernorConfig(require_focus=False),
            MotorModel(MotorProfile(humanize=False), seed=1),
            DryRunAdapter(keep=1),
            log,
            KillSwitch(),
            focus=lambda: True,
        )
        period = 1.0 / 120.0
        started = time.perf_counter()
        previous = started
        try:
            while time.perf_counter() - started < duration_s:
                now = time.perf_counter()
                intervals.append((now - previous) * 1000)
                previous = now
                governor.tick()
                remaining = period - (time.perf_counter() - now)
                if remaining > 0:
                    time.sleep(remaining)
        finally:
            governor.close()
    record["duration_s"] = duration_s
    record["target_hz"] = 120
    record["interval_ms"] = summarize_samples(intervals[1:])
    record["raw_samples"] = intervals[1:]
    record["evidence_path"] = str(write_evidence("E-06", run_id, record, root))
    return record


def run_capture(duration_s: float, process: str, backend: str, root: str | Path = "evidence") -> dict:
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if not process:
        raise ValueError("process is required")
    if backend not in {"dxgi", "winrt"}:
        raise ValueError("backend must be dxgi or winrt")
    import dxcam

    from aether.capture.screen import find_window_rect

    region = find_window_rect(process)
    camera = dxcam.create(output_color="RGB", backend=backend)
    run_id = new_run_id()
    record = _base_record("E-07 capture", run_id)
    latencies: list[float] = []
    none_frames = 0
    frames = 0
    resolution = None
    started = time.perf_counter()
    try:
        while time.perf_counter() - started < duration_s:
            tick = time.perf_counter()
            image = camera.grab(region=region)
            latencies.append((time.perf_counter() - tick) * 1000)
            if image is None:
                none_frames += 1
            else:
                frames += 1
                resolution = [int(image.shape[1]), int(image.shape[0])]
    finally:
        stop = getattr(camera, "stop", None)
        if callable(stop):
            stop()
    record.update(
        {
            "process": process,
            "backend": backend,
            "duration_s": duration_s,
            "frames": frames,
            "none_frames": none_frames,
            "resolution": resolution,
            "grab_latency_ms": summarize_samples(latencies),
            "raw_samples": latencies,
        }
    )
    record["evidence_path"] = str(write_evidence("E-07", run_id, record, root))
    return record


def _reflex_cadence(duration_s: float, supervisor_delay_s: float | None) -> dict:
    import numpy as np

    from aether.perception.frame_buffer import FrameBuffer
    from aether.perception.pipeline import PerceptionPipeline
    from aether.runtime.events import EventBus
    from prrex.backends.base import NullReflex, SupervisorOutput
    from prrex.runtime import ReflexLoop, SupervisorLoop
    from prrex.supervisor.planner import Planner

    class FakeClient:
        def __init__(self):
            self.sent: list[float] = []

        def send_frames(self, frames, **kwargs):
            self.sent.append(time.perf_counter())

    class SlowSupervisor:
        def assess(self, *args):
            if supervisor_delay_s:
                time.sleep(supervisor_delay_s)
            return SupervisorOutput(None, None, [], "synthetic delay benchmark", 0.0, 0.0, "synthetic-slow")

    bus = EventBus()
    buffer = FrameBuffer(240)
    client = FakeClient()
    perception = PerceptionPipeline(bus, {}, {})
    planner = Planner()
    reflex = ReflexLoop(bus, buffer, NullReflex(), client, planner, perception, None, 16, 0.5)
    supervisor = None
    stop = threading.Event()
    image = np.zeros((256, 256, 3), dtype=np.uint8)  # synthetic benchmark input, not captured data

    def produce():
        while not stop.is_set():
            buffer.push(time.monotonic(), image, "synthetic")
            time.sleep(1 / 120)

    producer = threading.Thread(target=produce, daemon=True)
    if supervisor_delay_s is not None:
        supervisor = SupervisorLoop(bus, buffer, SlowSupervisor(), planner, perception, {}, None, period_s=0.01)
    producer.start()
    reflex.start()
    if supervisor:
        supervisor.start()
    started = time.perf_counter()
    try:
        time.sleep(duration_s)
    finally:
        stop.set()
        if supervisor:
            supervisor.stop()
        reflex.stop()
        producer.join(timeout=1)
    elapsed = time.perf_counter() - started
    intervals = [(b - a) * 1000 for a, b in zip(client.sent, client.sent[1:])]
    cadence = (len(client.sent) - 1) / elapsed if len(client.sent) > 1 else 0.0
    return {
        "elapsed_s": elapsed,
        "chunk_count": len(client.sent),
        "cadence_hz": cadence,
        "interval_ms": summarize_samples(intervals),
        "timestamps_monotonic": client.sent,
        "interval_samples_ms": intervals,
        "input": "synthetic 256x256 RGB frames",
        "supervisor_sleep_s": supervisor_delay_s,
    }


def run_nonblocking(duration_s: float, supervisor_sleep_s: float, root: str | Path = "evidence") -> dict:
    if duration_s <= 0 or not 0.5 <= supervisor_sleep_s <= 5:
        raise ValueError("duration must be positive and supervisor sleep must be between 0.5 and 5 seconds")
    baseline = _reflex_cadence(duration_s, None)
    loaded = _reflex_cadence(duration_s, supervisor_sleep_s)
    change = (
        ((loaded["cadence_hz"] - baseline["cadence_hz"]) / baseline["cadence_hz"]) * 100
        if baseline["cadence_hz"]
        else None
    )
    run_id = new_run_id()
    record = _base_record("E-08 non-blocking", run_id)
    record.update({"baseline": baseline, "with_supervisor": loaded, "cadence_change_percent": change})
    record["evidence_path"] = str(write_evidence("E-08", run_id, record, root))
    return record



def run_inference(backend: str, calls: int = 5, concurrent: bool = False, root: str | Path = "evidence") -> dict:
    if backend not in {"ollama", "nitrogen"}:
        raise ValueError("backend must be ollama or nitrogen")
    if calls < 1:
        raise ValueError("calls must be at least 1")
    import numpy as np

    image = np.zeros((256, 256, 3), dtype=np.uint8)  # synthetic RGB input, not captured data
    selected = ["ollama", "nitrogen"] if concurrent else [backend]
    results: dict[str, dict] = {}
    gpu_samples: list[int] = []
    gpu_stop = threading.Event()
    smi = shutil.which("nvidia-smi")

    def poll_gpu() -> None:
        if not smi:
            return
        while not gpu_stop.is_set():
            try:
                result = subprocess.run(
                    [smi, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=True,
                )
                gpu_samples.extend(int(line.strip()) for line in result.stdout.splitlines() if line.strip().isdigit())
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
            gpu_stop.wait(0.25)

    def measure(name: str) -> None:
        started = time.perf_counter()
        try:
            if name == "ollama":
                from prrex.backends.ollama_vlm import OllamaSupervisor

                instance = OllamaSupervisor()
                call = lambda: instance.assess({"synthetic": image}, "synthetic benchmark image", None, [])
            else:
                from prrex.backends.nitrogen_reflex import NitrogenReflex

                instance = NitrogenReflex()
                call = lambda: instance.act(image, None, 16)
            call()
            cold_ms = (time.perf_counter() - started) * 1000
            warm = []
            for _ in range(calls):
                tick = time.perf_counter()
                call()
                warm.append((time.perf_counter() - tick) * 1000)
            results[name] = {
                "status": "completed",
                "cold_start_ms": cold_ms,
                "warm_latency_ms": summarize_samples(warm),
                "warm_samples_ms": warm,
                "calls": calls,
                "input": "synthetic 256x256 RGB image",
            }
            close = getattr(instance, "close", None)
            if callable(close):
                close()
        except Exception as exc:
            results[name] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "calls": 0,
                "input": "synthetic 256x256 RGB image",
            }

    poller = threading.Thread(target=poll_gpu, daemon=True)
    poller.start()
    workers = [threading.Thread(target=measure, args=(name,)) for name in selected]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    gpu_stop.set()
    poller.join(timeout=1)
    run_id = new_run_id()
    record = _base_record("inference", run_id)
    record.update(
        {
            "backend": backend,
            "concurrent": concurrent,
            "results": results,
            "gpu_memory_used_mib_samples": gpu_samples,
            "gpu_memory_poll": "available" if smi else "nvidia-smi unavailable",
            "gpu_memory_peak_mib": max(gpu_samples, default=None),
        }
    )
    record["evidence_path"] = str(write_evidence("inference", run_id, record, root))
    return record


def verify_run(run_dir: str | Path, root: str | Path = "evidence") -> dict:
    run = Path(run_dir)
    run_id = run.name
    failures: list[str] = []
    manifest_path = run / "manifest.json"
    if not manifest_path.is_file():
        failures.append("manifest.json missing")
        manifest = {}
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"manifest.json invalid: {exc}")
            manifest = {}

    stream_results = {}
    streams_dir = run / "streams"
    if streams_dir.is_dir():
        for path in sorted(streams_dir.glob("*.jsonl")):
            times = []
            try:
                for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if line.strip():
                        row = json.loads(line)
                        times.append(float(row["t_mono"]))
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                failures.append(f"{path.name} invalid: {exc}")
            monotonic = all(right >= left for left, right in zip(times, times[1:]))
            if not monotonic:
                failures.append(f"{path.name} timestamps are not monotonic")
            gaps = [right - left for left, right in zip(times, times[1:])]
            stream_results[path.stem] = {
                "count": len(times),
                "monotonic": monotonic,
                "largest_gap_s": max(gaps, default=0.0),
            }
    else:
        failures.append("streams directory missing")

    index_path = run / "frames.jsonl"
    frames_dir = run / "frames"
    indexed = []
    if index_path.is_file():
        try:
            indexed = [json.loads(line) for line in index_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"frames.jsonl invalid: {exc}")
    else:
        failures.append("frames.jsonl missing")
    frame_times = [float(row["t_mono"]) for row in indexed if "t_mono" in row]
    if not all(right >= left for left, right in zip(frame_times, frame_times[1:])):
        failures.append("frames.jsonl timestamps are not monotonic")
    indexed_files = {f"{int(row['seq']):08d}.jpg" for row in indexed if "seq" in row}
    disk_files = {path.name for path in frames_dir.glob("*.jpg")} if frames_dir.is_dir() else set()
    if not frames_dir.is_dir():
        failures.append("frames directory missing")
    frames_match = indexed_files == disk_files
    if not frames_match:
        failures.append("frames.jsonl index does not match JPEG files on disk")

    events_path = run / "events.jsonl"
    event_count = 0
    if events_path.is_file():
        try:
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    json.loads(line)
                    event_count += 1
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"events.jsonl invalid: {exc}")
    else:
        failures.append("events.jsonl missing")

    verdict = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": "VERIFIED" if not failures else "FAILED",
        "manifest_present": manifest_path.is_file(),
        "streams": stream_results,
        "frames_match": frames_match,
        "frame_count": len(indexed),
        "event_count": event_count,
        "failures": failures,
    }
    verdict_path = write_evidence("E-10", run_id, verdict, root)
    verdict["verdict_path"] = str(verdict_path)
    return verdict
