# RACH: Causal Admissibility and Degeneracy Framework

**RACH** stands for **Restricted Admissible Causal Hypotheses**.

RACH is a **causal admissibility and degeneracy framework** for ecological systems. It estimates which latent causal mechanisms remain admissible under biological constraints and independent observations, and quantifies whether the available observations are sufficient to resolve competing mechanisms.

English:

> RACH defines the admissible causal region and quantifies causal admissibility, causal degeneracy, and causal resolvability under biological constraints. It does not select the best model. It estimates which mechanisms remain admissible and how degenerate the causal explanation is.

Japanese:

> RACHは、生物学的制約と独立観測データのもとで、どの潜在因果メカニズムが許容されるか、また現在の観測集合がどの程度それらを識別できるかを定量化する、生態学的因果許容性・因果縮退性解析フレームワークである。RACHは単一モデルを選ぶのではなく、許容因果領域を推定し因果縮退性を定量化する。

**RACH is not a combination of ABM, ABC, and POM.** ABM, ABC, and POM are computational components used to approximate the admissible causal region A_ε. The framework is defined by its inferential objects: causal admissibility (CA_j), causal degeneracy (D_RACH), causal resolvability (R_RACH), observation contribution (OC_k), and next-observation value (NOV).

This repository implements a worked example using the Izu Islands *Campanula microdonta* system (シマホタルブクロ). Older literature may refer to the broader *C. punctata* complex; here シマホタルブクロ is treated as *Campanula microdonta*, with mainland ホタルブクロ / *C. punctata* used only as a related comparison context. The Campanula model is an example, not the definition of RACH.

**Worked-example provenance (important).** Only quantities actually measured in the Inoue series are used as independent ABC observations (`observed_target`): **flower size** (Amano & Inoue 1986) and **selfing/outcrossing rate** (Inoue 1990). **Pollinator (Bombus) availability** is fixed context `x_obs`. **Nectar guide** is a *planned own-field observation* (no per-population Inoue measurement exists) and is tracked as a NOV candidate for S1 until collected. **Herkogamy** is treated as a latent dichogamy / delayed-selfing mechanism (this species is protandrous with secondary pollen presentation, so static anther–stigma herkogamy is not the operative trait), not an independent observation. **Fis** remains excluded until an independent genetic estimate is source-confirmed, because the current simulator's Fis proxy is partly generated from selfing rate and would otherwise double-count selfing evidence. Numeric endpoint values are pending transcription from the primary PDFs; directional relations are used in the meantime.

**Falsification-first next observations.** The Campanula NOV list includes explicit falsification candidates for each causal switch: S1 guide-masked Bombus choice, S2 autonomous-selfing/bagging tests, S3 neutral-marker isolation structure, and S5 halictid substitution/exclusion tests. These are candidate future `observed_target` rows only after measurement; until then they prioritise non-circular data collection.

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

---

## Known-truth recovery benchmark

The benchmark tests whether RACH ABC inference recovers a **known** causal switch state when synthetic observations are generated by the same proxy model under that state.

**Epistemic note:** This is a *specified-simulator recovery benchmark*, not a causal proof.  A high recovery score means RACH is self-consistent under synthetic data — it does not mean the recovered switch state is the true ecological mechanism.

### Run

```bash
# Default: 8 true states × 3 noise levels × 200 draws
python -m causal_model.known_truth_benchmark

# Fast smoke test
python -m causal_model.known_truth_benchmark --n-attempts 50 --noise-rates 0.0 --cases all_off,S1_only

# Full sweep including n_attempts convergence
python -m causal_model.known_truth_benchmark \
    --n-attempts 200 \
    --noise-rates 0.0,0.1,0.2 \
    --n-attempts-sweep 50,100,200,500 \
    --output-dir outputs/known_truth_benchmark
```

### Output files (`outputs/known_truth_benchmark/`)

| File | Content |
|---|---|
| `known_truth_cases.csv` | One row per (case × switch): CA_j, predicted_on, true_on, correct, backend metadata |
| `known_truth_summary.csv` | One row per case: accuracy, precision, recall, F1, mean_abs_CA_error, D_RACH, R_RACH, backend metadata |
| `recovery_by_noise.csv` | Metrics averaged by noise_rate |
| `recovery_by_n_attempts.csv` | Metrics averaged by n_attempts (for convergence sweep) |
| `recovery_by_backend_pair.csv` | Metrics averaged by generator→inference backend pair |

### Cross-backend recovery (simulator robustness)

The benchmark can vary the **generator** backend (how synthetic `y_obs` is
produced) and the **inference** backend (which simulator runs RACH inference):

```bash
# proxy -> proxy: self-consistency (same simulator generates and infers)
python -m causal_model.known_truth_benchmark --generator-backend proxy --inference-backend proxy

# abm -> proxy: simulator robustness — data from the stochastic IBM, proxy inference
python -m causal_model.known_truth_benchmark --generator-backend abm --inference-backend proxy \
    --abm-generations 30 --abm-population-size 120 --abm-replicates 2

# abm -> abm: high-fidelity generation and inference (slowest)
python -m causal_model.known_truth_benchmark --generator-backend abm --inference-backend abm
```

**Interpretation.** `proxy→proxy` is a *self-consistency* check: if the data
were exactly the proxy model, can RACH recover the known switch state?
`abm→proxy` and `abm→abm` are stronger *simulator-robustness* tests: if the data
come from a higher-fidelity stochastic ABM, does the pipeline still recover the
known state under model misspecification? **This remains a specified-simulator
recovery benchmark, not proof of real-world causal truth.**

## Report generation (manuscript artifacts)

Turn benchmark and ensemble outputs into stable summary documents and figures:

```bash
# One command — auto-runs a quick benchmark/ensemble if their CSVs are missing
python -m causal_model.report_results

# Use existing benchmark outputs, regenerate the ensemble scan
python -m causal_model.report_results --run-ensemble \
    --benchmark-dir outputs/known_truth_benchmark \
    --ensemble-dir outputs/ensemble \
    --output-dir outputs/reports
```

Outputs under `outputs/reports/`: `benchmark_summary.md`, `ensemble_summary.md`,
`results_summary.md`, and `figures/*.png`. Reports are manuscript-safe — they
distinguish synthetic known-truth recovery from empirical admissibility
inference and never claim real-world causal truth. (Figures require
`matplotlib`; they are skipped with a notice if it is unavailable.)

### Tests

```bash
pytest tests/test_known_truth_benchmark.py tests/test_cross_backend_benchmark.py \
       tests/test_ensemble_robustness.py tests/test_report_results.py -v
```
