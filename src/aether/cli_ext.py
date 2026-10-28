# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Draft CLI for the new subsystems: python -m aether.cli_ext <command>

  serve      run the read-only Command Center (127.0.0.1)
  runs       list recordings
  replay     summarise a recording
  scorecard  print E-01..E-10 latest status
  record     add a scorecard result (status per §10, evidence path required)
  scenarios  list SCN/DG definitions
  freeze     freeze scenario thresholds (owner action)
  check      verify scenario files unchanged since freeze
  companion  run capture -> perception -> PR-REX loops -> Governor (REFINE: wire key + governor serve)
Merge into aether/cli.py once refined.
"""

from __future__ import annotations

import argparse
import json
import sys

from aether.evaluation import scenarios as scn
from aether.evaluation.scorecard import SCORECARD, Ledger, Result
from aether.recording.replay import list_runs, summarize
from aether.runtime.config import load_platform_settings
from aether.runtime.events import EventBus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="aether.cli_ext")
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("serve")
    s.add_argument("--settings")
    s.add_argument("--runs", default="runs")
    s = sp.add_parser("runs")
    s.add_argument("--root", default="runs")
    s = sp.add_parser("replay")
    s.add_argument("run_dir")
    sp.add_parser("scorecard")
    s = sp.add_parser("record")
    s.add_argument("criterion", choices=[c.id for c in SCORECARD])
    s.add_argument("status")
    s.add_argument("--runs", nargs="*", default=[])
    s.add_argument("--value", default="")
    s.add_argument("--evidence", required=True)
    s.add_argument("--note", default="")
    sp.add_parser("scenarios")
    sp.add_parser("freeze")
    sp.add_parser("check")
    s = sp.add_parser("companion")
    s.add_argument("--settings", required=True)
    s.add_argument("--goal")
    s.add_argument("--scenario")
    bench = sp.add_parser("bench")
    bench_sub = bench.add_subparsers(dest="bench_name", required=True)
    tick = bench_sub.add_parser("tick")
    tick.add_argument("--seconds", type=float, default=600)
    tick.add_argument("--evidence-root", default="evidence")
    capture = bench_sub.add_parser("capture")
    capture.add_argument("--seconds", type=float, default=60)
    capture.add_argument("--process", required=True)
    capture.add_argument("--backend", choices=["dxgi", "winrt"], default="dxgi")
    capture.add_argument("--evidence-root", default="evidence")
    nonblocking = bench_sub.add_parser("nonblocking")
    nonblocking.add_argument("--seconds", type=float, default=10)
    nonblocking.add_argument("--supervisor-sleep", type=float, default=1.0)
    nonblocking.add_argument("--evidence-root", default="evidence")
    inference = bench_sub.add_parser("inference")
    inference.add_argument("--backend", choices=["ollama", "nitrogen"], default="ollama")
    inference.add_argument("--calls", type=int, default=5)
    inference.add_argument("--concurrent", action="store_true")
    inference.add_argument("--evidence-root", default="evidence")
    verify = sp.add_parser("verify-run")
    verify.add_argument("run_dir")
    verify.add_argument("--evidence-root", default="evidence")
    a = ap.parse_args(argv)

    if a.cmd == "serve":
        from aether.server.app import CommandCenter

        st = load_platform_settings(a.settings)
        cc = CommandCenter(EventBus(), None, a.runs, Ledger(), st.server.host, st.server.port)
        print(f"Command Center on http://{st.server.host}:{st.server.port}  (read-only)")
        cc.serve_forever()
    elif a.cmd == "runs":
        print(json.dumps(list_runs(a.root), indent=2))
    elif a.cmd == "replay":
        print(json.dumps(summarize(a.run_dir), indent=2))
    elif a.cmd == "scorecard":
        for cid, r in Ledger().latest().items():
            print(f"{cid}  {r['status']:<20} {r['title']}")
    elif a.cmd == "record":
        Ledger().add(Result(a.criterion, a.status, a.runs, a.value, a.evidence, a.note))
    elif a.cmd == "scenarios":
        for sid, sc in scn.load_scenarios().items():
            print(f"{sid}  [{sc.kind}] {sc.environment}  {sc.title}")
    elif a.cmd == "freeze":
        print(json.dumps(scn.freeze(), indent=2))
    elif a.cmd == "check":
        ch = scn.check_frozen()
        print("unchanged" if not ch else f"CHANGED since freeze: {ch}")
        return 1 if ch else 0
    elif a.cmd == "companion":
        return _companion(a)
    elif a.cmd == "bench":
        from aether import bench as bench_tools

        if a.bench_name == "tick":
            result = bench_tools.run_tick(a.seconds, a.evidence_root)
        elif a.bench_name == "capture":
            result = bench_tools.run_capture(a.seconds, a.process, a.backend, a.evidence_root)
        elif a.bench_name == "nonblocking":
            result = bench_tools.run_nonblocking(a.seconds, a.supervisor_sleep, a.evidence_root)
        else:
            result = bench_tools.run_inference(a.backend, a.calls, a.concurrent, a.evidence_root)
        print(json.dumps(result, indent=2, default=str))
    elif a.cmd == "verify-run":
        from aether.bench import verify_run

        result = verify_run(a.run_dir, a.evidence_root)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result["status"] == "VERIFIED" else 1
    return 0


def _companion(a) -> int:
    """End-to-end wiring. REFINE: key loading (control.settings), Governor process start, player goal UI, clean shutdown."""
    import faulthandler
    import os
    import time
    from pathlib import Path

    from aether.capture.source import DxcamSource
    from aether.perception.frame_buffer import FrameBuffer
    from aether.perception.pipeline import PerceptionPipeline
    from aether.recording.session import RecordingSession
    from aether.runtime.identity import RunIdentity
    from aether.runtime.lifecycle import Runtime
    from prrex.backends.base import make_reflex, make_supervisor
    from prrex.runtime import ReflexLoop, SupervisorLoop, build_client
    from prrex.supervisor.planner import Planner

    st = load_platform_settings(a.settings)
    bus = EventBus()
    reflex = make_reflex(st.backends.reflex, **st.backends.reflex_options)
    sup = make_supervisor(st.backends.supervisor, **st.backends.supervisor_options)
    ident = RunIdentity.create(
        Path.cwd(),
        mode=st.mode,
        environment=st.environment,
        scenario=a.scenario,
        backends={"reflex": reflex.name, "supervisor": sup.name},
        settings_sha256=st.sha256(),
    )
    ident.run_id = os.environ.get("AETHER_SOAK_RUN_ID", ident.run_id)
    recording_root = os.environ.get("AETHER_RECORDING_ROOT", st.recording.root)
    rec = RecordingSession(recording_root, ident, bus, st.recording.frame_every_n, st.recording.jpeg_quality)
    heartbeat_path = Path(os.environ["AETHER_HEARTBEAT_PATH"]) if os.environ.get("AETHER_HEARTBEAT_PATH") else None
    dump_request = Path(os.environ["AETHER_DUMP_REQUEST"]) if os.environ.get("AETHER_DUMP_REQUEST") else None
    fault_handle = None
    if os.environ.get("AETHER_FAULTHANDLER_PATH"):
        fault_path = Path(os.environ["AETHER_FAULTHANDLER_PATH"])
        fault_path.parent.mkdir(parents=True, exist_ok=True)
        fault_handle = fault_path.open("a", encoding="utf-8")
        faulthandler.enable(file=fault_handle, all_threads=True)
    buf = FrameBuffer(int(st.capture.target_fps * st.capture.buffer_seconds))
    perc = PerceptionPipeline(bus, st.perception.rois, st.perception.readers)
    planner = Planner()
    key = Path("keys/intent.key").read_bytes()  # REFINE: use the existing key path from control settings
    client = build_client(st.governor_endpoint, key)
    rt = Runtime(bus)
    rt.add(DxcamSource(bus, buf, st.capture.process_name, st.capture.target_fps))
    rt.add(
        ReflexLoop(
            bus,
            buf,
            reflex,
            client,
            planner,
            perc,
            rec,
            st.backends.chunk_len,
            st.backends.execute_fraction,
            st.capture.reflex_size,
        )
    )
    rt.add(SupervisorLoop(bus, buf, sup, planner, perc, st.perception.rois, a.goal, st.backends.supervisor_period_s))
    rec.start()
    try:
        rt.start()
        import time

        while True:
            if heartbeat_path:
                heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
                heartbeat_path.write_text(
                    json.dumps({"t_wall": time.time(), "t_mono": time.monotonic()}), encoding="utf-8"
                )
            if dump_request and dump_request.exists() and fault_handle:
                faulthandler.dump_traceback_later(0.1, repeat=False, file=fault_handle)
                time.sleep(0.2)
                faulthandler.cancel_dump_traceback_later()
                dump_request.unlink(missing_ok=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        rt.stop()
        rec.stop()
        client.close()
        if fault_handle:
            faulthandler.cancel_dump_traceback_later()
            fault_handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
