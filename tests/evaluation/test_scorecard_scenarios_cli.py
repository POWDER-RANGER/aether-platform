from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from aether.cli_ext import main
from aether.evaluation.scenarios import Scenario, check_frozen, freeze, load_scenarios
from aether.evaluation.scorecard import SCORECARD, Ledger, Result


def test_result_validates_status_and_criterion() -> None:
    with pytest.raises(ValueError, match="status"):
        Result("E-01", "PASS", [], "", "evidence")
    with pytest.raises(ValueError, match="unknown criterion"):
        Result("E-99", "VERIFIED", [], "", "evidence")


def test_ledger_defaults_all_unverified_and_keeps_latest(tmp_path) -> None:
    path = tmp_path / "scorecard.jsonl"
    ledger = Ledger(path)
    initial = ledger.latest()
    assert set(initial) == {criterion.id for criterion in SCORECARD}
    assert all(row["status"] == "UNVERIFIED" for row in initial.values())
    ledger.add(Result("E-01", "PARTIALLY VERIFIED", ["run-1"], "first", "evidence/one.json"))
    ledger.add(Result("E-01", "VERIFIED", ["run-2"], "second", "evidence/two.json"))
    assert ledger.latest()["E-01"]["value"] == "second"
    assert ledger.latest()["E-01"]["status"] == "VERIFIED"


def test_all_scenario_yaml_files_load_and_freeze_detects_edit(tmp_path) -> None:
    scenarios = load_scenarios("configuration/scenarios")
    assert len(scenarios) == 9
    assert all(isinstance(item, Scenario) for item in scenarios.values())
    root = tmp_path / "scenarios"
    shutil.copytree("configuration/scenarios", root)
    lock = tmp_path / "thresholds.lock.json"
    freeze(root, lock)
    assert check_frozen(root, lock) == []
    first = sorted(root.glob("*.yaml"))[0]
    first.write_text(first.read_text(encoding="utf-8") + "\n# synthetic edit for freeze test\n", encoding="utf-8")
    assert first.name in check_frozen(root, lock)


def test_cli_scorecard_scenarios_freeze_check_and_record(tmp_path, monkeypatch, capsys) -> None:
    repo = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(tmp_path)
    shutil.copytree(repo / "configuration" / "scenarios", tmp_path / "configuration" / "scenarios")
    assert main(["scorecard"]) == 0
    assert "E-01" in capsys.readouterr().out
    assert main(["scenarios"]) == 0
    assert "SCN-" in capsys.readouterr().out
    assert main(["freeze"]) == 0
    assert main(["check"]) == 0
    assert main(["record", "E-01", "PARTIALLY VERIFIED", "--evidence", "evidence/synthetic.json"]) == 0
    rows = [json.loads(line) for line in (tmp_path / "evidence" / "scorecard.jsonl").read_text().splitlines()]
    assert rows[-1]["criterion"] == "E-01"
    assert rows[-1]["status"] == "PARTIALLY VERIFIED"
