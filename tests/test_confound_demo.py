"""Smoke + behaviour tests for the MEE confound demonstration (Experiment 1)."""
from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from causal_model.confound_demo import run_confound_demo


def test_confound_demo_story_holds():
    """The money figure's claims must hold: S2/S3 confounded, then resolved."""
    res = run_confound_demo(backend="proxy", n_attempts=400, seed=7)

    assert res.n_accepted > 0
    # (A) model choice cannot identify a clear winner.
    assert res.map_prob < 0.5, "MAP model should be far from certain under confounding"

    # (B) S2 and S3 are confounded: both admissible and close to each other.
    s2 = res.ca_j["selfing_syndrome_active"]
    s3 = res.ca_j["island_isolation_common_cause"]
    assert abs(s2 - s3) < 0.2, "S2 and S3 should be near-indistinguishable on ordinal y_obs"

    # (D) adding the quantitative confound-breaker resolves it: R up, S3 up, S2 down.
    assert res.resolving_candidate is not None
    assert res.R_after > res.R_RACH, "resolvability must increase after the added observation"
    assert res.D_after < res.D_RACH, "degeneracy must fall after the added observation"
    assert res.ca_j_after["island_isolation_common_cause"] > s3, "S3 should be supported"
    assert res.ca_j_after["selfing_syndrome_active"] < s2, "S2 should be rejected"
