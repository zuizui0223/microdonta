"""Independent sequence oracle and scope/input tests for the replication audit."""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from math import fsum, log2, prod

import pytest

from causal_model.empirical_observation_contract import LikelihoodCandidate
from causal_model.replication_information_audit import replication_information_profile
from examples.replication_limit_report import build_replication_examples


def _audit(targets, probabilities, *, weights=None, horizons=(0, 1, 2, 10), **kwargs):
    return replication_information_profile(
        [{"target": target} for target in targets],
        LikelihoodCandidate("repeat_reading", ("absent", "present"), probabilities, "synthetic"),
        target_columns=["target"], weights=weights or [1] * len(targets),
        support_reference="declared test worlds", weight_reference="test weights",
        conditional_iid_reference="fresh readings given a fixed full world",
        horizons=horizons, **kwargs,
    )


def _by_n(report):
    return {row.repeats: row for row in report.horizons}


def _sequence_information_oracle(targets, rates, weights, n):
    """Direct I(T; binary sequence), without binomial counts or production entropy."""
    total = fsum(weights)
    weights = [w / total for w in weights]
    target_mass = {t: fsum(w for s, w in zip(targets, weights) if s == t) for t in set(targets)}
    terms = []
    for sequence in product((0, 1), repeat=n):
        joint = {
            t: fsum(w * prod(p if bit else 1 - p for bit in sequence)
                    for s, p, w in zip(targets, rates, weights) if s == t)
            for t in target_mass
        }
        probability = fsum(joint.values())
        for target, mass in joint.items():
            if mass > 0:
                terms.append(mass * log2(mass / (target_mass[target] * probability)))
    return fsum(terms)


def test_different_laws_reduce_noise_without_finite_support_resolution():
    audit = _audit([0, 1], ((.9, .1), (.1, .9)), horizons=(0, 1, 2, 10, 20, 50, 100))
    by_n = _by_n(audit)
    assert audit.estimable
    assert audit.irreducible_target_entropy_bits == pytest.approx(0)
    assert audit.asymptotic_information_bits == pytest.approx(1)
    assert audit.same_law_different_target_pair is None
    assert by_n[1].information_bits == pytest.approx(0.5310044064107189)
    assert by_n[20].expected_remaining_entropy_bits == pytest.approx(1.2359518393751702e-5)
    # At high precision the displayed MI may round to H(T); no exact upgrade.
    assert by_n[100].expected_remaining_entropy_bits > 0
    assert all(not row.complete_repair_in_declared_pool for row in audit.horizons)
    assert all(row.max_remaining_target_image_size == 2 for row in audit.horizons)
    assert audit.feasible_domain_exhaustiveness == "not_certified"


def test_equal_law_different_programs_have_an_irreducible_floor():
    audit = _audit(["pollination_only", "abiotic_only", "combined"],
                   ((.1, .9), (.9, .1), (.1, .9)), horizons=(0, 1, 2, 10, 20, 50))
    assert audit.same_law_different_target_pair == (0, 2)
    assert audit.irreducible_target_entropy_bits == pytest.approx(2 / 3)
    assert audit.asymptotic_information_bits == pytest.approx(log2(3) - 2 / 3)
    assert _by_n(audit)[1].information_bits == pytest.approx(.47908265000462413)
    assert _by_n(audit)[50].expected_remaining_entropy_bits == pytest.approx(2 / 3, abs=1e-10)
    assert all(r.expected_remaining_entropy_bits >= 2 / 3 - 1e-12 for r in audit.horizons)


def test_floor_uses_declared_weights_not_world_counts():
    audit = _audit(["A", "B", "C"], ((.1, .9), (.9, .1), (.1, .9)), weights=[3, 2, 1])
    binary_h = -(.75 * log2(.75) + .25 * log2(.25))
    assert audit.irreducible_target_entropy_bits == pytest.approx((2 / 3) * binary_h)


def test_singleton_zero_can_hide_information_in_fresh_replicates():
    persistent = _audit([0, 0, 1, 1], ((.8, .2), (.2, .8), (.5, .5), (.5, .5)))
    assert _by_n(persistent)[1].information_bits == pytest.approx(0, abs=1e-14)
    assert _by_n(persistent)[2].information_bits == pytest.approx(.024309739895576943)
    assert persistent.irreducible_target_entropy_bits == 0
    # Averaging over persistent nuisance before forming a product changes the
    # generative protocol to nuisance redrawn at each observation.
    redrawn = _audit([0, 1], ((.5, .5), (.5, .5)))
    assert all(r.information_bits == pytest.approx(0, abs=1e-14) for r in redrawn.horizons)
    assert redrawn.irreducible_target_entropy_bits == pytest.approx(1)


def test_count_compression_matches_independent_full_sequence_oracle_exhaustively():
    for targets in product((0, 1), repeat=4):
        for rates in product((.25, .75), repeat=4):
            weights = [1, 2, 3, 4]
            audit = _audit(targets, tuple((1 - p, p) for p in rates), weights=weights,
                           horizons=(0, 1, 2, 3))
            for row in audit.horizons:
                assert row.information_bits == pytest.approx(
                    _sequence_information_oracle(targets, rates, weights, row.repeats), abs=2e-12)
                assert row.information_bits <= audit.asymptotic_information_bits + 1e-12


def test_genuinely_constant_target_resolves_even_with_many_worlds():
    audit = _audit(["A", "A", "A"], ((.1, .9), (.5, .5), (.9, .1)))
    assert audit.target_identified_in_declared_pool
    assert all(r.complete_repair_in_declared_pool for r in audit.horizons)
    assert all(r.information_bits == 0 for r in audit.horizons)


def test_deterministic_repair_does_not_count_impossible_outcomes_as_failures():
    audit = _audit([0, 1], ((1., 0.), (0., 1.)))
    assert not _by_n(audit)[0].complete_repair_in_declared_pool
    for n in (1, 2, 10):
        assert _by_n(audit)[n].complete_repair_in_declared_pool
        assert _by_n(audit)[n].positive_outcome_count == 2
        assert _by_n(audit)[n].information_bits == pytest.approx(1)


def test_partial_support_repair_is_not_full_repair():
    audit = _audit([0, 1], ((1., 0.), (.5, .5)))
    assert not _by_n(audit)[2].complete_repair_in_declared_pool
    assert _by_n(audit)[2].max_remaining_target_image_size == 2


def test_close_but_different_laws_are_not_merged_by_a_tolerance():
    audit = _audit([0, 1], ((.5, .5), (.4999999999999999, .5000000000000001)), horizons=(1,))
    assert len(audit.law_classes) == 2
    assert audit.irreducible_target_entropy_bits == 0
    assert audit.same_law_different_target_pair is None
    # A tiny numerically unresolved MI is not a certificate of equal laws.


def test_small_positive_likelihood_is_not_lost_by_one_minus_p_roundoff():
    audit = _audit([0, 1], ((1e-20, 1.), (1., 1e-20)), horizons=(1, 2))
    assert all(r.max_remaining_target_image_size == 2 for r in audit.horizons)
    assert all(not r.complete_repair_in_declared_pool for r in audit.horizons)


def test_underflow_is_reported_instead_of_silent_structural_exclusion():
    with pytest.raises(ValueError, match="underflow"):
        _audit([0, 1], ((1e-300, 1.), (1., 1e-300)), horizons=(2,))


def test_missing_likelihood_is_nonestimable_not_zero_floor():
    audit = _audit([0, 1], None)
    assert not audit.estimable
    assert audit.target_entropy_bits == pytest.approx(1)
    assert audit.irreducible_target_entropy_bits is None
    assert audit.asymptotic_information_bits is None
    assert audit.horizons == ()
    assert audit.law_classes == ()


@pytest.mark.parametrize("horizons", [(), (1, 1), (-1,), (True,), (1.5,), (257,), "12"])
def test_malformed_horizons_are_rejected(horizons):
    with pytest.raises(ValueError, match="horizons"):
        _audit([0, 1], ((.9, .1), (.1, .9)), horizons=horizons)


@pytest.mark.parametrize("weights", [[0, 1], [-1, 1], [float("nan"), 1], [1]])
def test_invalid_or_zero_support_weights_are_rejected(weights):
    with pytest.raises(ValueError, match="weight"):
        _audit([0, 1], ((.9, .1), (.1, .9)), weights=weights)


@pytest.mark.parametrize("target_columns", ["target", [], ["missing"], ["target", "target"]])
def test_target_schema_is_not_silently_rewritten(target_columns):
    with pytest.raises(ValueError):
        replication_information_profile(
            [{"target": 0}, {"target": 1}],
            LikelihoodCandidate("read", ("a", "b"), None),
            target_columns=target_columns, weights=[1, 1], support_reference="test",
            weight_reference="test", conditional_iid_reference="test fixed world iid",
        )


@pytest.mark.parametrize("reference", [None, "", "  "])
def test_independence_cannot_be_inferred_from_a_singleton_matrix(reference):
    with pytest.raises(ValueError, match="conditional_iid_reference"):
        replication_information_profile(
            [{"target": 0}], LikelihoodCandidate("read", ("a", "b"), ((.5, .5),)),
            target_columns=["target"], weights=[1], support_reference="test",
            weight_reference="test", conditional_iid_reference=reference,
        )


@pytest.mark.parametrize("outcomes, probabilities", [
    (("a",), ((1.,),)), (("a", "b", "c"), ((1., 0., 0.),)),
    ("ab", ((.5, .5),)), (("a", "a"), ((.5, .5),)),
    (("a", "b"), ((.7, .7),)), (("a", "b"), ((float("nan"), .5),)),
])
def test_binary_model_contract_is_checked(outcomes, probabilities):
    with pytest.raises(ValueError):
        replication_information_profile(
            [{"target": 0}], LikelihoodCandidate("read", outcomes, probabilities),
            target_columns=["target"], weights=[1], support_reference="test",
            weight_reference="test", conditional_iid_reference="fixed world iid",
        )


def test_inputs_are_not_mutated_and_horizons_are_canonicalized():
    rows, weights = [{"target": 0}, {"target": 1}], [1, 2]
    saved = deepcopy((rows, weights))
    report = replication_information_profile(
        rows, LikelihoodCandidate("read", ("a", "b"), ((.9, .1), (.1, .9))),
        target_columns=["target"], weights=weights, support_reference="test",
        weight_reference="test", conditional_iid_reference="fixed world iid", horizons=(2, 0, 1),
    )
    assert (rows, weights) == saved
    assert [r.repeats for r in report.horizons] == [0, 1, 2]


def test_example_keeps_empirical_and_exhaustiveness_claims_closed():
    result = build_replication_examples()
    assert result["data_kind"] == "synthetic_replication_limit_witnesses"
    assert len(result["reports"]) == 4
    for report in result["reports"].values():
        assert report["feasible_domain_exhaustiveness"] == "not_certified"
        assert "not empirical calibration" in report["calibration_reference"]


def test_floor_is_an_expected_residual_not_a_lower_bound_for_each_realised_outcome():
    from causal_model.empirical_observation_contract import condition_on_selected
    from causal_model.replication_information_audit import _binomial_row

    rows = [{"target": "P"}, {"target": "A"}, {"target": "both"}]
    binary = ((.1, .9), (.9, .1), (.1, .9))
    counts = LikelihoodCandidate("twenty_readings", tuple(f"count_{k}" for k in range(21)),
                                 tuple(_binomial_row(row, 20) for row in binary))
    posterior = condition_on_selected(rows, counts, "count_0", target_columns=["target"], weights=[1, 1, 1])
    audit = _audit(["P", "A", "both"], binary, horizons=(20,))
    assert posterior.target_entropy_bits < .1
    assert audit.horizons[0].expected_remaining_entropy_bits >= 2 / 3 - 1e-12
    assert not posterior.target_point_identified
