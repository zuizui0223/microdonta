from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_boundary_submission_gate_passes_current_candidate():
    completed = subprocess.run(
        [sys.executable, "paper/check_boundary_submission.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
    assert "candidate venue: Ecology Letters Perspective" in completed.stdout
    assert "mechanistic evidence axes: distinct/non-monotone" in completed.stdout
    assert "mechanistic evidence literature audit: pass" in completed.stdout
    assert "paper separation: pass" in completed.stdout
