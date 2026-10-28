from __future__ import annotations

import sys

import pytest

from scripts.regression.update_golden import main


def test_golden_update_requires_explicit_review(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["update_golden.py"])
    with pytest.raises(SystemExit):
        main()
