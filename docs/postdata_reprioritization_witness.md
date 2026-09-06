# Post-data candidate reprioritization witness

Status: controlled conceptual witness. This is **not** a benchmark against Yanco et al. (2020), Value of Information, Bayesian experimental design, or any named method. It isolates why a next-observation ranking must be conditioned on the evidence available at the time the next observation is chosen.

## Question

Pre-data multiple-working-hypotheses analysis can reveal whether proposed hypotheses are distinguishable before data collection. MROD starts later, after current evidence has already restricted the mechanism region. Does an observation ranking computed before that current evidence necessarily remain appropriate afterwards?

No. Candidate rankings can reverse after conditioning on current evidence.

## Construction

Let the declared mechanism vector be two balanced binary coordinates

```text
S = (A,B) in {0,1}^2,
```

with the four prior states equally represented.

Two candidate observations are available.

### Candidate 1 — `observe_A`

This candidate reads `A` exactly. Under the four-state pre-data distribution,

```text
I(S;Q_A)=1 bit.
```

### Candidate 2 — `observe_B_when_A0`

This candidate is positive only in state `(A=0,B=1)` and otherwise negative. Before current evidence, its positive outcome has probability `1/4`, so

```text
I(S;Q_B*) = H_2(1/4)
           = 0.811278... bit.
```

Thus pre-data information ranking prefers

```text
observe_A > observe_B_when_A0.
```

## Current evidence

Now suppose the already-collected evidence fixes

```text
A=0
```

while leaving `B` balanced and unresolved.

Within this post-data region:

- `observe_A` is constant, so `I(S;Q_A | A=0)=0`;
- `observe_B_when_A0` becomes an exact observation of `B`, so `I(S;Q_B* | A=0)=1 bit`.

The ranking therefore reverses:

```text
pre-data:  observe_A              1.000000 bit
           observe_B_when_A0      0.811278 bit

post-data: observe_A              0.000000 bit
           observe_B_when_A0      1.000000 bit
```

With `K=2`, MROD's normalized values are respectively

```text
pre-data:  0.5000 vs 0.4056
post-data: 0.0000 vs 0.5000.
```

## Interpretation

This is a ranking-reversal witness, not a novelty theorem. Bayesian and sequential design already condition decisions on available information. The purpose here is narrower: it makes the **post-current-data** qualifier in MROD operational.

A pre-data discriminability analysis and a post-data next-observation analysis answer questions at different information states. Once current ecological evidence has removed one mechanism distinction, an earlier high-value measurement can become redundant while another measurement becomes the relevant resolver.

This supports the following workflow distinction:

```text
pre-data hypothesis vetting
    -> are the proposed hypotheses distinguishable under the planned design?

current evidence arrives
    -> which mechanism programs remain admissible now?

post-data MROD
    -> among feasible follow-up observations, which one is informative about
       the mechanism distinctions that actually remain now?
```

## Claim guard

Do **not** infer from this witness that:

- pre-data multiple-working-hypotheses analysis is inferior;
- Yanco et al. (2020) prescribes a fixed ranking that cannot be updated;
- MROD invented Bayesian conditioning or sequential design;
- candidate-ranking reversal must occur in every ecological problem;
- the controlled values constitute empirical ecological validation.

The only demonstrated claim is existence: a candidate ranking based on a broader pre-data state distribution need not be preserved after current evidence restricts the admissible mechanism region.

## Reproduce

```bash
python -m causal_model.postdata_reprioritization_witness
pytest -q tests/test_postdata_reprioritization_witness.py
```
