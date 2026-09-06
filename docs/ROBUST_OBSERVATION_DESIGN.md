# Robust target acquisition over declared calibration scenarios

Status: optional finite-scenario extension of the
[noisy observation contract](EMPIRICAL_IDENTIFICATION_CONTRACT.md).
It does not change publication-facing mechanism MROD, target public exports,
sequential stopping semantics, or the deterministic predictive-partition contract.
All bundled examples are synthetic, not estimated field-data calibration.

## What varies and what is held fixed

Each named CalibrationScenario supplies a strictly positive world-weight vector,
a likelihood matrix per candidate, and provenance. Scenarios share the same
represented rows, declared target and candidate/outcome vocabularies. The
likelihood matrix or prior weights can vary; they are coherent alternatives,
not components to average with an invented meta-prior.

Metadata records assumptions; it does not validate a likelihood or establish
transportability. The guarantee is only over the enumerated finite scenario set.
Testing its endpoints does not certify a continuous uncertainty region or its
convex hull. Correlated sequences need an explicitly separate joint model.

## Paired comparisons, not unrelated extremes

For candidate q in scenario s, use raw one-step information in bits:

    V_s(q)=I_s(T;Q_q).

Costs are assumed equal for this optional rule. Normalized fractions I_s/H_s
would define a different across-scenario loss scale even though they produce
the same ranking within each fixed scenario. The receipt therefore records
`utility_units=raw_target_information_bits` rather than hiding the choice.

A uniformly optimal observation satisfies

    V_s(q)>=V_s(r) for every s and every r.

Use the paired lower advantage

    Delta_min(q,r)=min_s[V_s(q)-V_s(r)].

This is not min_s V_s(q)-max_s V_s(r), which mixes different scenarios and may
miss genuine uniform dominance when individual score ranges overlap. Strict
uniform winners require every paired advantage to exceed the declared numerical
tolerance. Non-strict winners may tie within that tolerance; this is not a
statistical significance test.

## When no observation is uniformly best

Return the absence of a uniform winner, and also an explicitly named alternative
criterion: deterministic minimax regret over equal-cost single observations.

    regret_s(q)=max_r V_s(r)-V_s(q)
    R(q)=max_s regret_s(q)
    q_minregret in argmin_q R(q).

This is a decision rule, not a theorem that nature supplies one universal best
measurement. Randomized acquisition policies, differing costs, multiple steps,
scenario-learning value and other utility scales are outside this API.

The selected observation can be neither scenario's individual optimum while
still avoiding the worst losses from committing to the wrong calibration/prior.

## Missing predictions and zero information

A missing likelihood remains None in that scenario. Candidate envelopes requiring
that missing value are non-estimable, not zero. Partial pairwise scores and regrets
can still describe the common estimable subset, but the receipt labels them
provisional and emits no full-vocabulary uniform winner or minimax-regret choice.
An empty candidate vocabulary is incomplete, not a proven information limit.
Malformed supplied likelihoods, scenario duplication, inconsistent vocabularies,
invalid target labels and nonpositive weights are errors rather than fallbacks.

Zero scores across all scenarios do not imply a sequence-information limit:
complementary observations can still carry joint information. Point identification
and scientific report licensing remain separate from both ranking and regret.

## Exact synthetic decision witness

Two target states and three binary-observation matrices are declared:

    A:        ((1,0), (0.5,0.5))
    B:        ((0.5,0.5), (0,1))
    balanced: ((0.85,0.15), (0.15,0.85)).

Two alternative target-one prior probabilities are 0.1 and 0.9. The resulting
raw information scores (bits) are:

| Candidate | Prior 0.1 | Prior 0.9 | Worst regret |
|---|---:|---:|---:|
| A | 0.186397 | 0.092774 | 0.093623 |
| B | 0.092774 | 0.186397 | 0.093623 |
| balanced | 0.150327 | 0.150327 | 0.036070 |

There is no uniformly best candidate. The balanced observation is the unique
deterministic minimax-regret choice in this finite example, not the maximum-MI
choice in either individual scenario. The same API also tests genuine paired
dominance despite overlapping marginal information envelopes.

## Reproduce

    python -m causal_model.robust_observation_design
    python -m pytest -q tests/test_robust_observation_design.py

Optional imports remain module-scoped:

    from causal_model.robust_observation_design import (
        CalibrationScenario, robust_likelihood_design,
    )

The module reuses the current `score_likelihood_candidates` implementation and
its target, probability-normalization, support and underflow checks. It never
reads a realized outcome during ranking.
