"""Tests for the constraint-separated replacement example.

This is the proof that CRC carries information beyond the marginal posterior:
two mechanisms tied by CA_j (and tied by CRC under data alone) are cleanly
separated by CRC once external literature constraints are supplied.
"""
import math

import pytest

from causal_model.worked_examples.constraint_separated_replacement import (
    run_constraint_separated,
    literature_constraints,
    _abc_accept,
    _switches,
    ConstraintSeparatedResult,
)
from causal_model.causal_replaceability import causal_replaceability_cost


# ---------------------------------------------------------------------------
# The posterior CANNOT separate the two mechanisms
# ---------------------------------------------------------------------------

def test_marginal_posterior_ties_the_two_mechanisms():
    res = run_constraint_separated(n_attempts=30000, seed=1)
    # CA(thermal) ≈ CA(resource): informationally symmetric for the cline
    assert abs(res.ca["thermal"] - res.ca["resource"]) < 0.03, (
        f"Posterior should tie them: CA(thermal)={res.ca['thermal']}, "
        f"CA(resource)={res.ca['resource']}"
    )


def test_crc_without_constraints_also_ties_them():
    res = run_constraint_separated(n_attempts=30000, seed=1)
    # Data alone (no external constraints) cannot separate either
    assert abs(res.crc_data_only["thermal"] - res.crc_data_only["resource"]) < 0.1, (
        "CRC(data only) should tie them — separation must come from constraints"
    )


# ---------------------------------------------------------------------------
# CRC WITH literature constraints separates them (the headline result)
# ---------------------------------------------------------------------------

def test_literature_constraints_separate_the_mechanisms():
    res = run_constraint_separated(n_attempts=30000, seed=1)
    crc_t = res.crc_constrained["thermal"]
    crc_r = res.crc_constrained["resource"]
    # resource is load-bearing (irreplaceable without violating thermal's
    # documented effect-size range); thermal is freely replaceable.
    assert crc_r > crc_t + 10.0, (
        f"Literature constraints must separate them: "
        f"CRC(resource)={crc_r:.3f} should greatly exceed CRC(thermal)={crc_t:.3f}"
    )


def test_separation_is_contributed_by_the_constraint_not_the_posterior():
    """The crux: the resource/thermal gap appears ONLY when constraints are on."""
    res = run_constraint_separated(n_attempts=30000, seed=1)
    gap_data = abs(res.crc_data_only["resource"] - res.crc_data_only["thermal"])
    gap_lit = abs(res.crc_constrained["resource"] - res.crc_constrained["thermal"])
    assert gap_lit > 10 * max(gap_data, 1e-6), (
        "The separation must be contributed by the external constraint: "
        f"gap(data)={gap_data:.4f}, gap(+lit)={gap_lit:.4f}"
    )


def test_thermal_crc_barely_changes_with_constraints():
    """Replacing thermal by resource needs a coefficient near resource's
    documented mean, so the constraint adds almost nothing to CRC(thermal)."""
    res = run_constraint_separated(n_attempts=30000, seed=1)
    delta = res.crc_constrained["thermal"] - res.crc_data_only["thermal"]
    assert delta < 1.0, (
        f"CRC(thermal) should barely change with constraints, got Δ={delta:.3f}"
    )


# ---------------------------------------------------------------------------
# Constraint structure
# ---------------------------------------------------------------------------

def test_literature_constraints_are_external_normal_priors():
    cons = literature_constraints()
    by_name = {c.name: c for c in cons}
    assert by_name["w_thermal"].type == "normal"
    assert by_name["w_resource"].type == "normal"
    # thermal documented modest, resource documented strong
    assert by_name["w_thermal"].mu < by_name["w_resource"].mu


def test_ablating_resource_forces_thermal_above_its_documented_range():
    """Direct check: in resource-ablated rows, w_thermal is pushed far above μ."""
    acc = _abc_accept(30000, seed=1)
    ablated = [r for r in acc if not r.get("resource")]
    assert ablated, "there should be resource-off accepted rows"
    # To carry the steep cline alone, thermal coefficient must be ≥ ~1.0,
    # which is ≫ its documented mean of 0.30.
    min_w_thermal = min(r["w_thermal"] for r in ablated)
    assert min_w_thermal > 0.9, (
        f"resource-ablated rows must use a large thermal coefficient, "
        f"min(w_thermal)={min_w_thermal:.3f}"
    )


# ---------------------------------------------------------------------------
# Reproducibility & registration
# ---------------------------------------------------------------------------

def test_reproducible():
    a = run_constraint_separated(n_attempts=15000, seed=7)
    b = run_constraint_separated(n_attempts=15000, seed=7)
    assert a.n_accepted == b.n_accepted
    assert a.crc_constrained == b.crc_constrained


def test_result_type():
    res = run_constraint_separated(n_attempts=8000, seed=1)
    assert isinstance(res, ConstraintSeparatedResult)
    assert set(res.ca.keys()) == {"thermal", "resource"}
