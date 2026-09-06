"""Independent probability oracle, branch updates and scope/input regressions."""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from math import log2

import pytest

from causal_model.empirical_observation_contract import LikelihoodCandidate
from causal_model.replication_switch_audit import audit_replication_switch
from examples.replication_switch_report import audit_history, build_report, three_program_model


def audit(rows, repeat, alternatives, weights=None, **kwargs):
    options = dict(
        target_columns=["T"], weights=[1] * len(rows) if weights is None else weights,
        support_reference="controlled worlds", weight_reference="declared test weights",
        conditional_iid_reference="fixed-world iid test assumption",
        future_likelihood_reference="future likelihood conditional on current state",
    )
    options.update(kwargs)
    return audit_replication_switch(rows, repeat, alternatives, **options)


def binary(name, probabilities):
    return LikelihoodCandidate(name, ("zero", "one"),
                               tuple((1-p, p) for p in probabilities), "synthetic")


def entropy(probabilities):
    return -sum(p * log2(p) for p in probabilities if p > 0)


def direct_information(targets, weights, likelihoods):
    """Independent joint-table MI, not the production entropy-difference scorer."""
    total = sum(weights)
    weights = [w / total for w in weights]
    values = set(targets)
    target_mass = {t: sum(w for t0, w in zip(targets, weights) if t0 == t) for t in values}
    outcome_mass = [sum(w * row[j] for w, row in zip(weights, likelihoods))
                    for j in range(len(likelihoods[0]))]
    mi = 0.0
    for t in values:
        for j, pq in enumerate(outcome_mass):
            joint = sum(w * row[j] for t0, w, row in zip(targets, weights, likelihoods) if t0 == t)
            if joint:
                mi += joint * log2(joint / (target_mass[t] * pq))
    return mi


def test_outcome_specific_repeat_or_switch_and_ceiling_comparison():
    initial = audit_history(())["audit"]
    positive = audit_history(("present",))["audit"]
    negative = audit_history(("absent",))["audit"]
    assert initial["best_positive_singletons"] == ("contact", "physiology")
    assert positive["best_positive_singletons"] == ("physiology",)
    assert negative["best_positive_singletons"] == ("contact",)
    assert positive["one_repeat_information_bits"] == pytest.approx(0.120730268962302)
    assert positive["all_repeat_information_ceiling_bits"] == pytest.approx(0.297472248919290)
    candidate = positive["alternatives"][0]
    assert candidate["information_bits"] == pytest.approx(0.529725185026074)
    assert candidate["advantage_over_all_repeat_ceiling_bits"] == pytest.approx(0.232252936106784)
    assert positive["ceiling_dominant_alternatives"] == ("physiology",)
    assert not negative["ceiling_dominant_alternatives"]
    assert not positive["target_identified_in_declared_pool"]
    assert positive["same_law_different_target_pair"] == (0, 2)


def test_no_fixed_sample_count_switch_rule():
    pos = audit_history(("present", "present"))["audit"]
    mix = audit_history(("present", "absent"))["audit"]
    neg = audit_history(("absent", "absent"))["audit"]
    assert pos["best_positive_singletons"] == ("physiology",)
    assert mix["best_positive_singletons"] == ("contact", "physiology")
    assert neg["best_positive_singletons"] == ("contact",)


def test_prior_entropy_floor_is_not_a_bound_on_each_realised_branch():
    # A pathwise use of the previous 2/3-bit floor would be wrong.
    negative = audit_history(("absent", "absent"))["audit"]
    assert negative["target_entropy_bits"] < 2 / 3
    assert negative["repeat_residual_floor_bits"] == pytest.approx(2 / 83)


def test_pairwise_dominance_survives_missing_candidate_but_global_best_does_not():
    result = audit_history(("present",), include_unmodelled=True)["audit"]
    assert result["ceiling_dominant_alternatives"] == ("physiology",)
    assert not result["complete_singleton_coverage"]
    assert result["ranking_scope"] == "provisional_estimable_subset"
    missing = result["alternatives"][1]
    for key in ("information_bits", "advantage_over_one_repeat_bits",
                "within_repeat_law_information_bits", "exceeds_repeat_ceiling_with_margin"):
        assert missing[key] is None


def test_missing_repeat_prediction_does_not_erase_known_alternative():
    rows = [{"T": 0}, {"T": 1}]
    result = audit(rows, LikelihoodCandidate("repeat", ("no", "yes"), None),
                   [binary("new", [0, 1])])
    assert not result.repeat_estimable
    assert result.all_repeat_information_ceiling_bits is None
    assert result.best_positive_singletons == ("new",)
    assert result.alternatives[0].exceeds_repeat_ceiling_with_margin is None


def test_within_law_synergy_is_not_immediate_information_or_impossibility():
    # T and old-law bit C independent; Q=T xor C. Knowing C would unlock Q.
    worlds = tuple(product((0, 1), repeat=2))
    rows = [{"T": t} for t, c in worlds]
    result = audit(rows, binary("old", [c for t, c in worlds]),
                   [binary("xor", [t ^ c for t, c in worlds])])
    assert result.one_repeat_information_bits == pytest.approx(0)
    assert result.all_repeat_information_ceiling_bits == pytest.approx(0)
    assert result.alternatives[0].information_bits == pytest.approx(0)
    assert result.alternatives[0].within_repeat_law_information_bits == pytest.approx(1)
    assert result.next_step_status == "one_step_zero_at_tolerance_joint_not_audited"
    assert not result.ceiling_dominant_alternatives


def test_exceeding_ceiling_is_sufficient_not_necessary_to_prefer_switch():
    rows = [{"T": 0}, {"T": 1}]
    result = audit(rows, binary("old", [0.4, 0.6]), [binary("new", [0.1, 0.9])])
    assert result.best_positive_singletons == ("new",)
    assert result.all_repeat_information_ceiling_bits == pytest.approx(1)
    assert not result.ceiling_dominant_alternatives
    assert result.alternatives[0].within_repeat_law_information_bits == pytest.approx(0)


def test_missing_vs_resolved_and_tolerance_are_separate():
    unknown = LikelihoodCandidate("unknown", ("a", "b"), None)
    rows = [{"T": 0}, {"T": 1}]
    result = audit(rows, binary("old", [.5, .5]), [unknown])
    assert result.next_step_status == "prediction_limited_no_positive_scored_singleton"
    resolved = audit([{"T": 0}, {"T": 0}], binary("old", [.1, .9]), [unknown])
    assert resolved.target_identified_in_declared_pool
    assert not resolved.best_positive_singletons
    unresolved = audit(rows, binary("old", [.1, .9]), [], information_tolerance_bits=2)
    assert not unresolved.target_identified_in_declared_pool
    assert unresolved.next_step_status == "one_step_zero_at_tolerance_joint_not_audited"


def test_calibration_sensitivity_no_automatic_switch_from_new_variable_name():
    good = audit_history(("present",), physiology_error=.1)["audit"]
    uninformative = audit_history(("present",), physiology_error=.5)["audit"]
    assert good["ceiling_dominant_alternatives"]
    assert not uninformative["ceiling_dominant_alternatives"]
    assert uninformative["best_positive_singletons"] == ("contact",)


@pytest.mark.parametrize("kwargs", [
    {"future_likelihood_reference": ""}, {"conditional_iid_reference": ""},
    {"support_reference": ""}, {"weight_reference": ""}, {"target_columns": "T"},
    {"target_columns": []}, {"target_columns": ["missing"]}, {"weights": [1, 0]},
    {"weights": [1, float("nan")]}, {"information_tolerance_bits": -1},
    {"information_tolerance_bits": float("nan")}, {"information_tolerance_bits": float("inf")},
    {"information_tolerance_bits": True},
])
def test_invalid_contracts_raise(kwargs):
    with pytest.raises(ValueError):
        audit([{"T": 0}, {"T": 1}], binary("old", [.1, .9]), [], **kwargs)


def test_duplicate_names_missing_targets_and_outcome_schema_rejected():
    rows = [{"T": 0}, {"T": 1}]
    old = binary("old", [.1, .9])
    with pytest.raises(ValueError):
        audit(rows, old, [old])
    with pytest.raises(ValueError):
        audit([{"T": None}, {"T": None}], old, [])
    with pytest.raises(ValueError):
        audit(rows, old, [LikelihoodCandidate("bad", "ab", None)])
    with pytest.raises(ValueError):
        audit(rows, old, [LikelihoodCandidate("bad", ("a", "b"), ((.7, .7), (.5, .5)))])


def test_no_mutation_and_example_json_serializable():
    import json
    rows, old, new = three_program_model()
    before = deepcopy((rows, old, new))
    audit(rows, old, [new], target_columns=["program"])
    assert (rows, old, new) == before
    json.dumps(build_report(), allow_nan=False)


def test_exhaustive_oracle_for_all_binary_maps_on_three_worlds():
    # 8 target maps x 8 old rate maps x 8 alternative maps = 512 cases.
    weights = [1, 2, 3]
    for targets, choices, qs in product(product((0, 1), repeat=3), repeat=3):
        rates = [.25 if bit == 0 else .75 for bit in choices]
        old, new = binary("old", rates), binary("new", qs)
        rows = [{"T": t} for t in targets]
        result = audit(rows, old, [new], weights=weights)
        info = direct_information(targets, weights, new.probabilities)
        law_matrix = [[int(c == 0), int(c == 1)] for c in choices]
        ceiling = direct_information(targets, weights, law_matrix)
        assert result.alternatives[0].information_bits == pytest.approx(info, abs=1e-10)
        assert result.all_repeat_information_ceiling_bits == pytest.approx(ceiling, abs=1e-10)
        for n in (1, 2, 3):
            sequences = tuple(product((0, 1), repeat=n))
            matrix = [[p ** sum(seq) * (1-p) ** (n-sum(seq)) for seq in sequences] for p in rates]
            repeat_information = direct_information(targets, weights, matrix)
            assert repeat_information <= ceiling + 1e-10
            if result.alternatives[0].exceeds_repeat_ceiling_with_margin:
                assert info > repeat_information


def test_seeded_weighted_noisy_alternatives_against_conditional_oracle():
    import random
    rng = random.Random(20260907)
    for _ in range(128):
        targets = [rng.randrange(3) for _ in range(5)]
        rates = [rng.choice((.15, .5, .85)) for _ in targets]
        weights = [rng.uniform(.1, 4) for _ in targets]
        qs = [rng.uniform(.01, .99) for _ in targets]
        new = binary("new", qs)
        result = audit([{"T": t} for t in targets], binary("old", rates), [new], weights=weights)
        expected_within = 0.0
        for rate in set(rates):
            indices = [i for i, p in enumerate(rates) if p == rate]
            group_weights = [weights[i] for i in indices]
            expected_within += sum(group_weights) / sum(weights) * direct_information(
                [targets[i] for i in indices], group_weights, [new.probabilities[i] for i in indices],
            )
        assert result.alternatives[0].within_repeat_law_information_bits == pytest.approx(
            expected_within, abs=1e-10,
        )
        assert result.alternatives[0].information_bits == pytest.approx(
            direct_information(targets, weights, new.probabilities), abs=1e-10,
        )
