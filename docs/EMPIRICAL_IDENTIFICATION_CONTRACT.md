# Empirical observation contract: noisy target acquisition

Status: optional declared-likelihood route. This does not replace the validated
mechanism-information score I(S;Q)/K, its deterministic partition contract, the
existing target API, or the current joint-information stopping audit.
No field-data likelihood is fitted here. The runnable witness is synthetic.

## Required inputs before acquisition

Supply a finite admissible ensemble with a predeclared, fully encoded target on
every row; strictly positive row weights and their provenance; the definition of
the represented support; and each candidate's per-world outcome probabilities.
Likelihood rows must align with the ensemble's row order and sum to one. A context
change requires a separately calibrated/transport-validated likelihood model.

Unlike a deterministic partition, a noisy observation can have positive
probability in multiple worlds. To support empirical use, estimate/validate the
measurement-error model with independent known-reference or otherwise identified
calibration information appropriate to the measurement context. An overall
observed high/low frequency does not supply P(Q|world). The optional
`calibration_reference` records provenance only: the function does not inspect
external calibration evidence or validate that model biologically.

The module computes:

    P(T=t,Q=q)=sum_{i:T_i=t} w_i L_i(q)
    I(T;Q)=H(T)-sum_q P(q) H(T|Q=q).

Changing prior/ensemble weights can change observation rankings. Retain the
weighting definition and report sensitivity across plausible weightings rather
than treating one weighted ranking as evidence-independent.

## Non-estimable is not zero

A missing candidate matrix yields `estimable=False` and information=None.
A best candidate among the remaining estimable subset is labelled provisional.
A malformed supplied probability matrix is an input error, not a silent fallback.
An empty vocabulary is not reported as a fully evaluated observation set.

Targets absent from a row, None, NaN, infinity, non-reflexive missing labels,
unhashable values and duplicate target column names are rejected. A missing
biological target must not be encoded as a shared None class and then called
point-identified. Tests also check the concurrent core target-entropy safeguard;
that core change is preserved rather than overwritten by this extension.

## Exact support is different from confidence

After the selected observation is revealed, condition its likelihood only.
Point identification is based on the number of remaining target values with
positive likelihood, NOT an entropy tolerance or posterior mode.

For equal prior weights and a symmetric binary error probability eta=0.1:

    I(T;Q)=1-h2(0.1)=0.5310044064107188 bits.

After outcome high, posterior target probabilities are (0.1,0.9), entropy is
0.4689955935892812 bits, and both targets remain. Even eta=1e-16 must not be
converted into exact identification simply because entropy is below 1e-12.
The deterministic eta=0 case can genuinely eliminate a target in this finite
model. This distinction is conditional on the supplied likelihood/support, not
a claim that real finite measurements certify a biological mechanism.

## Sequence and report limits

This module scores one-step candidates; separate marginal matrices do not define
joint dependence across candidates. Zero singleton information still does not
prove zero bundle/sequence information. Do not multiply likelihoods across
measurements without declaring and validating the relevant dependence model.
A positive-score singleton is not asserted globally optimal for a sequence.

Identification does not by itself license a scientific report. Support
completeness, target relevance, calibration transport and the separate reliability
conditions remain external requirements. Strings recording them are not evidence
that they were met. No human informed-consent model is implemented here.

## Reproduce

From the installed repository root:

    python -m causal_model.empirical_observation_contract
    python -m pytest -q tests/test_empirical_observation_contract.py

Optional imports (top-level publication API remains unchanged):

    from causal_model.empirical_observation_contract import (
        LikelihoodCandidate, score_likelihood_candidates, condition_on_selected,
    )

Implementation: `causal_model/empirical_observation_contract.py`.
Related routes: `causal_model/target_observation_value.py`,
`causal_model/target_sequential_design.py`, and the README stopping audit.
