# From Identifiability Limits to Mechanism-Resolving Observation Design

**Integrated development draft v0.1 — target lane: Methods in Ecology and Evolution, Research Article**

## Abstract

Ecological mechanism studies often face two measurement problems that are treated separately. First, additional measurements can improve precision without changing which latent mechanisms are structurally distinguishable. Second, even after several candidate mechanisms remain compatible with current evidence, technically available measurements can differ sharply in how much information they carry about that residual ambiguity. We combine these problems into a two-gate observation-design framework. Gate 1 is structural: for exact log-linear observations of positive latent channels, the compatible mechanism set has dimension `k-rank(M)`, and one additional scalar observation reduces that dimension if and only if its observation row lies outside the current row span. A field-like three-channel service example shows that different latent mechanisms can produce identical current records until one channel-resolving measurement is added. Gate 2 is conditional information allocation. Mechanism-Resolving Observation Design retains a declared admissible parameter–mechanism region rather than forcing a winner, measures residual mechanism entropy, and scores verified candidate observations by `V(Q)=I(S;Q|A_epsilon)/K`. Selected outcomes condition the retained region and candidate values may be recomputed. A finite theorem gives the exact condition under which such outcome-dependent recomputation has strict expected value over the best precommitted second measurement. In a frozen truth-peek-free benchmark, information-guided selection resolved all initial confounding edges at budget two versus 60.45% under random ordering, converged in 99.0% versus 43.5%, and almost completely avoided mechanism-independent nuisance measurements. A post-frozen diagnostic showed that a static initial-information ranking performed essentially identically to the adaptive policy on these benchmark systems, so the benchmark supports information-guided screening rather than an empirical claim that recomputation itself caused the gain. The resulting workflow separates three questions: whether a measurement can alter structural identification, how informative it is about the currently retained ambiguity, and whether realised outcomes make recomputation valuable.

**Keywords:** structural identifiability; experimental design; mechanism ambiguity; mutual information; ecological monitoring; value of information; sequential design

---

## 1. Introduction

Ecological mechanism inference is often described as a choice among explanations. A model family is specified, candidate mechanisms are fitted or simulated, and the evidence is used to rank them. Yet ranking is only decisive when the observation architecture actually separates the candidate mechanisms. Several distinct processes can generate the same endpoint, several parameter–mechanism combinations can remain compatible with one observed pattern, and increasingly precise measurement of an invariant endpoint can leave the underlying mechanism ambiguity unchanged.

This creates a measurement problem before it creates a model-selection problem. If an observation is insensitive to the distinction of interest, collecting it more precisely does not make that distinction structurally identifiable. Conversely, when several new measurements could separate the remaining mechanisms, measuring all of them may be unnecessary or expensive. The next observation should be chosen for the ambiguity that remains, not merely because it is measurable, proximal to biological machinery, or historically common.

We therefore separate two design gates.

**Gate 1 — structural identification.** Does adding a candidate observation change the exact observation map so that previously indistinguishable latent mechanisms become distinguishable?

**Gate 2 — information allocation.** Conditional on a declared set of mechanisms still compatible with the current evidence, which verified candidate measurement contains the most information about the residual mechanism ambiguity?

These gates answer different questions. Structural identifiability is a property of the declared observation map and latent model under exact measurement. Information value is conditional on the currently retained mechanism region and on a predictive model for candidate measurement outcomes. A candidate can be structurally new yet weakly informative in the current region, while a highly precise candidate can be structurally redundant.

The paper combines a source-owned identification result with a source-owned observation-design method without claiming that one mathematically implies the other. The first layer uses an exact rank criterion for log-linear observation maps as a transparent ecological design case. The second layer, Mechanism-Resolving Observation Design (MROD), is more general: it operates on a declared admissible parameter–mechanism region and is not restricted to multiplicative ecological chains.

The integrated workflow makes four contributions. First, it gives a necessary-and-sufficient criterion for when one additional exact scalar observation reduces structural ambiguity in the log-linear channel class. Second, it translates that condition into a field-like joint-measurement example in which two different mechanisms produce the same current records. Third, it defines residual mechanism ambiguity and candidate observation information in a retained admissible region, with exact mutual-information interpretation when candidate outcomes form a verified partition. Fourth, it separates the benefit of **information-guided screening** from the stronger claim that **adaptive recomputation** itself improves performance: the theory gives an exact strictness condition for the latter, while the frozen benchmark principally validates the former.

This distinction is important for methodological honesty. The benchmark result is strong—information-guided selection sharply outperforms random ordering and almost eliminates nuisance measurements—but a later static-information diagnostic shows that the benchmark does not isolate adaptivity as the causal source of that advantage. The method should therefore be presented as an explicit hierarchy of claims rather than a single “adaptive AI chooses the best measurement” story.

---

## 2. Gate 1 — when can an added observation change identification?

### 2.1 Exact observation geometry

Consider `k` positive latent channels `F_1,...,F_k` and write

\[
x_j=\log F_j.
\]

Suppose the exact available log-linear observations are collected as rows of a matrix `M`, so compatible latent states satisfy

\[
Mx=y.
\]

When the system is compatible, the solution set is an affine translate of the null space:

\[
\mathcal C_y=x_0+\ker M.
\]

The residual structural dimension is therefore

\[
\boxed{\dim \mathcal C_y=k-\operatorname{rank}(M).}
\]

Point identification occurs exactly when `rank(M)=k`.

This statement is elementary linear algebra. Its design consequence is more useful than the dimension formula by itself.

### Theorem 1 — one-observation rank-gain criterion

Add one exact scalar observation with row vector `a^T`. The structural unidentified dimension decreases if and only if

\[
\boxed{a\notin\operatorname{rowspan}(M).}
\]

For one scalar row, the decrease is exactly one dimension.

Thus:

- repeating an existing exact observation row gives no structural gain;
- nonzero rescaling of an existing row gives no structural gain;
- an exact linear combination of existing observations gives no structural gain;
- a genuinely independent row reduces the structural ambiguity by one dimension.

The theorem does **not** imply that repeated measurements or improved precision are statistically useless. They can reduce sampling uncertainty. It says that precision and structural identification are different properties.

### 2.2 Net performance as an identification bottleneck

A common ecological architecture combines positive stages multiplicatively. If

\[
W=\prod_{j=1}^{k}F_j,
\]

then observing net performance contributes the row `(1,...,1)` in log coordinates. Endpoint-only observation therefore leaves `k-1` product-preserving structural dimensions.

If `r` independent channel coordinates are directly anchored, the special case becomes

\[
k-1-r,
\]

but this is now a corollary of the rank theorem rather than a counting definition.

The design lesson is not “always measure every component.” It is to identify which new observation changes the row space relevant to the mechanism contrast being claimed.

---

## 3. A field-like joint-measurement witness

A concrete example shows why the rank criterion matters operationally.

Suppose a declared effective ecological service has three positive channels,

\[
W=V E D,
\]

where `V` is a quantity/visitation channel, `E` is per-interaction effectiveness, and `D` is a downstream dependency or reproductive-conversion channel.

Consider two latent states:

```text
Mechanism A: (V,E,D) = (10, 0.4, 0.5)
Mechanism B: (V,E,D) = (10, 0.2, 1.0)
```

Both generate

```text
V = 10
W = 2
W/V = 0.2
```

The current records therefore do not identify whether the difference lies in `E` or `D`. In log coordinates the available exact observation rows have rank two for three latent channels, leaving one structural degree of freedom.

Now add one direct effectiveness measurement `E`. The observation operator reaches rank three, and

\[
D=\frac{W}{VE}
\]

is recovered uniquely.

The example is deliberately simple. Its purpose is not to assert that every pollination or ecosystem-service study obeys this three-factor model. It demonstrates the measurement logic:

> **when mechanism ambiguity is structural under the current observation map, resolving it can require a qualitatively new measurement class rather than more endpoint replication.**

This gives a practical Gate-1 question before any candidate observation is assigned an information score.

---

## 4. Gate 2 — retain the mechanism ambiguity instead of forcing a winner

Structural analysis says whether an observation map can in principle separate latent dimensions in a declared exact model. Real mechanism studies often face a different object: many parameter–mechanism combinations remain compatible with noisy or approximate evidence.

MROD represents that ambiguity explicitly.

Let `S in {0,1}^K` be a mechanism vector, `theta` model parameters, `G(theta)` a pre-data biological constraint grammar, `x_obs` fixed context, `y_obs` observed targets, `f` a simulator or predictive model, `P_sim` and `P_obs` maps into a shared pattern space, `d` a declared discrepancy, and `epsilon` a tolerance. Define

\[
A_\epsilon(y_{obs},x_{obs})
=
\{(\theta,s):G(\theta)=1,
\ d(P_{sim}(f(x_{obs};\theta,s)),P_{obs}(y_{obs}))\le\epsilon\}.
\]

The method retains this region rather than immediately selecting a modal mechanism row.

### 4.1 Evidence roles

To limit circularity, each quantity is assigned one role before inference:

- `observed_target` — may enter the acceptance discrepancy;
- `input_context` — conditions the simulator but is not independent evidence;
- `diagnostic_only` — evaluates behavior after inference;
- `future_observation` — withheld as a candidate next measurement.

The same quantity should not silently define simulator context, enter the acceptance score, and then reappear as independent validation.

### 4.2 Residual mechanism ambiguity

Let

\[
D=H(S\mid A_\epsilon)
\]

be residual joint mechanism entropy. Define normalized mechanism resolvability

\[
R=1-D/K.
\]

The retained region can also support mechanism-equivalence and replaceability summaries. These are not alternative winner-selection criteria; they describe what mechanism distinctions remain unresolved.

---

## 5. Observation information value

Let `Q` be a candidate future measurement with finite outcomes `q`. For the stored-region calculation, candidate outcome maps must form a verified mutually exclusive and exhaustive partition of the current admissible region. Then

\[
\Pr(Q=q\mid A_\epsilon)
\]

is the pushforward of that retained region.

Define observation information value as expected normalized gain in mechanism resolvability:

\[
V(Q)
=E_Q[R(A_\epsilon\mid Q)-R(A_\epsilon)].
\]

Because of the entropy definition,

\[
\boxed{V(Q)=\frac{I(S;Q\mid A_\epsilon)}{K}.}
\]

A candidate with zero current mutual information cannot reduce mechanism entropy in the declared retained region. A candidate whose predictive outcome partition is unavailable is reported as non-estimable for this quantity; an external outcome prior is not silently substituted and called validated information value.

This is the second measurement gate. Gate 1 asks whether a proposed measurement adds a structurally new observation direction in the exact model class. Gate 2 asks how much a verified measurement separates the mechanism ambiguity that actually remains under the declared analysis.

---

## 6. Sequential observation design and what adaptivity does—and does not—establish

The operational policy can condition the retained region after a selected outcome and recompute the information value of all remaining verified candidates:

```text
A_0 = current admissible region
for t = 0,1,...:
    calculate V_t(Q) for each verified remaining candidate
    select a largest positive-current-value candidate
    reveal the selected outcome
    condition A_t to produce A_{t+1}
    recompute remaining candidate values
stop at resolution, budget exhaustion, or no positive verified value
```

Outcome-dependent recomputation is intuitively attractive, but it should not be justified only by comparison with random order.

### Theorem 2 — exact two-step adaptivity condition

Fix the first observation `X`. For each remaining candidate `q`, write

\[
U_q(x)=I(S;Q_q\mid X=x).
\]

The adaptive second-step value is

\[
V_{adapt}=E_X[\max_q U_q(X)],
\]

and the strongest precommitted static second measurement has value

\[
V_{static}=\max_q E_X[U_q(X)].
\]

Then

\[
V_{adapt}\ge V_{static}.
\]

Equality holds exactly when at least one candidate is optimal on every positive-probability branch:

\[
V_{adapt}=V_{static}
\iff
\bigcap_{x:P(X=x)>0}\arg\max_q U_q(x)\neq\varnothing.
\]

Therefore recomputation has strict expected value exactly when no common branchwise maximizer exists.

A four-world construction gives `1` bit of adaptive second-step information versus `0.5` bit for the best static second measurement. Within the declared deterministic two-branch witness class, fewer than four worlds cannot generate the required strict branch switch.

The theorem is a conditional result. It does not prove that a greedy multi-step policy is globally optimal under arbitrary future measurement processes.

---

## 7. Frozen controlled validation

The principal algorithmic evidence is a frozen truth-peek-free synthetic benchmark. The generated systems contain initial mechanism confounding, informative candidate observations, and mechanism-independent nuisance measurements. Hidden truth is not available to the policy when a candidate is selected; it is used only afterward to materialize the selected measurement outcome.

The benchmark compares information-guided selection with uniform random ordering on the same generated systems, candidate sets, hidden truths, and budgets.

### Budget two

| outcome | information-guided | random order |
|---|---:|---:|
| initial confounding edges resolved | `1.000` | `0.6045` |
| systems converged | `0.990` | `0.435` |
| observations used | `1.505` | `1.821` |
| nuisance selections | `0.001` | `0.974` |

### Budget four

Both policies resolved all initial confounding edges on average, but allocation remained strongly different:

- information-guided nuisance measurements per system: `0.014`;
- random-order nuisance measurements per system: `1.169`;
- fold difference: `83.5`;
- observations used: `1.518` versus `2.673`.

Hidden-truth false exclusion was zero in every frozen policy-by-budget cell.

These results support the claim that **current mechanism information can be used to avoid valid but mechanism-independent candidate measurements and to resolve the declared confounding more efficiently than random ordering in the frozen benchmark family**.

They do not, by themselves, establish that recomputation after each outcome caused the benchmark advantage.

---

## 8. Post-frozen static-information diagnostic and the adaptivity claim ceiling

A later diagnostic compared the information-guided policy with a policy that calculates candidate information at the initial state and then keeps that ranking fixed rather than recomputing it after realised outcomes.

On the benchmark systems, the results were nearly identical.

At budget two, both policies had:

- convergence `0.99`;
- initial edge resolution `1.0`;
- mean steps `1.505`;
- nuisance selections `0.001`;
- false exclusion `0.0`.

At budget four, information-guided versus static-initial-information results were:

- convergence `0.999` versus `0.998`;
- fraction resolved `1.0` versus `1.0`;
- mean steps `1.518` versus `1.518`;
- nuisance selections `0.014` versus `0.014`.

This diagnostic is not part of the frozen G2 protocol, but it is scientifically important because it limits interpretation. The benchmark demonstrates the value of **information-guided candidate screening relative to random order**. It does not provide material empirical evidence that **adaptive recomputation** is responsible for the gain in this particular benchmark family.

The adaptivity claim therefore remains theorem-conditional:

> recomputation is guaranteed not to be worse than the best precommitted second measurement in the declared two-step setting, and it is strictly better when branchwise optimal candidates have no common maximizer.

An empirical benchmark designed specifically to generate branch-dependent rank reversals would be required to test that mechanism of gain directly.

This separation is a feature rather than a weakness. It keeps algorithmic validation, theorem scope, and benchmark-specific mechanism of improvement distinct.

---

## 9. The integrated two-gate workflow

The combined method can now be stated as a practical design sequence.

### Step 1 — declare the mechanism contrast and current observation map

Do not start from a list of convenient measurements. State which latent distinctions the mechanism claim requires and what the current observations actually depend on.

### Step 2 — structural identification audit

Where an exact or locally linearized observation model is available, determine whether a proposed measurement adds a new observation direction. In the log-linear channel class, this is the row-span criterion.

If the candidate is structurally redundant, collect it for precision only when that precision is scientifically needed; do not count it as new mechanism identification.

### Step 3 — retain the current admissible mechanism region

When finite/noisy evidence leaves multiple mechanism programs compatible, preserve that multiplicity rather than forcing a winner.

### Step 4 — verify candidate outcome models

A candidate receives an information value only when its possible outcomes are represented in a declared predictive model of the current retained region.

### Step 5 — rank current mechanism information

Use

\[
V(Q)=I(S;Q\mid A_\epsilon)/K
\]

for verified candidates under the current contract.

### Step 6 — acquire, condition, and recompute when scientifically warranted

Recomputation is most consequential when realised outcomes change which remaining candidate is branchwise optimal. The common-argmax theorem states this condition exactly for the two-step comparison.

### Step 7 — stop honestly

Stop when the declared mechanism ambiguity is resolved, the observation budget is exhausted, or no verified available candidate carries positive current information. “No resolving candidate in the vocabulary” is a scientific design result, not an instruction to manufacture a winner.

---

## 10. Relation to existing methods

The integrated framework uses established ideas and should be positioned accordingly.

### Structural identifiability

Rank and null-space criteria are classical identification machinery. The contribution here is not new linear algebra. The ecological value is to place a structural-identification gate directly before measurement acquisition and to connect it to an explicit mechanism-resolving design workflow.

### Approximate Bayesian computation and retained model regions

MROD's admissible region resembles rejection-based ABC restriction. It is not presented as a new posterior model-choice theorem. The retained region is used as the state over which mechanism ambiguity and future observation value are calculated.

### Mutual information and value of information

Mutual information and experimental design are mature fields. The method contribution is the explicit target: current information about a declared ecological mechanism vector within a retained admissible region, with fail-closed requirements on candidate outcome partitions and evidence roles.

### Adaptive experimental design

The paper does not claim generic novelty for adaptive design and does not claim global optimality. The exact common-argmax theorem states when one branch-dependent second measurement has strict expected information advantage over every precommitted second measurement. The frozen benchmark, however, mainly validates information-guided screening rather than the adaptivity mechanism.

---

## 11. Discussion

### 11.1 “More data” contains at least two different operations

Increasing replication and changing the observation map are not the same intervention on an inference problem. More precise measurement of a structurally redundant endpoint can be valuable for uncertainty while leaving a mechanism equivalence class intact. A new channel-resolving measurement can change identification even if measured only once exactly in the idealized theory.

The distinction matters for field budgets. If the scientific bottleneck is structural, sample-size expansion alone is the wrong remedy. If the mechanism contrast is already structurally identifiable but uncertain, replication may be exactly what is needed.

### 11.2 The best next measurement depends on the ambiguity that remains

Once a retained mechanism region has been constructed, candidate value is state-dependent. A measurement that is generally considered mechanistically rich can have zero information about the mechanism distinctions remaining in the current analysis. Conversely, a simple field observation can be highly valuable if it splits the retained alternatives.

This is why the method does not use biological proximity as an automatic ranking principle.

### 11.3 Adaptivity should be claimed only when the benchmark tests it

The post-frozen static-ranking diagnostic is a useful negative result. It shows that a large information-guided versus random advantage does not imply that outcome-dependent recomputation was responsible. In the existing benchmark, the initial information ranking is already sufficient for almost the same performance.

A future adaptivity-specific benchmark should deliberately include branch-dependent candidate-rank reversals while fixing the initial information structure. The theorem predicts exactly when such a benchmark should produce strict benefit.

### 11.4 Relationship to target-specific ecological state

A broader ecological-state theory can require distinctions only for a declared intervention or target. Present MROD resolves a declared mechanism vector. These are related but not identical objectives. Full mechanism resolution can be more demanding than target-safe reporting.

The present paper therefore stops short of claiming a universal target-conditioned monitoring optimizer. A natural next extension is to replace full mechanism entropy with entropy over the minimal response distinctions required for a specified ecological target.

### 11.5 Scope

The structural rank theorem is exact only for its declared positive log-linear observation class. MROD's information values are conditional on the declared mechanism vocabulary, prior/parameter structure, constraints, simulator, discrepancy, tolerance, and candidate outcome model. The synthetic benchmark validates software and allocation behavior in controlled generated systems; it does not identify a true mechanism in nature.

---

## 12. Conclusion

Mechanism-resolving ecological measurement design should begin with two questions rather than one.

First:

\[
\boxed{\text{Can this observation change what is structurally identifiable?}}
\]

Second:

\[
\boxed{\text{Given what remains possible, how informative is this observation now?}}
\]

The rank criterion gives an exact answer to the first question in a transparent log-linear channel class. MROD supplies a retained-region information framework for the second. Its frozen benchmark shows that information-guided screening can resolve declared mechanism ambiguity far more efficiently than random candidate ordering while avoiding nuisance observations. The adaptive theorem then states when outcome-dependent recomputation has strict value—but the current benchmark appropriately does not claim to demonstrate that strictness mechanism.

The combined workflow therefore treats measurement design as a sequence of licensed distinctions: change the observation map when structural ambiguity demands it, rank verified candidates by the ambiguity that remains, and stop rather than overstate what the available measurement vocabulary can resolve.

---

## Development display plan

1. **Figure 1 — Two-gate mechanism-resolving measurement design.** Structural identification gate followed by current information-allocation gate.
2. **Figure 2 — Observation-rank geometry and field-like W=VED witness.** Same records, different latent mechanisms; targeted anchor closes rank.
3. **Figure 3 — MROD admissible region and candidate information value.** Retained mechanism ambiguity and verified candidate partitions.
4. **Figure 4 — Frozen G2 benchmark.** Information-guided versus random allocation at budgets 2 and 4.
5. **Table 1 — Claim hierarchy.** Structural theorem, information identity, adaptive theorem, frozen validation, post-frozen diagnostic, and claim ceiling.

## Integrated claim ceiling

This manuscript does **not** claim that:

- structural identifiability, rank-nullity, mutual information, ABC, value of information, or adaptive experimental design are generic novelties;
- every ecological mechanism problem is multiplicative or log-linear;
- structural non-identifiability makes replication statistically useless;
- MROD is restricted to the Boundary product model;
- the frozen G2 benchmark empirically demonstrates a benefit of recomputation over static information ranking;
- the sequential policy is globally optimal among all adaptive design methods;
- the synthetic benchmark identifies a natural ecological mechanism;
- full mechanism resolution is always necessary when a coarser target can already be reported safely.

The current frozen MROD submission remains an independent, fully validated fallback. This integrated development draft does not supersede its source-matched artifact validation SHA.
