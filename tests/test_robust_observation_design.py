from dataclasses import replace

import pytest

from causal_model.empirical_observation_contract import LikelihoodCandidate
from causal_model.robust_observation_design import (
    CalibrationScenario, robust_likelihood_design, synthetic_example,
)

ROWS=[{'target':0},{'target':1}]
KW=dict(target_columns=['target'],support_reference='synthetic two worlds')


def channel(name,e):
    return LikelihoodCandidate(name,('low','high'),((1-e,e),(e,1-e)))


def scenario(name,weights=(1,1),candidates=None):
    return CalibrationScenario(name,weights,tuple(candidates or (channel('good',.1),channel('worse',.2))),
                               'declared synthetic scenario')


def test_prior_reversal_has_no_uniform_winner_but_balanced_minimax_choice():
    r=synthetic_example()['receipt']
    assert not r['uniformly_best_names']
    assert r['unique_uniform_winner'] is None
    assert r['minimax_regret_names']==('balanced',)
    assert r['minimum_worst_regret_bits']==pytest.approx(.03606975887039099)
    assert r['scores'][0]['worst_regret_bits']==pytest.approx(.09362250312814774)


def test_paired_dominance_survives_overlapping_marginal_information_ranges():
    r=robust_likelihood_design(ROWS,[scenario('rare',(99,1)),scenario('balanced')],**KW)
    good,bad=r.scores
    assert good.lower_information_bits < bad.upper_information_bits
    assert r.unique_uniform_winner=='good'
    assert r.pairwise_minimum_advantage_bits['good']['worse']>0
    assert r.minimum_worst_regret_bits==0


def test_missing_candidate_cannot_certify_full_vocabulary_winner_or_regret():
    complete=scenario('complete')
    missing=replace(channel('worse',.2),probabilities=None)
    r=robust_likelihood_design(ROWS,[complete,scenario('partial',candidates=(channel('good',.1),missing))],**KW)
    assert not r.complete_vocabulary
    assert r.unique_uniform_winner is None
    assert not r.uniformly_best_names and not r.minimax_regret_names
    assert r.minimum_worst_regret_bits is None
    assert r.unresolved_candidate_names==('worse',)
    assert r.scores[1].lower_information_bits is None


def test_ties_remain_ties_and_zero_information_is_not_a_sequence_limit():
    c=(channel('one',.5),channel('two',.5))
    r=robust_likelihood_design(ROWS,[scenario('s',candidates=c)],**KW)
    assert set(r.uniformly_best_names)=={'one','two'}
    assert r.unique_uniform_winner is None
    assert r.minimum_worst_regret_bits==0
    assert all(s.lower_information_bits==0 for s in r.scores)


def test_empty_vocabulary_is_incomplete():
    r=robust_likelihood_design(ROWS,[CalibrationScenario('s',(1,1),(),'declared')],**KW)
    assert not r.complete_vocabulary
    assert not r.minimax_regret_names


def test_candidate_order_and_scenario_order_do_not_change_decision():
    models=[scenario('a',(3,1)),scenario('b',(1,3))]
    a=robust_likelihood_design(ROWS,models,**KW)
    b=robust_likelihood_design(ROWS,[replace(s,candidates=tuple(reversed(s.candidates)))
                                    for s in reversed(models)],**KW)
    assert a.unique_uniform_winner==b.unique_uniform_winner
    assert set(a.minimax_regret_names)==set(b.minimax_regret_names)


@pytest.mark.parametrize('models', [[],[scenario('a'),scenario('a')],
    [scenario('a'),scenario('b',candidates=(channel('different',.1),))],
    [replace(scenario('s'),calibration_reference='')],
    [scenario('s',(0,1))], [scenario('s',(1,float('nan')))]])
def test_invalid_scenario_contracts_rejected(models):
    with pytest.raises(ValueError):
        robust_likelihood_design(ROWS,models,**KW)


@pytest.mark.parametrize('tol',[-1,float('nan'),float('inf')])
def test_invalid_tolerances_rejected(tol):
    with pytest.raises(ValueError):
        robust_likelihood_design(ROWS,[scenario('s')],**KW,comparison_tolerance_bits=tol)


def test_outcome_vocabulary_must_stay_same_for_same_measurement():
    s=scenario('s')
    altered=replace(s.candidates[0],outcomes=('negative','positive'))
    with pytest.raises(ValueError,match='outcome'):
        robust_likelihood_design(ROWS,[s,scenario('t',candidates=(altered,s.candidates[1]))],**KW)


def test_malformed_probabilities_not_converted_to_missing():
    bad=replace(channel('bad',.1),probabilities=((1,1),(0,0)))
    with pytest.raises(ValueError,match='probability'):
        robust_likelihood_design(ROWS,[scenario('s',candidates=(bad,))],**KW)


def test_target_validation_is_retained():
    with pytest.raises(ValueError,match='missing'):
        robust_likelihood_design([{},{}],[scenario('s')],**KW)
    with pytest.raises(ValueError,match='bare string'):
        robust_likelihood_design(ROWS,[scenario('s')],target_columns='target',support_reference='s')
