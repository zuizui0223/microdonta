"""Smoke tests: verify RACH module imports and key symbols exist.

Covers issue #16 acceptance criteria:
  - All RACH functions imported by streamlit_app can be imported.
  - compute_rach_theory_metrics is importable from causal_model.identifiability.
  - next_observation_value_simulation is importable (simulation NOV).

Run with:
    python tests/test_rach_imports.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))


def test_causal_admissibility_imports():
    from causal_model.causal_admissibility import (
        rach_summary,
        causal_degeneracy,
        causal_resolvability,
        observation_contribution,
        next_observation_value,
        next_observation_value_simulation,
        compute_causal_admissibility_table,
        CandidateObservation,
        CandidateOutcome,
        CAMPANULA_CANDIDATE_OBSERVATIONS,
    )
    assert callable(rach_summary)
    assert callable(causal_degeneracy)
    assert callable(causal_resolvability)
    assert callable(observation_contribution)
    assert callable(next_observation_value)
    assert callable(next_observation_value_simulation)
    assert callable(compute_causal_admissibility_table)
    assert len(CAMPANULA_CANDIDATE_OBSERVATIONS) == 8
    print("[PASS] test_causal_admissibility_imports")


def test_identifiability_imports():
    from causal_model.identifiability import compute_rach_theory_metrics
    assert callable(compute_rach_theory_metrics)
    print("[PASS] test_identifiability_imports")


def test_switch_inference_imports():
    from causal_model.switch_inference import (
        run_switch_posterior_inference,
        run_switch_posterior_inference_abm,
        SwitchPosteriorResult,
        CAMPANULA_SWITCHES,
        BiologicalSwitch,
    )
    import dataclasses
    fields = {f.name for f in dataclasses.fields(SwitchPosteriorResult)}
    assert "evaluated_rows" in fields, "SwitchPosteriorResult missing evaluated_rows"
    assert "accepted_rows" in fields
    assert len(CAMPANULA_SWITCHES) == 4
    print("[PASS] test_switch_inference_imports")


def test_docstring_mentions_rach_notation():
    """R_RACH docstring should use K (not H(S)) in the formula."""
    import causal_model.causal_admissibility as _mod
    doc = _mod.__doc__ or ""
    assert "R_RACH" in doc, "Module docstring should use R_RACH notation"
    assert "H(S|A_ε)/K" in doc or "H(S|Aε)/K" in doc or "log2|S|" in doc, (
        "Module docstring should mention K as denominator in R_RACH"
    )
    assert "observation_contribution(evaluated_rows" in doc, (
        "Public API docstring should list evaluated_rows, not accepted_rows"
    )
    print("[PASS] test_docstring_mentions_rach_notation")


def test_candidate_outcomes_probabilities():
    from causal_model.causal_admissibility import CAMPANULA_CANDIDATE_OBSERVATIONS
    for cand in CAMPANULA_CANDIDATE_OBSERVATIONS:
        if cand.outcomes:
            total = sum(o.prior_probability for o in cand.outcomes)
            assert abs(total - 1.0) < 1e-9, (
                f"Candidate {cand.name}: outcome probabilities sum to {total:.4f}, expected 1.0"
            )
    print("[PASS] test_candidate_outcomes_probabilities")


if __name__ == "__main__":
    failures = []
    tests = [
        test_causal_admissibility_imports,
        test_identifiability_imports,
        test_switch_inference_imports,
        test_docstring_mentions_rach_notation,
        test_candidate_outcomes_probabilities,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback
            print(f"\n[FAIL] {t.__name__}: {e}")
            traceback.print_exc()
            failures.append(t.__name__)
    print()
    if failures:
        print(f"FAILED: {failures}")
        sys.exit(1)
    else:
        print(f"All {len(tests)} smoke tests passed.")
