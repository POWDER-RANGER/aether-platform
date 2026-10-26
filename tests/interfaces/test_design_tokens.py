"""Design tokens: tokens.css matches tokens.json, every declared contrast pair passes."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("build_tokens", ROOT / "scripts" / "brand" / "build_tokens.py")
bt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bt)


def test_tokens_css_in_sync():
    assert (ROOT / "interfaces" / "shared" / "design" / "tokens.css").read_text(encoding="utf-8") == bt.render_css(
        bt.load()
    )


def test_contrast_pairs_pass():
    failed = [r for r in bt.contrast_report(bt.load()) if not r[6]]
    assert not failed, failed


def test_contrast_reference_values():
    # Values recorded in docs/vision/BRAND.md section 2.
    assert round(bt.contrast("#e9e3d9", "#150809"), 2) == 15.37
    assert round(bt.contrast("#c7303a", "#150809"), 2) == 3.65


def test_status_vocabulary_matches_project():
    # Project instructions section 10: exactly six evidence classifications.
    labels = [v["label"] for v in bt.load()["status"].values()]
    assert labels == [
        "VERIFIED",
        "PARTIALLY VERIFIED",
        "UNVERIFIED",
        "FAILED",
        "BLOCKED",
        "NOT IMPLEMENTED",
    ]


def test_operational_states_distinct():
    ops = bt.load()["operational"]
    assert len({v["label"] for v in ops.values()}) == len(ops) == 8
