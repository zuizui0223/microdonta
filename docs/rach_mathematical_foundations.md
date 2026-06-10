# RACH: Mathematical Foundations

This document states the well-definedness conditions, metric bounds, and Monte Carlo consistency properties of the RACH admissible causal region.

> **Note:** The theorem below proves admissibility well-posedness, not causal truth.

---

## Admissible causal region

Let:

```text
Θ    — latent ecological parameter space (compact, finite-dimensional)
S    — causal switch space {0,1}^K  (finite, 2^K elements)
G    — constraint grammar: G : Θ → {0,1}  (measurable)
f    — generative simulator: f : X × Θ × S → Z  (measurable)
P_sim — pattern extractor: P_sim : Z → P  (measurable)
P_obs — empirical observation map: P_obs : Y → P
d    — distance function: d : P × P → ℝ_≥0  (satisfies d ≥ 0 and d(p,p) = 0)
ε    — tolerance threshold: ε ≥ 0
```

The **admissible causal region** is:

```text
A_ε(y_obs, x_obs)
=
{ (θ, s) ∈ Θ × S :  G(θ) = 1
                    and  d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

---

## Well-posedness

**Proposition 1 (non-emptiness under mild conditions).**
If the prior over Θ × S has full support on G^{-1}(1) × S, and the generative process f is continuous in θ for fixed s, then for any ε > 0 there exists a measurable set A_ε with positive prior measure.

*Proof sketch:* By continuity of f and measurability of d ∘ P_sim ∘ f, the set {(θ, s) : d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε} is closed in Θ for each s ∈ S. Under full-support prior, this set has positive measure for any ε > 0 that includes at least one point in the range of d. □

---

## Causal admissibility

Given a sample {(θ^i, s^i)}_{i=1}^N drawn from the prior restricted to A_ε, the empirical causal admissibility is:

```text
CA_j^N  =  (1/N) Σ_{i: (θ^i, s^i) ∈ A_ε}  s_j^i
```

**Proposition 2 (Monte Carlo consistency).**
As N → ∞, CA_j^N → CA_j = E[s_j | (θ,s) ∈ A_ε] almost surely, by the strong law of large numbers applied to the restricted prior.

---

## Causal degeneracy and resolvability

Let S = (s_1, ..., s_K) be the switch vector. Define:

```text
D_RACH  =  H(S | A_ε)  =  -Σ_{s ∈ {0,1}^K}  P(S=s | A_ε) log_2 P(S=s | A_ε)
```

where P(S=s | A_ε) is the empirical frequency of switch combination s in the accepted sample.

The maximum degeneracy under a uniform prior over S is K = log_2(2^K) bits.

```text
R_RACH  =  1 - D_RACH / K  =  1 - H(S|A_ε) / K
```

R_RACH ∈ [0, 1]. R_RACH = 0 means no resolution (uniform posterior over switch combinations). R_RACH = 1 means complete resolution (unique switch state identified).

**Note:** R_RACH uses K = log_2|S| as the normaliser, not H(S_prior). This ensures R_RACH is bounded in [0,1] and is interpretable as the fraction of maximum-possible switch entropy resolved.

---

## Observation contribution

For a pattern observation set O = {o_1, ..., o_M}, define:

```text
OC_k  =  R_RACH(O) - R_RACH(O \ {o_k})
```

OC_k measures how much pattern o_k contributes to causal resolvability. OC_k > 0 means removing o_k would reduce resolution. OC_k < 0 means removing o_k would improve resolution (pattern o_k confounds inference under current ε).

**Implementation requirement:** OC_k must be computed from all evaluated draws (accepted + rejected), not only accepted draws. When o_k is removed (LOO), some previously-rejected draws may become accepted. Using only accepted rows underestimates OC_k because it misses these re-accepted draws.

---

## Metric bound on ε

If d is a proper metric (d(p,q) = 0 ⟺ p = q, symmetry, triangle inequality), then as ε → 0, A_ε shrinks to the set of (θ, s) that exactly reproduce the observed patterns. As ε → ∞, A_ε expands toward the full prior support constrained only by G(θ) = 1.

The parameter ε controls the admissibility tolerance. In practice, ε is set via an acceptance rule (e.g. `weighted_lax`: weighted match rate ≥ 0.8) rather than a fixed metric distance.

---

## Limitations of this formulation

- The results depend on the prior over Θ × S, the constraint grammar G, the simulator f, the pattern extractors P_sim and P_obs, and the distance function d.
- A_ε is not a posterior in the Bayesian sense unless d is derived from a likelihood function. It is a compatibility region under approximate simulation.
- CA_j, D_RACH, R_RACH, OC_k, and NOV are all relative to the specified model components. They quantify admissibility within the model, not causal truth in nature.

See [`docs/literature_comparison.md`](literature_comparison.md) for a full discussion of validity and limitations.
