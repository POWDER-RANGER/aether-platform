from pathlib import Path
from scripts.docs.check_docs import check
from scripts.docs.build_index import build

def test_checker_rules(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "src/x").mkdir(parents=True)
    (tmp_path / "src/x/a.py").write_text("pass")
    (tmp_path / "README.md").write_text("[guide](docs/guide.md)")
    valid = "Status: VERIFIED\n| Path | Description |\n|---|---|\n| " + chr(96) + "src/x/a.py" + chr(96) + " | exists |"
    (tmp_path / "docs/guide.md").write_text(valid)
    assert check(tmp_path) == []

    proposed_word = "PROPOSED "
    threshold_word = "threshold: 4"
    invalid = "Status: GREEN\n[bad](missing.md)\n| Path | Description |\n|---|---|\n| "
    invalid += chr(96) + "src/missing.py" + chr(96) + " | missing |\n"
    invalid += proposed_word
    invalid += threshold_word
    (tmp_path / "docs/guide.md").write_text(invalid)
    errors = check(tmp_path)
    assert any("invalid status" in error for error in errors)
    assert any("broken link" in error for error in errors)
    assert any("cited table path" in error for error in errors)
    assert any("NOT FROZEN" in error for error in errors)


def test_index_read_only(tmp_path):
    path = tmp_path / "evidence/E-01/a.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"run_id":"r1","timestamp_utc":"2026-10-28T00:00:00Z",'
        '"criterion":"E-01","status":"VERIFIED"}'
    )
    before = path.read_bytes()
    result = build(tmp_path)
    assert "r1" in result and "VERIFIED" in result
    assert path.read_bytes() == before
