"""Tests for NOV-as-EVSI calibration (MEE Experiment 3)."""
from __future__ import annotations
import sys
from pathlib import Path
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.nov_calibration import run_calibration


def test_nov_evsi_exact_and_calibrated():
    res = run_calibration(n_attempts=500, seed=7)
    assert res.n_accepted > 0
    assert res.exactness, "should have exactness comparisons"
    # (1) cheap EVSI shortcut must equal fresh re-inference (deterministic proxy).
    for label, cheap, reinf in res.exactness:
        assert abs(cheap - reinf) < 1e-6, f"{label}: cheap {cheap} != reinf {reinf}"
    # (2) EVSI must positively predict realised gain across observations.
    assert res.calibration
    import statistics, math
    by_obs = {}
    evsi_of = {}
    for obs, evsi, _tn, real in res.calibration:
        by_obs.setdefault(obs, []).append(real); evsi_of[obs] = evsi
    xs = [evsi_of[o] for o in by_obs]
    ys = [statistics.mean(by_obs[o]) for o in by_obs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
    sx = math.sqrt(sum((a-mx)**2 for a in xs)); sy = math.sqrt(sum((b-my)**2 for b in ys))
    r = cov/(sx*sy) if sx and sy else 0.0
    assert r > 0.5, f"EVSI should predict realised gain (got r={r:.2f})"
