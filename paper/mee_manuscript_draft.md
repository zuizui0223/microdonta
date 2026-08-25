# RACH: from causal non-identifiability to next-observation design in ecological mechanism inference

**Ruiqi Zhang**

Kyoto University, Kyoto, Japan

> **Working draft for Methods in Ecology and Evolution.** This theorem-first
> draft supersedes the pre-theorem manuscript archived under
> `paper/archive/`. Numerical benchmark statements remain subject to the final
> frozen submission run and table; pre-fix generality percentages are deliberately
> absent from this draft until replaced by protocol-tagged frozen outputs.

---

## Abstract

Ecological patterns can remain compatible with distinct mechanisms even when
measured without sampling error. We first establish an exact identifiability
boundary for positive trait performance (W(z)=F(z)E(z)). Any observation that
depends only on (W), including complete thresholded trait-space geometry,
cannot distinguish a change in (F) from the same trait-dependent change in
(E) (N1). Observing (W) plus either channel recovers the other (N2); an
unknown proxy calibration is sufficient for relative change only when it is
stable across the comparison (N3), whereas calibration drift restores
non-identifiability (N4). We then present Restricted Admissible Causal
Hypotheses (RACH), which retains every mechanism program compatible with a
declared grammar and observations and reports the remaining causal degeneracy.
For a future observation whose predictive outcomes are identified by the current
admissible region, its validated next-observation value is exactly the residual
mechanism–observation mutual information normalised by switch dimension,
`NOV(Q)=I(S;Q|A_ε)/K`; RACH-SEQ recomputes that information state after each
collected observation. A preregistered synthetic selection benchmark challenges
RACH-SEQ with mechanism-uninformative distractor measurements and compares its
observation choices with a matched random candidate-order baseline while tracking
hidden-truth false exclusion. An exact one-step colonisation-recruitment
factorisation demonstrates how the theorem can be earned for a specified
life-cycle output without being overextended to a multistep agent-based model.
Published Izu Islands *Campanula microdonta* patterns are used only as a
prospective observation-design example: the existing record does not identify a
vital-rate channel. RACH therefore turns structural non-identifiability into a
reportable admissible set and an explicit measurement design rather than a forced
model winner.

**Keywords:** structural identifiability, causal admissibility, degeneracy,
approximate Bayesian computation, mutual information, value of information,
observation design.

---

## 1. Introduction

Most ecological and evolutionary questions are about *mechanisms*. Does a floral
signal persist because pollinators select for it, because a correlated selfing
syndrome drags it along, or because island isolation drives many traits at once?
Field data, however, deliver *patterns* — trait values, interaction frequencies,
breeding-system and genetic summaries — and several distinct mechanisms can
generate the same pattern. The data are therefore typically **degenerate** with
respect to mechanism: the observation underdetermines the cause.

It is worth separating two ways a pattern-to-mechanism inference can be a
coincidence, because they call for different remedies. The first is a *sampling*
coincidence: the pattern itself may be noise — drift, small samples, or
measurement error rather than a real signal. This is a question about the data
and is addressed by replication, uncertainty propagation and the tolerance `ε`
below; it is not what this paper solves. The second is a *causal* coincidence
(confounding): the pattern is real, but more than one mechanism reproduces it, so
attributing it to any single mechanism is an unjustified leap. This second
problem is the one ecological practice most often hides, and the one RACH is built
to expose and act on.

The dominant response to mechanism questions is model selection: enumerate
candidate models and rank them, e.g. by approximate Bayesian computation (ABC)
model choice or information criteria. This is informative when models are
distinguishable, but under confounding it returns a "best" model whose posterior
probability is low and whose identity is sensitive to arbitrary analytic choices —
an overconfident answer to a question the data cannot resolve, and one whose
reliability for ABC model choice in particular has been questioned (Robert et al.
2011).

The first question must therefore be whether the available observation can
identify the mechanism at all. We make that boundary exact for a common
two-channel trait-performance model before introducing RACH. When the boundary
says that several explanations remain observationally equivalent, the
scientifically honest target is the **admissible region** of mechanisms and its
**degeneracy**, paired with a principled answer to *what to measure next*. RACH
formalises this:

1. mechanisms are binary **switches** `s ∈ {0,1}^K`; complex pathways are several
   switches ON, not a separate model label;
2. an explicit **constraint grammar** `G(θ)` removes biologically infeasible
   parameter combinations *before* data enter;
3. the **admissible causal region** `A_ε` is the set of constraint-feasible
   (θ, s) whose simulated patterns match independent observations within `ε`;
4. **causal degeneracy** `D_RACH = H(S | A_ε)` and **resolvability**
   `R_RACH = 1 − D_RACH/K` quantify how much the data resolve mechanism identity;
5. **observation contribution** `OC_k` measures how current patterns affect joint
   mechanism resolution, while a validated **next-observation value** `NOV(Q)`
   measures how much residual mechanism information a future observation is
   expected to remove.

RACH is not a new simulator and does not claim to recover causal truth. It
identifies which mechanisms remain admissible under stated assumptions, reports
how confounded they are, and prioritises observations that would reduce the
remaining ambiguity. In other words, it is a discipline against precisely the
causal-coincidence leap described above: where a natural-history reading would
propose one mechanism from a pattern, RACH returns the *set* of mechanisms the
pattern admits, plus the measurement that would justify narrowing it.

## 2. Exact channel-identifiability boundary

### 2.1 Observation class

Let trait-specific total performance be

[
W_i(z)=F_i(z)E_i(z), \qquad F_i(z)>0, E_i(z)>0,
]

for regimes (i\in{0,1}). A net-only observation is any deterministic
operator (O_i=\Phi(W_i)). This class includes the complete performance curve,
every viable set (\Omega_t={z:W_i(z)\ge t}), and every edge, breadth,
component count, or other geometry derived from those sets. The result is about
the information discarded by multiplication; it is not a statement that local
reproduction and establishment are biologically interchangeable.

### 2.2 N1: net-only observations cannot identify the changed channel

For any positive trait-dependent multiplier (a(z)), compare

[
P_F: (F_1,E_1)=(aF_0,E_0), \qquad
P_E: (F_1,E_1)=(F_0,aE_0).
]

Both yield (W_1(z)=a(z)F_0(z)E_0(z)) pointwise. Therefore
(\Phi(W_1)) is identical under the two distinct programs for every net-only
operator (\Phi). Complete trait-space geometry at every threshold cannot break
this symmetry. N1 is structural non-identifiability, not low statistical power.

### 2.3 N2: net performance plus one channel is sufficient

If (W_i) and (F_i) are observed, positivity gives the unique reconstruction
(E_i=W_i/F_i); observing (W_i) and (E_i) symmetrically gives
(F_i=W_i/E_i). The before/after ratios
(\rho_F=F_1/F_0) and (\rho_E=E_1/E_0) then distinguish
fecundity-only, establishment-only, mixed, and unchanged cases. No assumption
that exactly one channel changed is required.

### 2.4 N3–N4: proxy calibration is the operational boundary

Field assays are commonly proxies. Let (X_i(z)=q_i(z)F_i(z)). If
(q_0(z)=q_1(z)>0), then (X_1/X_0=F_1/F_0), and

[
\rho_E(z)=\frac{W_1(z)/W_0(z)}{X_1(z)/X_0(z)}.
]

Thus unknown absolute calibration is compatible with identification of relative
change when the conversion is stable (N3). If (q_1/q_0) is unconstrained, the
same observed (W) and (X) support arbitrarily different latent channel
changes (N4). A visit count or connectivity index is therefore not automatically
a channel measurement; its conversion must be stable or separately calibrated.

### 2.5 Scope and executable checks

N1–N4 require a declared positive multiplicative factorisation. Zeros,
additional channels, nonmultiplicative interactions, measurement error, and
regime-dependent observation maps require extensions. Algebraic proofs are in
`docs/channel_identifiability_theorem.md` and
`docs/proxy_calibration_theorem.md`; executable finite-grid constructions are
regression checks, not proofs. These results establish the boundary that RACH
operates on: when the observation map cannot select a unique program, retain the
compatible set and design a resolving observation.

## 3. RACH: admissible explanations and next-observation design

### 3.1 Formal object

```
RACH = (X, Y, Θ, S, G, f, P_sim, P_obs, d, ε, π)
A_ε(y_obs, x_obs) = { (θ,s) ∈ Θ×S : G(θ)=1, d(P_sim(f(x_obs;θ,s)), P_obs(y_obs)) ≤ ε }
```

`x_obs` is fixed context (not an inference target); `y_obs` are independent
observations; the pattern maps `P_sim, P_obs` send raw values into a common
observation space, and `d` is predeclared before inference. ABC approximates
`A_ε` by sampling (θ, s) from the prior `π` and retaining draws with `d ≤ ε`.
Full definitions and the worked-example instantiation are in `docs/rach_theory.md`
and `docs/rach_mathematical_foundations.md`.

### 3.2 The five quantities and their guarantees

`CA_j = P(s_j=1 | A_ε)`; `D_RACH = H(S|A_ε)`; `R_RACH = 1 − D_RACH/K`;
`OC_k = R_RACH(O) − R_RACH(O∖{k})`. For a future observation `Q` with an
identified predictive distribution under current `A_ε`,

[
NOV(Q)=E_Q\{R_RACH(A_ε|Q)-R_RACH(A_ε)\}.
]

We prove (Propositions 1–7, `docs/rach_mathematical_foundations.md`) that `A_ε`
is well-defined; `CA_j ∈ [0,1]`; `0 ≤ D_RACH ≤ K`; `0 ≤ R_RACH ≤ 1` (normalised
by the **maximum** switch entropy `K`, not a non-uniform prior entropy); and
`−1 ≤ OC_k ≤ 1`, with `OC_k` allowed to be negative. For the validated
current-region predictive map, Proposition 6′ gives the stronger exact identity

[
\boxed{NOV(Q)=I(S;Q\mid A_ε)/K}
]

and therefore

[
0\le NOV(Q)\le 1-R_RACH(A_ε)\le1.
]

Thus `NOV(Q)=0` exactly when the candidate observation carries no information
about the remaining mechanism vector under current `A_ε`; it attains the full
remaining uncertainty `1-R_RACH` exactly when observing `Q` completely resolves
that switch uncertainty. Empty `A_ε` makes conditional quantities non-estimable.
The finite-sample estimators are consistent under the stated assumptions.

### 3.3 NOV as mechanism–observation information

For a candidate observation `Q=g(θ,s)`, take the predictive outcome distribution
to be the pushforward of the restricted prior `π|A_ε` under `g`. Then

[
\begin{aligned}
NOV(Q)
&=E_Q[R_RACH(A_ε|Q)-R_RACH(A_ε)]\\
&=\frac{H(S|A_ε)-H(S|A_ε,Q)}{K}\\
&=\frac{I(S;Q|A_ε)}{K}.
\end{aligned}
]

This is the constructive resolvability-EVSI of RACH. It needs no external
decision utility because its utility is the inference's own residual mechanism
uncertainty. The information identity also explains why a coherent validated NOV
cannot be negative in expectation, even though an individual realised outcome
can increase conditional switch entropy and lower realised `R_RACH`.

Under a deterministic simulator, conditioning a fresh inference on `Q=q` accepts
exactly the filtered stored sub-region `A_ε|{Q=q}`. Hence no simulator re-run is
needed for the stored-region calculation. The implementation in
`causal_model/nov_evsi.py` independently constructs the empirical joint `(S,Q)`
table and checks `EVSI=I(S;Q|A_ε)/K`; `causal_model/nov_calibration.py` separately
checks stored-region filtering against fresh re-inference and realised-gain
calibration.

The executable public quantity follows the same information boundary. For an
explicit finite candidate outcome vocabulary, `next_observation_evsi` computes
`Pr(q|A_ε)` only when the outcome maps form a verified mutually exclusive and
exhaustive partition of current `A_ε`. If the maps overlap, are incomplete, or
required simulator outputs are absent, that predictive pushforward is not
identified by the stored region and the validated EVSI is reported as **not
estimable**. A declared outcome prior is not silently substituted and relabelled
as validated EVSI. The older target-switch heuristic is retained only as the
explicit compatibility helper `heuristic_next_observation_value`, not as the
publication NOV.

### 3.4 Sensitivity to ε and the prior, not rule selection

Because `R_RACH` depends on `ε` and the prior, RACH is reported for a single
*pre-specified* acceptance rule and distance. Varying (prior × ε × distance) is
treated only as a post-hoc **sensitivity check**, never as a way to choose the
rule: selecting the setting that maximises `R_RACH` would overfit `ε` and is
explicitly avoided. The reported result is the pre-specified one, with ε/prior
sensitivity disclosed rather than optimised over.

### 3.5 The RACH algorithm

RACH is a single procedure, not a pipeline of separate analyses. Its primitives
are standard — prior sampling / ABC, Shannon entropy, and preposterior
expectation — but three steps that do not co-occur with this objective in ABC
model choice, pattern-oriented modelling, or classical value-of-information give
RACH its distinct identity:

(i) a **constraint grammar `G` applied before the data**, together with an
evidence-role taxonomy (`observed_target` / `input_context` / `diagnostic_only` /
`future_observation`) that determines which observations may enter the distance
`d` and thereby blocks circular inference;

(ii) the **entropy of the switch posterior is reported as a result** — causal
degeneracy — rather than hidden behind its mode;

(iii) a **next-observation step whose value is the mutual information between a
candidate measurement and residual mechanism identity**, normalised by `K`.

```
Algorithm 1  RACH
Input : switches S = {s_1..s_K}; prior π over (θ,s); constraint grammar G;
        simulator f; pattern maps P_sim, P_obs; observed patterns y_obs;
        context x_obs; tolerance ε; candidate observations Q
Output: admissibility CA_j, degeneracy D, resolvability R, validated NOV where estimable

 1  A ← ∅
 2  repeat N times:
 3      draw (θ, s) ~ π
 4      if G(θ) = 0: continue
 5      p ← P_sim(f(x_obs; θ, s))
 6      if d(p, P_obs(y_obs)) ≤ ε:
 7          A ← A ∪ {(θ, s)}
 8  CA_j ← mean_{(θ,s)∈A} s_j
 9  D ← H(S | A);  R ← 1 − D / K
10  for each candidate Q with an identified predictive map over A:
11      construct Pr(Q=q | A) from the current admissible region
12      compute I(S;Q | A)
13      NOV(Q) ← I(S;Q | A) / K
14  return A, CA_j, D, R, NOV
```

**Closing the loop (RACH-SEQ).** Single-shot RACH evaluates what is worth
measuring *now*; RACH-SEQ iterates after observations arrive. Given the current
mechanism-equivalence graph, it scores each candidate by expected confounding-edge
cuts, takes the highest-scoring available observation, conditions `A`, recomputes
the graph and predictive distributions, and repeats until the graph is empty or
the budget is exhausted. Thus a verified candidate is reweighted by
`Pr(q|current A_ε)` at every step, rather than by a probability frozen at step 0.
If an outcome vocabulary does not define a verified partition, a predeclared
prior may be used as an explicit RACH-SEQ ranking fallback and its probability
source is reported; that fallback is not called validated single-shot EVSI.
Hidden synthetic truth is used only *after* candidate ranking to materialise a
benchmark outcome.

## 4. Controlled validation

### 4.1 Known-truth recovery (self-consistency; Fig. S1)

*(`python -m causal_model.known_truth_benchmark --figure …`)* A
specified-simulator recovery benchmark generates synthetic data under a fixed
switch state and checks RACH under controlled truth; cross-backend modes
(proxy→proxy self-consistency vs abm→proxy / abm→abm simulator robustness) are
supported. This tests self-consistency or misspecification robustness, not
real-world causation. Confounded switches are deliberately not expected to become
uniquely recoverable from a non-identifying pattern.

### 4.2 Model selection misleads; RACH exposes the confound (Fig. 2)

*(`python -m causal_model.confound_demo --figure …`; proxy backend, seed 7,
n = 600 draws, |A_ε| = 346)* In a controlled system where selfing syndrome (S2)
and island isolation (S3) reproduce the same ordinal gradients, ABC model choice
reports a single MAP switch-combination with low posterior mass. RACH instead
reports high degeneracy and the coupled mechanism structure, then asks which
measurement carries information about that unresolved pair. This figure is a
controlled diagnostic, not a natural-system mechanism claim.

### 4.3 Generality and observation-budget error control (Fig. 3)

The submission result for this section is generated only by the current frozen
protocol `rach-g2-truth-peek-free-v2` through
`paper/run_g2_frozen_benchmark.py`. Protocol v1 is preserved in the archive but
was **never executed as the final submission benchmark**. It was superseded before
any final output was inspected because a resolver-only candidate vocabulary could
test observation sufficiency without testing whether RACH-SEQ selected useful
observations efficiently.

V2 therefore separates those questions. Each generated system contains one or two
disjoint two-driver confounds with an explicit quantitative resolving observation
for each confound. It additionally contains **two binary nuisance measurements**
generated independently of the mechanism vector. The nuisance measurements are
valid, mutually exclusive/exhaustive predictive observation maps, but have no
designed mechanism information. They therefore compete for the same observation
budget without being malformed candidates.

The exact same seed-defined systems, hidden mechanism truths, candidate sets and
budgets are evaluated under two preregistered policies:

```text
RACH-SEQ      choose the remaining candidate with maximum expected confounding-edge cuts
random_order  choose uniformly among remaining candidates
```

Neither policy sees a hidden outcome before selecting the candidate. Only after a
candidate has been chosen is its hidden benchmark outcome materialised and the
current admissible region conditioned on that observation. RACH-SEQ recomputes
candidate outcome probabilities from current `A_ε` whenever a verified partition
is available. Random-order selection is an uninformed **selection baseline**, not
an alternative causal model.

The frozen protocol uses five predeclared seeds, 200 systems per seed, 1,500 prior
draws per system, K ∈ {4,5,6}, one or two confounds, random pre-data driver
coefficients, two nuisance candidates and observation budgets 0–4. Primary
policy-specific outputs are convergence to an empty confounding graph, fraction
of confounding edges resolved, mean observations used and hidden-truth
false-exclusion rate. The number of nuisance observations selected is retained as
a selection diagnostic. The runner additionally reports within-seed
`RACH-SEQ − random_order` contrasts for each budget and aggregates all quantities
by mean and sample standard deviation across seeds.

The comparison is deliberately **not an acceptance criterion**. There is no
software test or protocol rule requiring RACH-SEQ to outperform random order in
any metric. Favourable, null or adverse policy contrasts all remain valid frozen
results. Every row is tagged with the SHA-256 hash of the exact v2 protocol, and
numerical values will be inserted here only from those tagged outputs. The pre-fix
99.2%/98.5% values are not submission evidence.

This benchmark therefore supports a narrower and more falsifiable generality
claim than “RACH works across ecology”: over a declared family of random confounded
systems, it asks whether a sequential structural observation policy reduces
mechanism ambiguity and how its observation-budget efficiency compares with an
uninformed selection policy while controlling hidden-truth exclusion.

### 4.4 NOV information identity and calibration (Fig. 4)

NOV is checked at two independent levels. First,
`causal_model/nov_evsi.py` calculates the expected resolvability gain from
conditional sub-regions and independently calculates the empirical mutual
information of `(S,Q)`; the implementation requires agreement with
`I(S;Q|A_ε)/K` up to the existing display rounding of `R_RACH`. Second,
`python -m causal_model.nov_calibration --figure …` compares the cheap
stored-region conditioning calculation with fresh deterministic re-inference and
evaluates predictive expected value against realised gains across controlled true
states. The first check establishes the information identity; the second tests the
computational conditioning shortcut and empirical calibration.

## 5. Exact ecological projection and ABM boundary

The abstract factorisation is projected only after an ecological output and its
observation map are declared. In the colonisation life cycle, expected juvenile
recruits retained after one step for one initial adult can be written exactly as

[
W_{\mathrm{recruit}}(z)=F_{\mathrm{local}}(z)
E_{\mathrm{settlement}}(z),
]

with

[
F_{\mathrm{local}}=P(\mathrm{survive})P(\mathrm{conceive}\mid\mathrm{survive})
]

and

[
E_{\mathrm{settlement}}=(1-p_{\mathrm{ext}})
[D(z)cT+{1-D(z)}L].
]

Here (D(z)) is dispersal investment, (c) corridor connectivity, (T)
expected room in a reachable target, and (L) local settlement room. The formula
matches the implemented order of survival, conception, mutually exclusive
dispersal or local settlement, and the end-of-step extinction draw. Within the
strict positive interior, N1–N4 apply exactly to this declared output.

This bridge does not factorise long-run invasion growth, persistence, or endpoint
trait-space geometry. Those outputs additionally contain surviving parents,
repeated generations, density dependence, resource feedback, mutation,
stochasticity, and changing resident composition. Spatial, colonisation, and
defence ABMs therefore enter only as Supplementary robustness or counterexample
families. The projection ledger labels each target `exact`,
`requires_factorization_extension`, or `not_applicable`; agreement in a full
ABM cannot be used as proof of N1–N4.

## 6. Prospective worked design: Izu Islands *Campanula*

Published Izu Islands records describe increased autonomous selfing, reduced
flower size, and pollinator turnover along island isolation gradients (Inoue &
Amano 1986; Inoue 1988, 1990). Those summaries are biologically informative but
do not provide trait-specific total performance (W(z)), a resolved factor
(F(z)) or (E(z)), or a proxy whose conversion is shown to be stable across
islands. In the projection ledger the record is therefore
`not_applicable` to N1–N4 as an empirical channel-identification claim.

RACH uses the case prospectively. The present pattern admits at least a
pollination/fecundity change, an establishment/reachability change, a
selfing-syndrome pathway, and shared island effects under the declared grammar.
The valid output is the surviving explanation set and the measurements required
to reduce it, not a conclusion that pollinator loss caused the observed trait
change.

The minimum theorem-ready comparison is:

| Quantity | Required empirical role |
|---|---|
| (W(z)) | trait-specific total performance on a shared trait domain and census scale |
| one channel | direct (F(z)) or (E(z)), measured before and after or among regimes |
| or proxy (X(z)) | conversion to the channel demonstrated stable or calibrated in each regime |
| uncertainty | propagated through reconstructed (\rho_F) and (\rho_E) |
| mapping | declared recruitment/reachability and life-cycle window |

For a pollination interpretation, visitation alone is insufficient because
visitor quality, pollen transfer, resource limitation, selfing, and seed
maturation can change the conversion from visits to successful reproduction.
Pollen deposition, hand-pollination controls, and trait-specific seed output can
test that conversion. Campanula is retained in the main text because it shows how
a negative identifiability result changes a field design; it is not presented as
empirical validation of RACH.

## 7. Software and reproducibility

The Python package implements N1–N4 constructions, RACH admissibility and
replaceability, validated information-theoretic NOV/EVSI
(`causal_model/nov_evsi.py`), RACH-SEQ, controlled benchmarks, the exact one-step
colonisation projection, and the executable projection ledger. The older
heuristic next-observation score remains available only as an explicitly named
compatibility helper and is not the primary publication API. The canonical
submission inventory is `paper/submission_manifest.json`.

The final selection/error-control benchmark is governed by
`paper/g2_frozen_benchmark_protocol.json` and
`paper/run_g2_frozen_benchmark.py`; manuscript G2 numbers must carry the hash of
that frozen v2 protocol. Running

```bash
python paper/check_submission_bundle.py
```

checks that every main-text dependency exists, that required theorem-first
sections remain in the manuscript, that G2 v2 retains its matched random-order
selection challenge, and that provisional ecological-rule and structure-discovery
claims have not re-entered the primary draft. The standard CI then runs the
complete test suite across Python 3.10–3.12 and smoke-tests the core figure
commands. No new empirical data are reported.

## 8. Discussion

The central methodological result is a change in the inferential target. When an
observation map is structurally non-identifying, selecting a single mechanism is
not an answer with large uncertainty; it is an answer to a question the data
cannot distinguish. N1–N4 make that statement exact for a positive two-channel
performance model. RACH then provides the finite reportability object needed in
less algebraically tractable settings: the admissible explanation set, its
degeneracy and replaceability structure, and an information measure for what to
observe next.

The identity `NOV(Q)=I(S;Q|A_ε)/K` clarifies why this observation-design step is
not an arbitrary priority score. A candidate observation is valuable exactly to
the extent that it carries information about residual mechanism identity under
the current admissible region. This also provides a clean stopping criterion:
when every available candidate has zero validated NOV, the current candidate
vocabulary contains no further information about the unresolved mechanism vector,
even if `D_RACH` remains positive.

The sequential algorithm adds a distinct claim: given a finite candidate
vocabulary and observation budget, useful measurements should be selected before
mechanism-uninformative alternatives if the structural score actually carries the
intended information. The frozen G2 matched-policy benchmark therefore separates
**observation sufficiency** from **selection efficiency**. A high resolver-only
success rate alone would not validate the latter. Conversely, an adverse or null
RACH-versus-random contrast would narrow the method's defensible boundary and is
retained rather than tuned away.

RACH combines familiar components—ABC-style restriction, explicit biological
constraints, entropy, pattern-oriented modelling, and value of information
(Beaumont et al. 2002; Grimm et al. 2005; Chaloner & Verdinelli 1995; Canessa et
al. 2015)—under a different inferential target and stopping rule. It does not stop
when a ranking can be computed. It stops when the declared observation budget is
exhausted, the remaining programs are separated at the declared resolution, or
the available observation vocabulary carries no further identified mechanism
information. This also clarifies the relation to ABC model choice: RACH is
designed for cases in which a model winner may be unstable or weakly supported
(Robert et al. 2011).

The exact projection illustrates how mathematical and ecological claims should
be connected. The factorisation is earned for a specified one-step life-cycle
output and deliberately withheld from multistep ABM outcomes that have not been
factorised. This prevents simulations from being treated as proofs while still
allowing them to test robustness after additional processes are introduced.

Several limitations remain. Admissibility is relative to a program vocabulary,
constraint grammar, prior, distance and tolerance. A missing causal program
cannot be recovered by reporting the retained set. A validated stored-region NOV
also requires an observation map whose predictive outcomes can actually be
obtained as a pushforward of current `A_ε`; otherwise the EVSI is non-estimable
without an additional predictive model. The v2 random-system benchmark challenges
selection only against simple independent nuisance measurements and a uniform
random-order baseline; it does not establish optimality against all experimental
design algorithms or all ecological candidate vocabularies. Under stochastic
simulators, re-inference-free filtering is approximate and its Monte Carlo
properties must be reported. Measurement error can be propagated, but unknown
regime-specific proxy calibration is structural and cannot be repaired by larger
sample size alone. Finally, the Campanula example remains prospective until
channel-resolved data and calibration evidence exist.

The immediate empirical implication is modest but actionable: observed
contraction, shift, fragmentation or persistence should not be assigned to a
vital-rate channel when it is only a function of net performance. The
corresponding methods implication is stronger: non-identifiability can be
reported as a reproducible scientific object and converted into a quantitatively
ranked next-observation design.

## Figure plan

1. **Figure 1 — Exact boundary and workflow.** N1 observational symmetry; N2–N4
   sufficient/insufficient measurement boundary; hand-off to RACH.
2. **Figure 2 — Controlled confound.** Model ranking versus the admissible set,
   causal degeneracy, and the resolving observation.
3. **Figure 3 — Sequential selection and error control.** Frozen v2 budget curves
   for RACH-SEQ and random-order baseline, convergence, edge resolution,
   observations used, distractors selected, false exclusion, and seed-level
   uncertainty/contrasts.
4. **Figure 4 — NOV information and calibration.** `I(S;Q|A_ε)/K` identity,
   admissible-region conditioning versus fresh re-inference, and realised-gain
   calibration.
5. **Figure 5 — Earned ecological projection.** Exact one-step colonisation
   factorisation, projection-ledger boundary, and prospective Campanula
   measurement design.

ABM endpoint sweeps, sensitivity analyses, and detailed known-truth panels belong
in Supplementary Information. Ecological-rule panels and structure discovery are
not part of this submission.

## Data accessibility and code availability

No new empirical data are reported. All algebraic constructions, synthetic
generators, benchmark code, tests, and figure commands are in the accompanying
repository. The archival DOI will be added after the submission release is
minted.

## Author contributions

Ruiqi Zhang conceived the framework, implemented the software, ran the analyses,
and wrote the manuscript. Complete CRediT roles and any co-authors before
submission.

## Acknowledgements

[To complete.]

## Funding

[To complete.]

## Conflict of interest

The author declares no conflict of interest.

## ORCID

Ruiqi Zhang — [to add].

## References

- Beaumont, M.A., Zhang, W. & Balding, D.J. 2002. Approximate Bayesian computation
  in population genetics. *Genetics* 162: 2025–2035.
- Beaumont, M.A. 2010. Approximate Bayesian computation in evolution and ecology.
  *Annual Review of Ecology, Evolution, and Systematics* 41: 379–406.
- Canessa, S., Guillera-Arroita, G., Lahoz-Monfort, J.J., Southwell, D.M.,
  Armstrong, D.P., Chadès, I., Lacy, R.C. & Converse, S.J. 2015. When do we need
  more data? A primer on calculating the value of information for applied
  ecologists. *Methods in Ecology and Evolution* 6: 1219–1228.
- Chaloner, K. & Verdinelli, I. 1995. Bayesian experimental design: a review.
  *Statistical Science* 10: 273–304.
- Csilléry, K., Blum, M.G.B., Gaggiotti, O.E. & François, O. 2010. Approximate
  Bayesian computation (ABC) in practice. *Trends in Ecology & Evolution* 25:
  410–418.
- Grimm, V., Revilla, E., Berger, U., Jeltsch, F., Mooij, W.M., Railsback, S.F.,
  Thulke, H.-H., Weiner, J., Wiegand, T. & DeAngelis, D.L. 2005. Pattern-oriented
  modeling of agent-based complex systems: lessons from ecology. *Science* 310:
  987–991.
- Hartig, F., Calabrese, J.M., Reineking, B., Wiegand, T. & Huth, A. 2011.
  Statistical inference for stochastic simulation models – theory and
  application. *Ecology Letters* 14: 816–827.
- Inoue, K. & Amano, M. 1986. Evolution of *Campanula punctata* Lam. in the Izu
  Islands: changes of pollinators and evolution of breeding systems. *Plant
  Species Biology* 1: 89–97.
- Inoue, K. 1988. Pattern of breeding-system change in the Izu Islands in
  *Campanula punctata*: bumblebee-absence hypothesis. *Plant Species Biology* 3:
  125–128.
- Inoue, K. 1990. Evolution of mating systems in island populations of
  *Campanula microdonta*: pollinator availability hypothesis. *Plant Species
  Biology* 5: 57–64.
- Inoue, K. & Kawahara, T. 1990. Allozyme differentiation and genetic structure in
  island and mainland Japanese populations of *Campanula punctata*. *American
  Journal of Botany* 77: 1440–1448.
- Raiffa, H. & Schlaifer, H. 1961. *Applied Statistical Decision Theory.* Harvard
  University Press, Boston.
- Robert, C.P., Cornuet, J.-M., Marin, J.-M. & Pillai, N.S. 2011. Lack of
  confidence in approximate Bayesian computation model choice. *Proceedings of the
  National Academy of Sciences* 108: 15112–15117.
