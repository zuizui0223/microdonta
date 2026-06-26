# Restricted expected H-alpha multiplier theorem

## Why a restriction is necessary

A universal statement that local genetic diversity always declines is false in
the declared simulator. Migration can mix patch frequencies and increase local
H-alpha, and selection can move an allele frequency toward one half.

This theorem therefore works on a declared high-allele interval rather than
claiming a global contraction.

## Declared region

At one update, suppose every patch satisfies

```text
p_min <= p_j <= p_max,
1/2 <= p_min <= p_max < 1,
q_j >= q_min,
N_j,next <= N_max.
```

Assume

```text
high_interaction_benefit >= 0,
selection_strength >= 0,
f_min = 1 + selection_strength [W(1; q_min)-threshold] > 1.
```

The last condition means the high allele is uniformly favoured over the stated
interaction region.

## Selection and migration

The simulator's selected frequency is

```text
s(p,f) = p f / [p f + (1-p)].
```

Thus every patch after selection has

```text
p_j^sel >= s_min = s(p_min, f_min) > p_min >= 1/2.
```

Census-weighted migration is a convex combination of selected frequencies, so
it cannot lower this common post-selection lower bound:

```text
p_j^mig >= s_min.
```

Because

```text
H(p) = 2p(1-p)
```

is decreasing on `[1/2,1]`, every post-migration local heterozygosity is at
most `H(s_min)`.

## Current H-alpha lower envelope

The current patch frequencies are no larger than `p_max`, so their local
heterozygosities are at least `H(p_max)`. Any positive census-weighted mean
therefore satisfies

```text
H_alpha,current >= H(p_max).
```

## Sampling

For `M_j` gene copies, Wright--Fisher sampling gives exactly

```text
E[H_j,next | p_j^mig] = (1 - 1/M_j) H(p_j^mig).
```

With

```text
M_j <= M_max = max(2, round_upper(2 effective_fraction N_max)),
```

we obtain

```text
E[H_alpha,next]
<= (1 - 1/M_max) H(s_min).
```

Combining the two envelopes gives the conditional one-step multiplier:

```text
E[H_alpha,next]
<= lambda_bar H_alpha,current,

lambda_bar = (1 - 1/M_max) H(s_min) / H(p_max).
```

The code reports a contraction certificate only when

```text
lambda_bar < 1.
```

## Interpretation

A narrow high-frequency interval can produce `lambda_bar < 1`: directional
selection plus sampling dominates any heterogeneity-induced increase in local
H-alpha.

A wide interval may give `lambda_bar >= 1`. That does not disprove selection or
drift; it means this theorem cannot rule out a migration/heterogeneity increase
in local H-alpha over one step.

## Limits

This is a one-step conditional theorem. It does not prove:

- that the allele interval is invariant after independent finite sampling;
- a multi-generation multiplier without a separately proved interval-retention
  event;
- H-gamma or F_ST contraction;
- realised high-trait persistence;
- a genetic lead ordering by itself.

It supplies the previously missing `lambda_bar` ingredient for L4 whenever a
separate finite-horizon region certificate establishes the stated interval at
each step.