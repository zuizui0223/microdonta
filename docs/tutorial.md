# Mechanism-Resolving Observation Design tutorial

This tutorial introduces the publication-facing method without requiring the
historical project vocabulary. The inference layer consumes an accepted sample
of parameter-mechanism draws, the mechanism definitions and a declared family of
candidate measurements. It reports what remains unresolved and which verified
measurement is expected to reduce that ambiguity most.

## 1. Install and test

```bash
pip install -e ".[dev]"
pytest -q
```

The Python distribution is `mechanism-resolution-design`; its current import
namespace remains `causal_model` for compatibility with the implemented model
family.

## 2. Reproduce the submitted figures

```bash
python -m causal_model.controlled_confounding_demo \
  --figure outputs/g5/figures/figure1_controlled_confounding.png
python paper/make_g2_figure.py \
  --output outputs/g5/figures/figure2_g2_frozen_v2.png
python -m causal_model.observation_value_calibration \
  --figure outputs/g5/figures/figure3_information_value_calibration.png
python -m causal_model.known_truth_benchmark \
  --figure outputs/g5/figures/figureS1_known_truth.png
```

Figure 1 contrasts modal model ranking with the retained admissible mechanism
region, evaluates quantitative candidate measurements using
`V(Q)=I(S;Q|A_epsilon)/K`, and conditions on a realised confound-breaking
measurement. Figure 2 is the frozen truth-peek-free sequential benchmark. Figure
3 checks the information identity and calibration. Figure S1 is a specified-
simulator self-consistency check.

## 3. Minimal admissible-region analysis

```python
from causal_model import (
    compute_admissible_mechanisms,
    mechanism_entropy,
    mechanism_resolvability,
)

# accepted_rows contains one dict per accepted (theta, mechanism) draw.
# Each dict includes Boolean columns named by the mechanism definitions.
admissibility = compute_admissible_mechanisms(accepted_rows, mechanisms)
D = mechanism_entropy(accepted_rows, mechanisms)
R = mechanism_resolvability(accepted_rows, mechanisms)

print(f"residual mechanism entropy: {D:.3f} bits")
print(f"normalized resolvability: {R:.3f}")
for item in admissibility:
    print(item.switch_name, item.CA_j)
```

Interpretation is set-valued. A marginal probability near 0.5 means the current
observation map leaves that mechanism active in roughly half of the accepted
region; it is not evidence that a forced winner has been found. Joint entropy
retains dependence among mechanisms that marginal summaries alone can hide.

## 4. Score candidate measurements

A publication-level candidate must declare outcomes that form a mutually
exclusive and exhaustive predictive partition of the current admissible region.
When that requirement is met, its information value is exactly normalized mutual
information.

```python
from causal_model import observation_information_value

records = observation_information_value(
    accepted_rows,
    mechanisms,
    candidate_measurements,
)
for record in records:
    if record.estimable:
        print(record.candidate, record.information_value)
    else:
        print(record.candidate, "not estimable:", record.reason)
```

The method does not silently replace a missing predictive partition with a
subjective outcome prior. Non-estimable candidates remain visible, with the
reason recorded. A structural fallback can be used in explicitly labelled
compatibility workflows, but it is not the validated `V(Q)` quantity.

## 5. Run adaptive observation design

```python
from causal_model import sequential_observation_design

result = sequential_observation_design(
    accepted_rows=accepted_rows,
    switches=mechanisms,
    candidates=candidate_measurements,
    budget=3,
    seed=7,
)
```

At each step the design ranks candidates before the outcome is revealed,
conditions the admissible region on the realised outcome, and recomputes all
remaining values. It stops when the declared ambiguity is resolved, the budget is
exhausted, or every available verified candidate has zero current information.

## 6. Adapt the method to another ecological system

Provide four ingredients:

1. a declared mechanism vector `S` and prior over its states;
2. a simulator or predictive map from context, parameters and mechanisms to
   observation space;
3. predeclared biological constraints and an acceptance discrepancy defining
   `A_epsilon`;
4. candidate measurements with explicit predictive outcome maps and costs.

The method is simulator-agnostic after the admissible rows are constructed. Its
scientific claim is conditional on the declared model and candidate families: it
quantifies residual mechanism ambiguity and designs the next observation; it does
not convert a synthetic benchmark into a natural-system mechanism discovery.

Historical identifiers retained in frozen G2 machine-readable artifacts are
provenance keys only. They are not the current method name or recommended API.
