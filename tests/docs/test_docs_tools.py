from scripts.docs.build_index import build
from scripts.docs.check_docs import check


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
    path.write_text('{"run_id":"r1","timestamp_utc":"2026-10-28T00:00:00Z","criterion":"E-01","status":"VERIFIED"}')
    before = path.read_bytes()
    result = build(tmp_path)
    assert "r1" in result and "VERIFIED" in result
    assert path.read_bytes() == before


def test_index_derives_run_id_from_manifest_and_evidence_path(tmp_path):
    path = tmp_path / "evidence" / "SCN-02" / "run-02" / "stdout.txt"
    path.parent.mkdir(parents=True)
    path.write_text("synthetic log")
    direct = tmp_path / "evidence" / "E-10" / "run-10.json"
    direct.parent.mkdir(parents=True)
    direct.write_text("{}")
    result = build(tmp_path)
    assert "run-02" in result
    assert "run-10" in result
    assert "SCN-02" in result
    assert "E-10" in result


def test_status_label_with_trailing_prose_rejected(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/p.md").write_text("**Status:** NOT IMPLEMENTED (pending tooling)\n")
    assert any("invalid status" in e for e in check(tmp_path))
    (tmp_path / "docs/p.md").write_text("**Status:** NOT IMPLEMENTED\nPending tooling.\n")
    assert check(tmp_path) == []
