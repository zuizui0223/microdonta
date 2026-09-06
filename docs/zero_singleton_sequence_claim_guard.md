# Zero-singleton versus sequence-information claim guard

Status: internal claim-ceiling note for the active MROD submission. This file does not define a new optimization method and is not part of frozen G2 performance evidence.

## Core distinction

For a declared current admissible region `A` and singleton candidate observations `Q_1,...,Q_m`, the publication-level immediate values are

```text
V(Q_j)=I(S;Q_j|A)/K.
```

If every singleton value is zero,

```text
I(S;Q_j|A)=0 for every j,
```

then the current positive-singleton greedy policy has no informative immediate move. This is a **validated one-step information stop** only.

It is not, in general, a proof that combinations of the declared observations contain no mechanism information. Synergistic examples exist, including the executable XOR witness in `causal_model/zero_singleton_synergy_witness.py`, for which

```text
I(S;Q_1|A)=0,
I(S;Q_2|A)=0,
I(S;Q_1,Q_2|A)=1 bit.
```

After either first observation is realised, the second has positive conditional information. The current positive-only singleton rule would stop too early on this system.

## Stronger sequence-level statement

Let `Q_C` denote a coherent joint predictive vector containing all declared candidate outcomes. If

```text
I(S;Q_C|A)=0,
```

then any transcript constructed solely from those outcomes also has zero mechanism information by the data-processing inequality. This licenses a **sequence-information limit** relative to the declared candidate vocabulary.

If joint information is positive while singleton values are all zero, the correct diagnosis is a non-myopic bundle/sequence-design problem, not an in-principle information limit. Positive joint information alone does not identify the best acquisition order, cost-optimal policy or globally optimal adaptive strategy.

## Prior-art / novelty ceiling

MROD does not claim novelty for synergistic information, non-myopic Bayesian experimental design, batch information acquisition or adaptive-submodular design. The contribution here is narrower: the limitation-reporting contract must not overinterpret a zero-singleton greedy stop as a sequence-level impossibility.

## Submission rule

Do not submit text that equates

```text
max_j I(S;Q_j|A)=0
```

with

```text
I(S;Q_C|A)=0.
```

The former is a one-step statement. The latter is a stronger joint-information statement.
