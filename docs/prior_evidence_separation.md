# Current resolvability, prior concentration and evidence gain

Status: mathematical scope note and controlled audit for Mechanism-Resolving Observation Design (MROD).

## 1. The distinction

MROD reports the current mechanism state through

```text
D(A)=H(S|A),
R(A)=1-H(S|A)/K.
```

The current admissible distribution `A` already reflects the declared mechanism vocabulary, parameter support, switch priors, pre-data biological constraints, context and observed targets used in acceptance. Consequently, `R(A)` is an **absolute state summary relative to the K-bit maximum entropy**. It is not a decomposition of which part of the concentration came from the prior, constraints or current observations.

This matters whenever the pre-observation mechanism distribution is non-uniform. A concentrated prior can produce `R>0` before any current observation is applied.

## 2. Baseline-relative evidence contribution

Let `B` denote the declared state before an observation `O` is used. `B` can include the model family, prior, pre-data constraints and fixed context. Then

```text
R_B = 1-H(S|B)/K.
```

After seeing `O=o`,

```text
R_{B,o}=1-H(S|B,O=o)/K.
```

The realised change relative to that baseline is

```text
Delta_R(o)
=R_{B,o}-R_B
={H(S|B)-H(S|B,O=o)}/K.
```

For one realised outcome this difference can be negative because conditioning on surprising evidence can increase entropy.

The expected change is

```text
E_O[Delta_R(O)]
=I(S;O|B)/K
>=0.
```

So three concepts are distinct:

1. current absolute resolvability `R(A)`;
2. realised baseline-relative entropy change `Delta_R(o)`;
3. expected observation information `I(S;O|B)/K`.

## 3. Why candidate V is still the right next-observation quantity

MROD evaluates a future observation `Q` from the **current** mechanism distribution:

```text
V(Q)=I(S;Q|A_current)/K.
```

This is already incremental. It asks how much information the future observation is expected to add beyond everything currently encoded in `A_current`.

Therefore it is entirely coherent for

```text
R(A_current)>0
```

while an independent candidate has

```text
V(Q)=0.
```

The current distribution may already be concentrated because of prior knowledge or earlier evidence; a new irrelevant measurement adds nothing.

## 4. Executable one-switch witness

The controlled witness represents a single binary mechanism with

```text
P(S=1)=0.9,
P(S=0)=0.1
```

before any current observed target is applied.

Its entropy is

```text
H_2(0.9)=0.468996... bit,
```

so for `K=1`

```text
R=1-H_2(0.9)=0.5310.
```

This positive `R` is prior concentration, not evidence supplied by an observation.

Two candidate measurements are then evaluated from exactly this current state:

| Candidate | Raw MI | Normalized V | Expected R after candidate |
|---|---:|---:|---:|
| direct observation of `S` | 0.468996 bit | 0.4690 | 1.0000 |
| mechanism-independent noise | 0.000000 bit | 0.0000 | 0.5310 |

The direct observation can add at most the entropy that remains. The nuisance measurement adds none.

## 5. Prior sensitivity of the next-observation ranking

Candidate information is conditional on the current mechanism distribution. Therefore a scientifically different prior can alter what distinction remains most uncertain and can alter the highest-value observation.

A second controlled witness uses independent binary mechanisms `A` and `B` and direct observations of each.

### Prior specification 1

```text
P(A=1)=0.5,
P(B=1)=0.9.
```

Then

```text
I(S;Q_A)=H(A)=1 bit,
I(S;Q_B)=H(B)=0.468996 bit,
```

so `observe_A` ranks first.

### Prior specification 2

Swap the concentrations:

```text
P(A=1)=0.9,
P(B=1)=0.5.
```

The information ranking swaps too: `observe_B` ranks first.

This is not a defect of conditional information design. It expresses the intended question: *which feasible observation resolves the mechanism uncertainty that remains under the declared current knowledge state?*

It does imply that scientifically plausible alternative priors should be included in sensitivity analysis rather than hidden.

## 6. Reporting rule

1. Call `R` **current resolvability** or **current mechanism concentration**, not “information supplied by the data” without a baseline contrast.
2. If attributing information to current evidence, declare the pre-evidence baseline and report an entropy difference or mutual-information quantity relative to it.
3. Report the priors and pre-data constraints that contribute to the current admissible distribution.
4. When multiple priors are scientifically plausible, report whether the candidate ranking is stable across them.
5. Keep `V(Q)=I(S;Q|A_current)/K` as the next-observation criterion; it is already incremental conditional information.

## 7. Claim guard

Do not claim that:

- positive current `R` proves that the current observations supplied that amount of information;
- `R=1` necessarily means the data alone identified the mechanism;
- candidate ranking is invariant to scientifically different priors;
- prior sensitivity invalidates MROD rather than defining a required sensitivity analysis.

The defensible statement is:

> **R summarizes the concentration of the current declared mechanism distribution; observation information is a baseline-relative or incremental quantity, and MROD's candidate V is already the expected incremental information from the current state.**

## 8. Reproduce

```bash
python -m causal_model.prior_evidence_separation_witness
pytest -q tests/test_prior_evidence_separation_witness.py
```
