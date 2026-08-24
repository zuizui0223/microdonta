# Publication claim graph

Status: publication boundary for the theorem-first reorganisation branch,
2026-08-24.

This document turns the mixed repository into a claim–evidence graph. It is a
submission map, not a claim that every retained module belongs in one paper.

## 1. Repository status graph

~~~mermaid
flowchart TD
    R["microdonta repository"] --> A["Active: RACH methods"]
    R --> B["Active but separate: Campanula/Izu"]
    R --> C["Supplementary: ABM robustness"]
    R --> D["Separate: eco-genetic criticality"]
    A --> M["Primary submission: MEE Methods"]
    B --> E["Future empirical paper after channel-resolved data"]
    C --> M
    D --> X["Independent research program"]
~~~

| Node | Scientific role | Current evidence | Publication disposition |
|---|---|---|---|
| RACH core | Retain all robustly admissible causal programs and rank resolving observations | causal_admissibility.py, causal_replaceability.py, rach_seq.py, known_truth_benchmark.py | Main paper |
| Channel-identifiability theory | Establish the exact observation boundary for W(z)=F(z)E(z) | channel_identifiability_theory.py, proxy_calibration_theory.py, N1–N4 proofs | Main paper, mathematical foundation |
| One-step colonization bridge | Show one exact life-cycle projection of W=FE | colonization_recruitment_factorization.py and projection ledger | Main worked model or Supplement |
| Rule-transition ABMs | Test whether restricted conclusions persist with extra processes | spatial, defense, and colonization backends plus endpoint sensitivity | Supplementary robustness only |
| Campanula/Izu | Show what published island patterns cannot identify and which measurements are required | campanula_real_data.py and examples/campanula_izu | Prospective worked example only |
| Attraction-trait model | Optional simulator backend used by prospective workflows | attraction_trait_model | Retain as software support; exclude from primary evidence |
| Eco-genetic criticality | Independent criticality, fragmentation, and genetic-lag program | eco_genetic_criticality plus matched docs/examples/tests | Separate physical package and publication program |
| Legacy | Historical reproducibility | legacy modules and archived documents | Exclude from new claims |

## 2. Claim–evidence graph

~~~mermaid
flowchart TD
    P["Observed ecological pattern"] --> N1["N1: net-only observations do not identify the changed channel"]
    N1 --> N2["N2: W plus one exact channel identifies both relative changes"]
    N2 --> N3["N3: a stable-calibration proxy is sufficient"]
    N3 --> N4["N4: calibration drift restores non-identifiability"]
    N4 --> R["RACH retains all admissible explanations"]
    R --> V["NOV / RACH-SEQ ranks observations that cut the remaining confounding"]
    V --> B["Ground-truth and random-system benchmarks"]
    V --> C["Campanula measurement design"]
~~~

The publishable logical chain is:

1. **Boundary theorem:** trait-space geometry and every other function of net
   performance W alone are structurally non-identifying under the positive
   multiplicative model.
2. **Minimal remedy:** W plus one resolved channel, or a proxy whose conversion is
   stable across the comparison, is sufficient for relative channel-change
   identification.
3. **Operational method:** when those measurements are absent, RACH does not choose
   a winner. It returns the admissible causal region, degeneracy, and
   replaceability structure.
4. **Observation design:** NOV and RACH-SEQ select the next measurement expected to
   reduce that unresolved structure.
5. **Validation:** controlled truth and random-system benchmarks test recovery,
   false exclusion, false invariants, calibration, and observation efficiency.
6. **Ecological projection:** an exact one-step colonization factorisation shows
   how the theorem can be earned for a declared life-cycle output. Campanula shows
   why published pattern-only evidence remains non-identifying.

## 3. Evidence classes and allowed language

| Evidence class | What it establishes | Allowed manuscript language | Language to avoid |
|---|---|---|---|
| Algebraic proof | Exact result inside stated positive factorisation | proves, is sufficient, is non-identifying | universally identifies nature |
| Implementation test | Code agrees with the algebra on tested inputs | regression-checked, implementation-verified | simulation proves theorem |
| Synthetic benchmark | Algorithmic recovery under declared generators | recovers under benchmark, controls error under design | empirically validated in ecology |
| Full ABM | Robustness or counterexample under additional processes | persists or fails within sampled model family | theorem applies automatically |
| Published Campanula pattern | Existing biological context and missing observation diagnosis | competing explanations remain; motivates measurements | identifies pollination or establishment channel |
| Future field data | Not yet present | preregistered target, prospective test | result, validation, confirmation |

## 4. Primary submission decision

**Target:** Methods in Ecology and Evolution, Methods / Practical Tools.

**One-sentence claim:**

> RACH converts structural non-identifiability from a hidden model-selection
> failure into an explicit admissible set and a minimal next-observation design,
> with exact channel-identifiability boundaries and controlled synthetic
> validation.

**Manuscript title direction:**

> RACH: from causal non-identifiability to next-observation design in ecological
> mechanism inference

### Main-text spine

| Section | Required content | Repository source |
|---|---|---|
| 1. Problem | Ecological patterns can be functions of net performance and therefore cannot identify the changed channel | docs/channel_identifiability_theorem.md |
| 2. Exact boundary | N1–N4 and the stable-calibration condition | channel_identifiability and proxy-calibration theory |
| 3. RACH method | admissible region, degeneracy, replaceability, NOV, RACH-SEQ | causal_admissibility.py, causal_replaceability.py, rach_seq.py |
| 4. Validation | known-truth recovery, calibration, error rates, random-system generality | known_truth_benchmark.py plus benchmark runners |
| 5. Projection | exact one-step colonization bridge; explicit projection ledger | colonization_recruitment_factorization.py, theorem_projection_ledger.py |
| 6. Worked design | Campanula as a prospective observation-design example, without empirical channel attribution | campanula_real_data.py, examples/campanula_izu |
| 7. Discussion | scope, stochastic approximation, grammar dependence, and empirical calibration requirements | interpretation boundaries across docs |

### Move out of the main text

- T1–T4 relationship-loss comparative statics: Supplementary motivation unless
  directly required by a main figure.
- Spatial, defense, and multistep colonization endpoint sweeps: Supplementary
  robustness/counterexample material.
- Bergmann, Allen, Foster, and Gloger panels: remove from the submission unless
  every encoding is source-verified and they add a benchmark property not already
  covered by random-system validation.
- Structure-discovery extension: future paper or Supplement; it changes the
  estimand from named causal programs to graph structure and currently dilutes
  the central method.
- Streamlit and tutorial prototypes: software demonstration, not scientific
  evidence.

## 5. Separate publication boundary

The Campanula/Izu study is not the empirical validation paper yet. It becomes a
separate empirical submission only after the same trait domain and census scale
provide:

1. trait-specific total performance W;
2. one direct channel or a stable/calibrated proxy;
3. before/after or among-regime calibration evidence;
4. a declared recruitment/reachability mapping;
5. uncertainty propagation on reconstructed relative channel changes.

Until then, its valid conclusion is an observation-design result: published
flower size, selfing, and pollinator-turnover patterns retain multiple channel
explanations.

## 6. Submission gates

| Gate | Pass condition | Current status |
|---|---|---|
| G1 Claim consistency | README, manuscript, figures, and code use the same theorem → RACH → observation-design story | **Pass:** theorem-first manuscript, README, and manifest aligned |
| G2 Benchmark validity | preregistered generators; recovery, false-exclusion, false-invariant, calibration, and budget curves reported | **Partial:** known-truth and generality code exist; final error-control table is not the manuscript spine |
| G3 Projection honesty | every ecological or ABM claim has exact / extension-required / not-applicable status | **Pass in ledger; manuscript integration pending** |
| G4 Worked-example evidence | all literature encodings are primary-source verified or clearly prospective | **Pass for prospective use:** provisional rule panels are excluded |
| G5 Reproducible submission | one command rebuilds main and supplementary figures and a clean environment passes tests | **Partial:** scope and boundary checks plus regression suite pass; final full figure rebuild remains |

The next implementation milestones are G2 and G5: freeze the benchmark design,
produce the final error-control and budget table, then rebuild the complete
figure bundle in a clean environment. Additional ecological examples should not
enter the primary manuscript before those gates pass.

## 7. Stop rules

- Do not infer a channel from contraction, shift, fragmentation, or persistence
  when the observation is only a function of W.
- Do not call an uncalibrated visit count or connectivity index a channel
  measurement.
- Do not use ABM agreement as proof of an algebraic theorem.
- Do not present Campanula as empirical validation before channel-resolved data
  exist.
- Do not use the separate eco-genetic package or application code as evidence for
  the RACH submission.
