"""Test the synthetic generality demo (MEE Experiment 2)."""
from __future__ import annotations
import sys
from pathlib import Path
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.synthetic_demo import run_synthetic_demo


def test_synthetic_generality_story():
    res = run_synthetic_demo(n_attempts=3000, seed=1)
    assert res.n_accepted > 0
    # ABC model choice cannot identify a single model.
    assert res.map_prob < 0.5
    # B and C are confounded on the ordinal observable.
    assert abs(res.ca_j["B"] - res.ca_j["C"]) < 0.15
    assert res.ca_j["B"] > 0.55 and res.ca_j["C"] > 0.55
    # EVSI for the quantitative magnitude is positive and substantial.
    assert res.evsi_y2 > 0.1
    # Adding the quantitative observation resolves: C up, B down, degeneracy falls.
    assert res.R_after > res.R_RACH
    assert res.D_after < res.D_RACH
    assert res.ca_j_after["C"] > res.ca_j["C"]
    assert res.ca_j_after["B"] < res.ca_j["B"]
