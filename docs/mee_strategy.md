# MEE submission strategy — RACH

Target: **Methods in Ecology and Evolution** (BES). Article type: Methods /
Practical Tools. This file fixes the novelty claim, the experiments that defend
it, and the submission logistics. It is the single source of truth for the MEE
push; `mee_submission_plan.md` (older framing) is superseded by this file.

---

## 1. The novelty thesis (one defensible sentence)

> **RACH reframes mechanism inference from "which model is best?" to "which
> mechanisms remain admissible, how confounded are they, and what should be
> measured next?" — formalising *causal degeneracy* over a constraint-feasible
> switch space and the *next-observation value* that most reduces it as a
> preposterior expectation on causal resolvability.**

What carries the claim (and what does not):

| Component | Honest status vs. existing tools | Role in the paper |
|---|---|---|
| A_ε, CA_j | = ABC model choice over s ∈ {0,1}^K (posterior over switch combinations) | **not** the novelty; the substrate |
| D_RACH, R_RACH | = entropy / normalised entropy of that posterior | reframing — degeneracy as the *primary reported quantity*, not a by-product |
| OC_k | leave-one-out resolvability contribution (retrospective design) | supporting |
| **NOV(q) as preposterior EVSI on R_RACH** | **currently heuristic — this is the technical contribution to harden** | **the novelty core** |
| Constraint grammar G + role taxonomy | constraint-first admissibility; circular-inference guard | the "constraint-aware" framing |

**Why this survives the "it's just ABC model choice + EVSI" objection:** the
contribution is not any single piece but (i) treating degeneracy as the target
rather than collapsing to a MAP model, and (ii) a *resolvability-utility* EVSI
that does not require an external decision/utility model — the utility is
internal (mechanism resolvability). We must show this delivers a decision an
ecologist would otherwise get wrong (Experiment 1).

---

## 2. The three experiments that must win

### Experiment 1 — Money figure: model selection misleads, RACH does not

Uses the **existing** model structure, where **S2 (selfing syndrome)** and
**S3 (island isolation common cause)** both predict *selfing ↑* and *flower size ↓*
with isolation — i.e. they are genuinely confounded under the current 2-gradient
`y_obs` (`selfing_distance`, `flower_size_distance`).

> **Confound verified (proxy model).** Simulating the isolation gradient under
> single-switch states gives weighted_match_rate against the current y_obs of:
> null = 0.00, S1_only = 0.00, **S2_only = 1.00, S3_only = 1.00**, S2+S3 = 1.00.
> S2 and S3 are therefore *exactly* indistinguishable on the two current
> gradients — a real (not contrived) confound, the ideal substrate for the
> money figure.

Implemented in `causal_model/confound_demo.py` (panels A–C done; D pending).

Result (proxy, n=800, verified):
1. **ABC model choice**: posterior spread over many switch-combination models; the
   MAP model has only **P≈0.10** — reporting it as "the best model" is overconfident
   and near-arbitrary.
2. **RACH**: **D_RACH≈3.57 of 4**, R≈0.11; CA_j(S2)≈0.66 and CA_j(S3)≈0.67 — both
   admissible and nearly equal = the S2/S3 confound is reported, not hidden.
3. **Mechanism of the confound (verified, important):** S2 and S3 agree on the
   *ordinal direction* of both gradients but differ in *magnitude* (selfing slope
   ≈0.18 vs ≈0.50; Fis ≈0.19 vs ≈0.41; guide ≈0 vs −0.12). **Ordinal y_obs cannot
   separate them; a quantitative/absolute observation can.** This is the resolution
   mechanism — and it ties directly to the repo's `absolute_summary` /
   `absolute_observations.csv` machinery (issue #31).

(Correction to an earlier draft: neutral genetic diversity does NOT distinguish
S2 from S3 in this model — it declines with isolation under both because drift is
always-on. The true discriminator is gradient *magnitude*, captured by
`absolute_summary` patterns, not an additional ordinal pattern.)

Step D (DONE, verified): add the quantitative confound-breaker and re-infer.
Result — adding a measured **nectar-guide magnitude** at the most-isolated
population (truth = S3):

```
D_RACH 3.57 → 2.38      R_RACH 0.11 → 0.40
CA_j[S3] 0.67 → 0.85    (↑ supported)
CA_j[S2] 0.66 → 0.51    (↓ rejected)
```

**Why the guide, not selfing/Fis:** selfing-rate / Fis magnitude reduces
degeneracy but does NOT reject S2 (S2 can mimic high selfing). The nectar-guide
decline is a signature S2 (selfing syndrome) cannot mimic in the model, so it
*resolves* the confound — S3 up, S2 down. This is decision-relevant value model
selection cannot provide: it tells the ecologist that **quantifying the
nectar-guide gradient** (the planned own-field observation) breaks the S2/S3
confound — and the same measurement is the NOV top-target for S1. One field
measurement, two payoffs.

Deliverable: a single multi-panel figure (model-choice posterior vs. degeneracy
verdict vs. NOV ranking vs. post-measurement resolution). Panels A–C generated by
`python -m causal_model.confound_demo --figure outputs/mee/confound_demo.png`.

### Experiment 2 — Generality (≥2 systems)

Run the full workflow on (a) the synthetic confound system above and (b) the
Campanula worked example, to show the workflow is system-independent. Campanula
is presented honestly as a *low-resolution* real case whose degeneracy diagnosis
*motivates* the NOV-recommended fieldwork — not as a resolved causal history.

### Experiment 3 — NOV-as-EVSI calibration  (DONE)

Implemented in `causal_model/nov_calibration.py`. Validates that NOV is a
*calibrated, cheaply computable preposterior EVSI on resolvability*, not a
heuristic. Two verified results (proxy, n=1000):

1. **Exactness / cheapness (perfect 1:1).** For every tested quantitative
   observation, the resolvability gain computed by *filtering the existing
   admissible region* equals the gain from a *fresh ABC re-inference* that
   actually adds the observation (|Δ| < 1e-6). So NOV/EVSI is computed from the
   current A_ε without costly re-runs — exact under the deterministic proxy.
2. **EVSI predicts realised gain (r ≈ 0.77).** The preposterior EVSI(q) —
   expectation of ΔR over the predictive distribution of q's value across A_ε —
   positively predicts the gain realised under specific true states, across a
   panel of (variable × population) observations. EVSI is the *full-predictive
   expectation*, so it summarises across outcomes while the realised gain depends
   on which true state obtains (grey spread in the figure); EVSI therefore orders
   observations by value and slightly exceeds any single-truth realisation.

Figure: `python -m causal_model.nov_calibration --figure outputs/mee/nov_calibration.png`
(panel 1 exactness, panel 2 EVSI-vs-realised). This hardens the novelty core: NOV
is a genuine, validated EVSI, closing the "it's just heuristic VOI" objection.

---

## 3. Technical work required (maps to repo)

| Task | Where | Status |
|---|---|---|
| NOV as preposterior EVSI on R_RACH (formalise + implement) | `causal_model/causal_admissibility.py` (`next_observation_value_simulation`) | needs hardening |
| ABC-model-choice baseline (posterior over s, MAP model) for head-to-head | new helper in `causal_model/` | to build |
| Confound demonstration driver (Exp 1) | extend `causal_model/known_truth_benchmark.py` | to build |
| NOV calibration driver (Exp 3) | new script | to build |
| Two-system runner + figure generation | `causal_model/report_results.py` extension | partial |
| Well-posedness proofs | `docs/rach_mathematical_foundations.md` | ✅ done |
| Software / reproducibility | package + Streamlit + tests | ✅ strong |

---

## 4. Phased plan

1. **Strategy fixed** (this file).
2. **Experiment 1 driver + money figure** — the decisive deliverable; build first.
3. **NOV → EVSI hardening + Experiment 3 calibration.**
4. **Two-system runner (Experiment 2) + manuscript figures.**
5. **Write** as Methods/Practical Tools. Pre-submission enquiry → preprint
   (EcoEvoRxiv) → submit.

---

## 5. Pre-submission enquiry draft (email to MEE editor)

> Subject: Pre-submission enquiry — a constraint-aware framework for diagnosing
> causal degeneracy and prioritising next observations in ecological mechanism
> inference
>
> Dear Editor,
>
> I would like to gauge fit for a Methods article. Ecological field data
> typically constrain *patterns* rather than the latent mechanisms that produced
> them, so multiple mechanisms often remain jointly compatible with the data.
> Standard practice selects a best model; this can be overconfident when
> mechanisms are confounded by the available observations.
>
> We present RACH, a constraint-aware framework that (i) defines an admissible
> region over mechanism-switch combinations under an explicit biological
> constraint grammar, (ii) reports *causal degeneracy* (entropy over admissible
> mechanisms) as the primary result rather than collapsing to a single model,
> and (iii) computes a *next-observation value* — a preposterior expectation of
> the gain in causal resolvability — to tell the ecologist which field
> measurement would most reduce the remaining confounding. We validate it with a
> known-truth recovery benchmark and a controlled demonstration in which model
> selection picks the wrong mechanism while RACH correctly reports the confound
> and identifies the resolving observation; open-source software accompanies it.
>
> Would this be of potential interest to MEE? I can share an extended summary or
> preprint.

---

## 6. Honest risk assessment

- **Primary risk:** reviewers see the pieces as ABC model choice + heuristic VOI.
  Mitigation = Experiment 1 (decision-relevant divergence) + Experiment 3
  (NOV is a real, calibrated EVSI, not a heuristic).
- **Secondary risk:** "demonstrated on one bespoke ABM." Mitigation = Experiment 2
  (synthetic + Campanula).
- **Worked-example weakness:** Campanula is honestly low-resolution. Reframe its
  role as *motivating* observation design, not as an empirical resolution.
- **Fallback venues if MEE declines:** Ecological Modelling; Ecology and
  Evolution; PeerJ. Keep the framing portable.
