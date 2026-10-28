from __future__ import annotations

import json

import pytest

from aether.scenario_runner import run_scenario, scenario_report


def test_formal_scenario_refuses_missing_lock(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="no threshold/scenario lock"):
        run_scenario(
            "SCN-01",
            "research",
            "configuration/platform/ENV-02.yaml",
            root="configuration/scenarios",
            lock=tmp_path / "missing.lock",
            input_fn=lambda _prompt: "y",
            pipeline_runner=lambda _args: 0,
        )


def test_screening_run_collects_raw_metrics_and_is_not_formal(tmp_path) -> None:
    answers = iter(["y", "phase-ok", "objective-ok", "0", "0", "VERIFIED", "synthetic notes"])
    called = []

    def fake_runner(args):
        called.extend(args)
        return 0

    result = run_scenario(
        "SCN-01",
        "research",
        "configuration/platform/ENV-02.yaml",
        screening=True,
        evidence_root=tmp_path,
        input_fn=lambda _prompt: next(answers),
        pipeline_runner=fake_runner,
    )
    assert result["screening"] is True
    assert result["formal"] is False
    assert result["outcome"] == "screening"
    assert result["reported_outcome"] == "VERIFIED"
    assert result["metrics"]["phase_accuracy"] == "phase-ok"
    assert "--duration" in called
    assert (tmp_path / "SCN-01" / f"{result['run_id']}.json").is_file()


def test_report_keeps_research_and_companion_separate(tmp_path) -> None:
    directory = tmp_path / "SCN-01"
    directory.mkdir()
    for mode, run_id, value in [("research", "r1", "raw-r"), ("companion", "c1", "raw-c")]:
        (directory / f"{run_id}.json").write_text(
            json.dumps({"scenario": "SCN-01", "mode": mode, "run_id": run_id,
                        "metrics": {"metric": value}, "outcome": "UNVERIFIED"}),
            encoding="utf-8",
        )
    (directory / "screening.json").write_text(
        json.dumps({"scenario": "SCN-01", "mode": "research", "run_id": "screen",
                    "screening": True, "metrics": {"metric": "screen-value"}, "outcome": "screening"}),
        encoding="utf-8",
    )
    report = scenario_report("SCN-01", tmp_path)
    assert report["research"]["count"] == 1
    assert report["screening_count"] == 1
    assert report["companion"]["count"] == 1
    assert report["research"]["raw_values"][0]["metrics"]["metric"] == "raw-r"
    assert "No pass/fail" in report["note"]


def test_formal_scenario_refuses_changed_frozen_file(tmp_path) -> None:
    import shutil

    from aether.evaluation.scenarios import freeze

    root = tmp_path / "scenarios"
    shutil.copytree("configuration/scenarios", root)
    lock = tmp_path / "thresholds.lock.json"
    freeze(root, lock)
    target = sorted(root.glob("*.yaml"))[0]
    target.write_text(target.read_text(encoding="utf-8") + "\n# modified after freeze\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="frozen scenario files changed"):
        run_scenario(
            "SCN-01",
            "research",
            "configuration/platform/ENV-02.yaml",
            root=root,
            lock=lock,
            input_fn=lambda _prompt: "y",
            pipeline_runner=lambda _args: 0,
        )
