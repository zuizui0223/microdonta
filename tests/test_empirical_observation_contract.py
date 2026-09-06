import pytest
from causal_model.empirical_observation_contract import (
    LikelihoodCandidate, score_likelihood_candidates, condition_on_selected,
    target_state, synthetic_example,
)
ROWS=[{"target":0},{"target":1}]
META=dict(target_columns=["target"],weights=[1,1],support_reference="two declared worlds",
          weight_reference="uniform by design")


def noisy(error=0.1):
    return LikelihoodCandidate("noisy",("low","high"),((1-error,error),(error,1-error)))


def test_noisy_measurement_has_less_information_than_perfect_measurement():
    r=score_likelihood_candidates(ROWS,[noisy()],**META)
    assert r.scores[0].information_bits==pytest.approx(0.5310044064107188)
    perfect=score_likelihood_candidates(ROWS,[noisy(0)],**META)
    assert perfect.scores[0].information_bits==pytest.approx(1)


def test_positive_likelihood_everywhere_does_not_point_identify_target():
    p=condition_on_selected(ROWS,noisy(),"high",target_columns=["target"],weights=[1,1])
    assert p.posterior_weights==pytest.approx((0.1,0.9))
    assert not p.target_point_identified and p.remaining_target_image_size==2
    p=condition_on_selected(ROWS,noisy(1e-16),"high",target_columns=["target"],weights=[1,1])
    assert p.target_entropy_bits < 1e-12 and not p.target_point_identified


def test_missing_predictions_are_not_zero_and_rank_is_provisional():
    missing=LikelihoodCandidate("unmeasured",("low","high"),None)
    r=score_likelihood_candidates(ROWS,[noisy(),missing],**META)
    assert not r.complete_vocabulary and r.ranking_scope=="provisional_estimable_subset"
    assert not r.scores[1].estimable and r.scores[1].information_bits is None


def test_deterministic_likelihood_can_identify_after_observation():
    p=condition_on_selected(ROWS,noisy(0),"high",target_columns=["target"],weights=[1,1])
    assert p.target_point_identified and p.remaining_target_image_size==1


@pytest.mark.parametrize("row",[{}, {"target":None},{"target":float("nan")},
                               {"target":float("inf")},{"target":(1,None)}])
def test_missing_target_never_becomes_a_target_class(row):
    with pytest.raises(ValueError):
        target_state(row,["target"])


def test_null_guard_applies_to_existing_public_target_entropy():
    from causal_model.target_observation_value import target_entropy_bits
    for rows in ([{},{}],[{"target":None},{"target":None}]):
        with pytest.raises(ValueError,match="target"):
            target_entropy_bits(rows,["target"])


def test_malformed_likelihood_and_zero_world_weight_are_rejected():
    bad=LikelihoodCandidate("bad",("low","high"),((0.8,0.8),(0.1,0.9)))
    with pytest.raises(ValueError,match="probability"):
        score_likelihood_candidates(ROWS,[bad],**META)
    meta=dict(META);meta["weights"]=[1,0]
    with pytest.raises(ValueError,match="positive"):
        score_likelihood_candidates(ROWS,[noisy()],**meta)


def test_row_weight_changes_information_but_not_target_image():
    meta=dict(META);meta["weights"]=[9,1]
    a=score_likelihood_candidates(ROWS,[noisy()],**META)
    b=score_likelihood_candidates(ROWS,[noisy()],**meta)
    assert a.target_image_size==b.target_image_size==2
    assert b.scores[0].information_bits < a.scores[0].information_bits


def test_duplicate_target_columns_are_rejected():
    with pytest.raises(ValueError,match="unique"):
        target_state(ROWS[0],["target","target"])


def test_example_is_synthetic():
    assert synthetic_example()["data_kind"]=="synthetic_noisy_likelihood_witness"


def test_bare_string_columns_rejected_and_large_integer_target_is_valid():
    with pytest.raises(ValueError,match="sequence"):
        target_state({"t":0},"t")
    assert target_state({"target":10**1000},["target"]) == (10**1000,)


def test_public_scoring_also_rejects_bare_string_target_columns():
    meta=dict(META); meta["target_columns"]="t"
    with pytest.raises(ValueError, match="sequence"):
        score_likelihood_candidates([{"t":0},{"t":1}], [noisy()], **meta)
