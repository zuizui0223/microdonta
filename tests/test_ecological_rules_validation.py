"""Tests for RACH validation against established ecological rules."""
from causal_model.ecological_rules_validation import (
    ECOLOGICAL_RULES,
    EcologicalRule,
    validate_rule,
    run_validation,
    _all_off_fraction,
    _abc_accept,
    RuleValidation,
)


def _rule_by_name(name):
    return next(r for r in ECOLOGICAL_RULES if r.name == name)


def test_panel_has_varied_structure():
    # the panel must not be one template relabelled: it should span 2-way and
    # 3-way confounds and different switch counts
    n_mech = {len(r.mechanisms) for r in ECOLOGICAL_RULES}
    n_total = {len(r.mechanisms) + len(r.inert_controls) for r in ECOLOGICAL_RULES}
    assert 3 in n_mech              # at least one 3-way confound (Foster)
    assert len(n_total) > 1         # K varies across rules


def test_all_off_fraction_near_zero_for_disjunction():
    rule = _rule_by_name("Bergmann")
    acc = _abc_accept(rule, n_attempts=3000, seed=1)
    frac = _all_off_fraction(acc, rule.mechanisms)
    assert frac < 0.02              # at least one mechanism required => disjunction


def test_bergmann_validates_with_direction_recovery():
    res = validate_rule(_rule_by_name("Bergmann"), n_attempts=4000, seed=1)
    assert res.confound_reproduced            # V1
    assert res.nov_points_correctly           # V2
    assert res.direction_recovered is True    # V3 (resolved truth)
    assert res.ca_after["fasting_endurance"] > 0.9
    assert res.ca_after["heat_conservation"] < 0.1


def test_three_way_confound_detected():
    # Foster is a 3-way confound: the pairwise edge layer would miss it, but the
    # degeneracy-based V1/V2 must still flag and resolve it
    res = validate_rule(_rule_by_name("Foster_island"), n_attempts=4000, seed=1)
    assert len(res.ca_confound) == 3
    assert res.confound_reproduced            # V1 via all-off-cell-empty
    assert res.nov_points_correctly           # V2 via mech-subset degeneracy drop
    assert res.direction_recovered is None    # literature: unresolved


def test_unresolved_rule_skips_direction_recovery():
    res = validate_rule(_rule_by_name("Gloger"), n_attempts=3000, seed=1)
    assert res.direction_recovered is None
    assert res.passes                          # passes on V1+V2 alone


def test_full_panel_passes():
    results = run_validation(n_attempts=3000, seed=1)
    assert len(results) == len(ECOLOGICAL_RULES)
    assert all(r.passes for r in results)


def test_validation_is_reproducible():
    a = validate_rule(_rule_by_name("Bergmann"), n_attempts=2000, seed=3)
    b = validate_rule(_rule_by_name("Bergmann"), n_attempts=2000, seed=3)
    assert a.ca_confound == b.ca_confound
    assert a.direction_recovered == b.direction_recovered


def test_every_rule_carries_verification_note():
    # provisional encodings must be tagged for domain-expert verification
    for r in ECOLOGICAL_RULES:
        assert r.literature_note
        assert "VERIFY" in r.literature_note.upper() or "UNRESOLVED" in r.literature_note.upper()
