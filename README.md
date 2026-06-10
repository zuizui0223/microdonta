# RACH: Causal Admissibility and Degeneracy Framework

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH is a **causal admissibility and degeneracy framework** for ecological systems. It estimates which latent causal mechanisms remain admissible under biological constraints and independent observations, and quantifies whether the available observations are sufficient to resolve competing mechanisms.

English:

> RACH defines the admissible causal region and quantifies causal admissibility, causal degeneracy, and causal resolvability under biological constraints. It does not select the best model. It estimates which mechanisms remain admissible and how degenerate the causal explanation is.

Japanese:

> RACHは、生物学的制約と独立観測データのもとで、どの潜在因果メカニズムが許容されるか、また現在の観測集合がどの程度それらを識別できるかを定量化する、生態学的因果許容性・因果縮退性解析フレームワークである。RACHは単一モデルを選ぶのではなく、許容因果領域を推定し因果縮退性を定量化する。

**RACH is not a combination of ABM, ABC, and POM.** ABM, ABC, and POM are computational components used to approximate the admissible causal region A_ε. The framework is defined by its inferential objects: causal admissibility (CA_j), causal degeneracy (D_RACH), causal resolvability (R_RACH), observation contribution (OC_k), and next-observation value (NOV).

This repository implements a worked example using the Izu Islands population system of *Campanula punctata* / シマホタルブクロ. The Campanula model is an example, not the definition of RACH.

**Mathematical foundations:** see [`docs/rach_mathematical_foundations.md`](docs/rach_mathematical_foundations.md) for the well-definedness, metric-bound, and Monte Carlo consistency proof. The theorem proves admissibility well-posedness, not causal truth.

**Literature comparison and novelty:** see [`docs/literature_comparison.md`](docs/literature_comparison.md) for how RACH relates to Pattern-Oriented Modeling, ABC, ABC model choice, ABM/IBM, structural causal models, and Value of Information, and for defensible novelty and limitation claims.

---

## Formal definition

The core RACH object is the **admissible causal region**:

```text
A_ε(y_obs, x_obs)
=
{(θ, s) ∈ Θ × S :
  G(θ)=1,
  d(P_sim(f(x_obs; θ, s)), P_obs(y_obs)) ≤ ε }
```

where:

```text
x_obs  = fixed empirical context used as simulator input
θ      = latent ecological parameters to infer or marginalise over
s      = causal switch state, s ∈ {0,1}^K
G(θ)   = ecological constraint grammar
f      = generative ecological dynamics
P_sim  = pattern extractor for simulated output
P_obs  = pattern extractor for empirical observations
y_obs  = independent empirical observations used for ABC/RACH acceptance
d      = distance between simulated and observed pattern spaces
ε      = tolerance threshold
```

The key inference is not a best-model label, but the admissible region and its information structure.

---

## Core workflow

```text
1. Define biological axioms and ecological constraint grammar
2. Define fixed empirical context x_obs
3. Sample latent parameters θ within biologically admissible ranges
4. Sample causal switch states s ∈ {0,1}^K
5. Run generative simulation f(x_obs; θ, s)
6. Extract comparable patterns P_sim and P_obs
7. Accept samples whose distance to independent y_obs is ≤ ε
8. Estimate CA_j, D_RACH, R_RACH, OC_k, and NOV(q)
```

RACH is **not** manual parameter tuning. The goal is to identify the subset of latent parameter–mechanism space that is both biologically coherent and compatible with independent observations.
