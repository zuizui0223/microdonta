# RACH Core Redirection — Design Document

**Status:** design only (no implementation in this document).
**Scope:** redefine RACH's *primary* mission as the discovery of **robust causal
invariants** shared across all admissible generative programs, from *qualitative*
ecological patterns, **without fixing numerical coefficients, effect sizes, or
fitness functions**. Observation-set design (CRC / NOV / greedy theorems / RACH-SEQ /
RACH-SET) is demoted to an *auxiliary* layer.

This document answers the eight points requested before implementation:

1. What existing code to reuse
2. Causal-program grammar
3. Ecological-constraint schema
4. Mathematical definition of *robust* vs *fragile*
5. ABM-family interface
6. Causal-invariant extraction algorithm
7. MVP test cases
8. Compatibility policy with existing RACH

---

## 0. The reframing in one paragraph

A causal **program** `G` fixes only the *qualitative* skeleton — causal order, edge
signs, monotonicity, trade-offs, state-transition constraints, and ecologically
forbidden relations. Its coefficients are **not** a point; they range over an
admissible set `B(G)`. RACH samples `θ ~ B(G)`, computes the set `Y(G)` of
qualitative patterns the program can produce, and asks not merely *"can G reproduce
y_obs?"* but *"does G reproduce y_obs **robustly** — across a non-negligible,
perturbation-stable, non-cancellation region of B(G) — or only on a measure-zero,
boundary, fine-tuned sliver?"* RACH keeps the **robustly admissible** programs,
discards the **fragile** ones, and reports the causal **motifs / clauses common to
every robustly admissible program** as causal invariants. The headline claim is
deliberately modest: *"within the specified constraints, observations, and model
vocabulary, no robust generative model reproduces the pattern without C"* — **not**
"C is true in nature."

The decisive point: **not fixing numbers does not mean "anything passes."** It is
precisely what lets us *detect and exclude* explanations that survive only by
special numerical tuning — a distinction a fixed-coefficient analysis cannot even
see.

---

## 1. What existing code to reuse

The repository already contains most of the needed machinery. The redirection is
largely a **re-composition + generalisation**, not a rewrite.

| New core concept | Reuse directly | Role of the reused code |
|---|---|---|
| Qualitative program → admissible Boolean region | `replaceability_theory.StructuralModel`, `admissible_configs`, sign-consistent disjunctive semantics (`cline(t) ⟺ ⋁_{k∈D(t)} s_k`) | The exact ε→0 **discrete backbone** for `Y(G)` and for motif/clause logic. Already enumerates `A(O)` over `{0,1}^K`. |
| Robustness mass `ρ(G)` (Monte-Carlo) | `simulator.randomised_linear_f` + the **Tier-A "randomise coefficients, marginalise economics"** policy; `generality_sweep._abc_accept`, `ecological_rules_validation._abc_accept` | These already do *sample θ in a box → forward-propagate signs → accept on an ordinal trend*. `ρ(G)` is the acceptance fraction restricted to one program. |
| Causal-invariant intersection | `minimal_explanations` (`_on_set`, `_minimal_elements` antichain, mass splitting) | The minimal-sufficient-explanation antichain is the **seed** of invariant extraction; generalise from on-sets of switches to motifs/clauses of programs. |
| Ecological-constraint schema | `parameter_constraints` (sign-fixed directions `C5`, ranges with `LiteratureSource`, predicate constraints `C1–C4`), `parameter_sampling.check_ecological_parameter_constraints` | Becomes the **system-agnostic** `EcologicalConstraint` schema. The Campanula constants move into a plugin. |
| Robust vs fragile *vocabulary* | `ensemble.SwitchRobustness` (`is_stable`, `is_resolved`, `is_robust`, `classification`) | Reuse the **naming/verdict pattern**. NOTE: a *different axis* — `ensemble` measures CA_j stability across prior/ε presets; the new layer measures pattern reproduction stability across `B(G)`. Do not reuse the computation, only the idiom. |
| Causal-program grammar | `structures.CausalEdge`, `structures.CausalStructure` (`edges`, `relation`, `latent_parameters`, `expected_patterns`) | The grammar **seed**; extend with monotonicity, ordering, trade-off, state-transition, forbidden relations. |
| ABM-family backend | `simulator_protocol.SimulatorProtocol` (`f(env, θ, s)`), `generator_bridge`, `simulator.SimulatorProtocol` | The ABM-family interface **seed**. The family is `{(F_G, θ) : θ ∈ B(G) ∧ C(θ)}`. |
| Ordinal pattern plumbing | `abc_distance`, `pattern_targets`, `rach_seq.filter_by_outcome` | Pattern matching / outcome filtering, reused unchanged. |
| Cross-system abstract panel | `ecological_rules_validation.ECOLOGICAL_RULES` (Bergmann/Allen/Foster/Gloger as sign-coefficient confounds) | The **cross-system worked-example seed**; re-expressed in the abstract variable layer. |

**Demoted (kept, not broken, re-labelled "auxiliary observation-design layer"):**
`causal_replaceability` (CRC), `replaceability_nov` (NOV), `replaceability_theory`
Theorem C / `rach_set` / `rach_seq` (greedy design), `causal_substitution`,
`counterfactual_ablation`. All their tests stay green (see §8).

---

## 2. Causal-program grammar (`rule_grammar.py`, `qualitative_programs.py`)

A program is **numbers-free**. The grammar extends `structures.CausalEdge` with the
qualitative-only relation vocabulary the user specified.

```python
# rule_grammar.py
Sign = Literal["+", "-", "0"]

@dataclass(frozen=True)
class QualitativeEdge:
    source: str               # abstract variable (see §2.1)
    target: str
    sign: Sign                # monotone direction of dF_target/dsource
    monotone: bool = True     # strictly monotone in this argument over B(G)
    description: str = ""

@dataclass(frozen=True)
class TradeOff:
    # a budget/antagonism: increasing one investment decreases another
    variables: tuple[str, ...]
    description: str = ""

@dataclass(frozen=True)
class StateTransition:
    # allowed qualitative transitions of a discrete state variable
    variable: str
    allowed: frozenset[tuple[str, str]]   # (from_state, to_state)

@dataclass(frozen=True)
class ForbiddenRelation:
    # ecologically impossible co-occurrence / ordering
    predicate: str            # a named, documented impossibility
    description: str = ""

@dataclass(frozen=True)
class CausalProgram:
    name: str
    variables: tuple[str, ...]            # nodes, in a topological order
    edges: tuple[QualitativeEdge, ...]
    causal_order: tuple[str, ...]         # DAG order (no cycles)
    trade_offs: tuple[TradeOff, ...] = ()
    transitions: tuple[StateTransition, ...] = ()
    forbidden: tuple[ForbiddenRelation, ...] = ()
    notes: str = ""
```

**Semantics (the bridge to the existing engine).** The *sign-consistent disjunctive*
reduction already proven in `replaceability_theory` is the ε→0 limit: under random,
sign-definite magnitudes a target shows its ordinal response iff at least one
positively-signed driver is active. So each `CausalProgram` compiles to:

* a **discrete** `StructuralModel` (driver sets per observable) for exact motif/clause
  logic and `Y(G)` enumeration, **and**
* a **continuous** forward map `F_G` (via `randomised_linear_f` for the MVP, or an ABM
  backend, §5) for the robustness-mass Monte Carlo.

The two must agree in the ε→0 limit (a registered consistency test, §7.8).

### 2.1 Abstract variable layer

Cross-system comparison happens in abstract coordinates, never biological names:

```
environmental_change, interaction_opportunity, demographic_state,
reproductive_or_transmission_mode, trait_investment, trait_expression,
neutral_process
```

A plugin (e.g. Campanula) supplies a `dict[str, str]` mapping its concrete variables
(`bombus_frequency`, `selfing_rate`, `nectar_guide`, …) onto this layer. The pollinator
/ selfing / nectar-guide system becomes **one worked example / plugin**, not core.

---

## 3. Ecological-constraint schema (`ecological_constraints.py`)

Generalises `parameter_constraints.py` (today Campanula-specific) into a
system-agnostic schema. Two kinds, mirroring what already exists:

```python
@dataclass(frozen=True)
class RangeConstraint:               # generalises TradeoffPreset.ranges + LiteratureSource
    parameter: str
    lo: float
    hi: float                        # lo>0 can encode a fixed sign (direction principle)
    citation: str = ""
    note: str = ""

@dataclass(frozen=True)
class PredicateConstraint:           # generalises C1..C5 hard-rejection predicates
    name: str
    predicate: Callable[[dict[str, float]], bool]   # True == admissible
    rationale: str = ""

@dataclass(frozen=True)
class EcologicalConstraintSet:
    ranges: tuple[RangeConstraint, ...]
    predicates: tuple[PredicateConstraint, ...] = ()

    def admissible(self, theta: dict[str, float]) -> bool: ...
    def sample(self, rng) -> dict[str, float]: ...        # rejection sampling, like sample_valid_parameter_sets
```

`B(G)` **is** the box `∏[lo_i, hi_i]` intersected with all `predicate`s. Directions
(signs) are encoded as `lo > 0` exactly as `parameter_constraints` already does for the
slope parameters (`C5`). The existing `check_ecological_parameter_constraints` logic is
the reference implementation; the Campanula thresholds move into the Campanula plugin.

---

## 4. Mathematical definitions: robust vs fragile (`robust_admissibility.py`, `fragility_analysis.py`)

### 4.1 Setup

Program `G` with admissible region `B(G) ⊆ ℝ^d`, forward map
`F_G : (θ, x, noise) ↦ π ∈ {−,0,+}^m` (ordinal pattern over `m` observables), and a
target qualitative pattern `y_obs`. `G` **reproduces** `y_obs` at `θ` iff
`match(π(F_G,θ), y_obs)` on the observed coordinates (ordinal equality within tolerance,
using the existing `abc_distance` logic).

Let `B_match(G) = { θ ∈ B(G) : G reproduces y_obs at θ }`.

### 4.2 Robustness mass

```
ρ(G; y_obs) = μ(B_match(G)) / μ(B(G))            μ = Lebesgue measure
```

estimated by Monte Carlo as the acceptance fraction (exactly what `_abc_accept`
already computes, restricted to one program). `ρ(G)=0` ⇒ impossible;
`ρ(G)>0` ⇒ *possible explanation*.

### 4.3 Robust admissibility

`G ∈ RobustAdm(y_obs; δ, η, α)` iff **all three** hold:

* **(R1) Non-negligible mass:** `ρ(G) ≥ δ`.
* **(R2) Perturbation stability (open, not boundary):** for `θ* ` drawn from
  `B_match(G)`, `P_{‖Δ‖≤η}[ match(θ*+Δ) ] ≥ 1−α`. The match set contains open balls;
  it is not a thin boundary shell.
* **(R3) No-cancellation / no fine-tuning:** the match does not rely on exact
  cancellation of opposing pathways or exact initial-condition alignment.
  *Operationalisation:* independently re-scale each pair of opposing-sign edges by
  random positive factors; the match must survive with probability `≥ 1−α`. (Exact
  cancellation breaks immediately under independent positive rescaling.)

### 4.4 Fragility

`G ∈ Fragile(y_obs)` iff `ρ(G) > 0` **and** `G ∉ RobustAdm` — i.e. it *can* reproduce
`y_obs`, but only via (¬R1) measure-zero/thin mass, (¬R2) boundary-only values, or
(¬R3) opposing-pathway cancellation / fine-tuned initial conditions.

`fragility_analysis.py` returns *which* clause failed (R1/R2/R3) and a witness, so the
exclusion is auditable.

### 4.5 The three theoretical goals (as stated; provable/Monte-Carlo-verifiable)

* **Theorem A (Invariance).** If `φ : B(G) → B(G')` is a sign-, monotonicity- and
  causal-order-preserving diffeomorphism (e.g. coordinatewise positive rescaling
  `θ_i ↦ a_iθ_i`, `a_i>0`, or unit changes), then `ρ`, the topological type of
  `B_match`, and the extracted invariants are preserved. ⇒ **invariants do not depend
  on coefficient absolute values.** *Proof idea:* the ordinal `π` is the sign vector of
  sums of sign-definite monomials; positive rescaling preserves those signs, and a
  diffeomorphism preserves positivity of measure.

* **Theorem B (Robust necessity).** If a motif/clause `C` lies in *every*
  `G ∈ RobustAdm(y_obs)`, then *no robustly admissible model in the specified class
  reproduces `y_obs` without `C`.* Reported verbatim with the standing caveat
  (vocabulary-relative; not a claim about nature).

* **Theorem C (Fragility exclusion is non-vacuous).** There exist programs with
  `ρ(G)>0` that fail (R2)∨(R3); RACH excludes them, so `RobustAdm ⊊ PossibleAdm` and a
  motif present across `RobustAdm` but absent across `PossibleAdm` exists. ⇒ qualitative
  **+ robust** analysis yields strictly more necessity than mere reproducibility. The
  canonical witness is the **opposing-cancellation family** (§7.2).

This is the precise sense of the user's claim: *fixing no numbers* still excludes
*tuning-dependent* explanations — the opposite of "anything goes."

---

## 5. ABM-family interface (`abm_family.py`)

ABMs are not a rival to RACH; they are the **primary generative backend**. A single
fixed-parameter ABM run is **never** a causal conclusion. The object of study is the
*family*:

```
Z[t+1] = F_G(Z[t], x, noise; θ),     family = { (F_G, θ) : θ ∈ B(G) ∧ C(θ) }
```

Interface (extends the existing `SimulatorProtocol`):

```python
@runtime_checkable
class ABMFamily(Protocol):
    program: CausalProgram
    constraints: EcologicalConstraintSet
    def step(self, state, x, noise, theta) -> state: ...     # one update
    def run(self, x, noise, theta) -> dict[str, float]: ...   # to qualitative outputs
    def ordinal_pattern(self, outputs) -> dict[str, str]: ...  # {observable: -,0,+}
```

`robust_admissibility` consumes any `ABMFamily`: draw `θ ~ constraints.sample`, run,
reduce to an ordinal pattern, accumulate `ρ(G)` and the (R2)/(R3) perturbation checks.
For the MVP the backend is `randomised_linear_f` (deterministic, exact `ρ`); stochastic
ABMs are admissible with `ρ` taken to the Monte-Carlo limit (the same caveat already
documented in `simulator.py`). Backends available later:
evolutionary / population-genetic / demographic / interaction-network / stochastic.

---

## 6. Causal-invariant extraction algorithm (`causal_invariants.py`, `cross_system_invariants.py`)

**Input:** `RobustAdm(y_obs)` = the set of robustly admissible programs (each carrying
its motif set `M(G)` = edges/sign-edges, plus its driver-set structure).

**Single-system invariants.**

1. **Necessary motif (conjunctive invariant):**
   `C` is invariant iff `C ∈ ⋂_{G ∈ RobustAdm} M(G)`. (Set intersection — the
   `minimal_explanations` antichain idea lifted to motifs.)
2. **Disjunctive necessary clause:** a clause `D = (m₁ ∨ … ∨ m_k)` is necessary iff
   every `G ∈ RobustAdm` contains ≥1 literal of `D`. Minimal such clauses = minimal
   **hitting sets** over `{M(G)}` — directly generalises the disjunction-confound. Found
   by minimal-transversal enumeration over the robust programs.
3. **Necessary causal motif with order:** intersect not just edges but
   `(source, target, sign)` triples *and* their relative causal order, so an invariant
   can assert "`interaction_opportunity` acts *upstream of* `trait_investment`,
   positively."
4. **No-common-rule result:** if `⋂ M(G) = ∅` *and* no necessary disjunctive clause of
   size ≤ k exists, return an explicit `NoCommonRule` verdict (this is a *finding*, not a
   failure).

**Cross-system invariants.** For independent scenarios `r` with robust sets
`RobustAdm_r`, map each program's motifs through its abstract-layer dictionary (§2.1),
then take invariants of the *intersection across systems*:

```
CrossInvariant = ⋂_r ( ⋂_{G ∈ RobustAdm_r} M_abstract(G) )
```

and likewise minimal cross-system disjunctive clauses. Campanula enters here as **one**
system `r`, alongside abstract re-expressions of the existing Bergmann/Allen/Foster/
Gloger panel.

**Output object:**

```python
@dataclass
class InvariantReport:
    robust_programs: list[str]
    fragile_programs: list[tuple[str, str]]      # (name, failed clause R1/R2/R3)
    necessary_motifs: list[Motif]                # conjunctive invariants
    necessary_clauses: list[DisjunctiveClause]   # minimal hitting sets
    no_common_rule: bool
    caveat: str = "Necessity is relative to the specified vocabulary, constraints, "
                  "and observations — not a claim of truth in nature."
```

---

## 7. MVP test cases

Implemented against small, exactly-enumerable programs so every claim is machine-checked
(the precedent set by `test_replaceability_theory.py`).

1. **Grammar + `Y(G)`** — a 3-variable sign program enumerates the expected ordinal
   pattern set `Y(G)`; matches the discrete `StructuralModel` reduction.
2. **Robust vs fragile classification (the crux):**
   * *Robust:* single positive pathway `env → trait`. `ρ ≈ 0.5`, (R1)(R2)(R3) pass.
   * *Fragile:* two opposing pathways `env →(+) trait`, `env →(−) trait`; net sign matches
     `y_obs` only when `|w₊ − w₋|` is tuned near a boundary. Assert `ρ` small **and**
     (R3) fails under independent positive rescaling ⇒ classified **fragile**.
3. **Causal-invariant extraction** — a motif present in all robust programs is returned;
   a motif present only in fragile programs is **not**.
4. **No-common-rule** — two robust programs with disjoint motif sets ⇒ `no_common_rule
   is True`, empty `necessary_motifs`.
5. **Disjunctive necessary clause** — the disjunction-confound family ⇒ returns minimal
   clause `(m₁ ∨ m₂)`; verified as a hitting set.
6. **Theorem A invariance** — positive rescaling of every `B(G)` range leaves
   `necessary_motifs` and `necessary_clauses` byte-identical.
7. **Cross-system invariant** — two abstract scenarios sharing exactly one abstract motif
   (`interaction_opportunity →(+) trait_investment`) ⇒ that motif is the sole cross-system
   invariant; Campanula plugged as one scenario.
8. **ε→0 consistency** — `randomised_linear_f` robustness region converges to the
   discrete `admissible_configs` region as tolerance → 0 (bridges §2 continuous/discrete).
9. **Theorem C non-vacuity** — exhibit `RobustAdm ⊊ PossibleAdm` and a motif separating
   them, over random programs (mirrors `find_greedy_failures`' random-scan style).

---

## 8. Compatibility policy with existing RACH

* **Additive only.** New modules
  (`rule_grammar`, `qualitative_programs`, `ecological_constraints`, `abm_family`,
  `robust_admissibility`, `fragility_analysis`, `causal_invariants`,
  `cross_system_invariants`) are **new files**. No public API of CRC / NOV / theorem
  modules changes. The full existing suite (386 tests) must stay green.
* **Reuse by import, not mutation.** `StructuralModel` / `admissible_configs`,
  `minimal_explanations`, `randomised_linear_f`, and the constraint predicates are
  imported, not edited. If `parameter_constraints` is generalised, the Campanula numbers
  are *moved* into a plugin and re-exported for backward compatibility (existing imports
  keep working).
* **Demotion, not deletion.** CRC, NOV, RACH-SEQ, RACH-SET, Theorem C remain as the
  *auxiliary observation-design layer*. README/theory docs are updated to state the new
  primary mission and explicitly label these as secondary. Their tests are untouched.
* **Tier policy.** New core worked examples (the abstract scenarios, the Campanula
  plugin) register in `simulator.VALIDATED_SIMULATOR_MODULES`, inheriting the Tier-A /
  Tier-B evidentiary discipline already enforced.
* **Boolean ↔ continuous consistency** is a registered invariant (test §7.8), so the new
  continuous robustness layer can never silently diverge from the proven discrete
  elimination theory.
* **Campanula stays a plugin.** No core module imports `attraction_trait_model` or
  Campanula constants; the abstract variable layer is the only coupling point.

---

## Appendix: proposed module-to-reuse map

```
causal_model/
  rule_grammar.py            ← extends structures.CausalEdge/CausalStructure
  qualitative_programs.py    ← compiles CausalProgram → StructuralModel (replaceability_theory)
  ecological_constraints.py  ← generalises parameter_constraints / parameter_sampling
  abm_family.py              ← extends simulator_protocol.SimulatorProtocol / generator_bridge
  robust_admissibility.py    ← Monte Carlo over randomised_linear_f / generality_sweep._abc_accept
  fragility_analysis.py      ← R1/R2/R3 witnesses (new); cancellation test is new
  causal_invariants.py       ← lifts minimal_explanations antichain to motifs/clauses
  cross_system_invariants.py ← abstracts ecological_rules_validation panel + Campanula plugin
```

Auxiliary (demoted, unchanged): `causal_replaceability`, `replaceability_nov`,
`replaceability_theory` (Theorem C), `rach_set`, `rach_seq`, `causal_substitution`,
`counterfactual_ablation`.
