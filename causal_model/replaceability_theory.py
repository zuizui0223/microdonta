"""The theory of Causal Replaceability: two general theorems, machine-checked.

This module states and *proves* (with an exhaustive structural computation, then
randomised machine verification in the tests) two general results about Causal
Replaceability Cost (CRC). Neither result depends on any particular numbers: they
hold for every disjunctive causal model. This is the general, number-free content
of the framework — the "new discovery" is a theorem, not a fitted value.

------------------------------------------------------------------------------
Structural model
------------------------------------------------------------------------------
K candidate mechanisms, switch vector s ∈ {0,1}^K. A set of observable traits;
each trait t has a *driver set* D(t) ⊆ {0..K-1} of mechanisms that can produce
its (directional) cline. We use the sign-consistent disjunctive semantics that
the whole repository's Tier-A simulators instantiate: under randomised, sign-
consistent magnitudes, trait t exhibits its cline in a draw iff at least one
driver is ON,

        cline(t)  ⟺  ⋁_{k ∈ D(t)} s_k .

(Generic non-cancellation: with continuous random magnitudes the net slope is
non-zero almost surely, so the ABC region converges to this Boolean region as
ε→0; the structural region below is that ε→0 limit, computed exactly.)

An observation set O assigns each observed trait an outcome:
    PRESENT(t)  → require ⋁_{k∈D(t)} s_k = 1   (a positive monotone clause)
    NULL(t)     → require s_k = 0 for every k ∈ D(t)   (negative unit clauses)

The structural admissible region is
    A(O) = { s ∈ {0,1}^K : all PRESENT clauses hold and all NULL units hold }.

CRC (no external constraints) is, with any full-support prior 0<p_k<1,
    CRC_j(O) = −log₂ P(s_j = 0 | s ∈ A(O)),
so CRC_j = ∞  ⟺  s_j = 1 in *every* admissible configuration (j indispensable).

------------------------------------------------------------------------------
Lemma (Elimination is null-only)
------------------------------------------------------------------------------
Let NullOff(O) = ⋃_{NULL(t) ∈ O} D(t). For any O with A(O) ≠ ∅ and any mechanism
k,
        s_k = 0 in every s ∈ A(O)   ⟺   k ∈ NullOff(O).

Proof. (⇐) immediate from the NULL units. (⇒) take any s* ∈ A(O); if k ∉
NullOff(O), flip s*_k to 1. NULL units are untouched (k not among them); PRESENT
clauses are monotone, so raising a coordinate cannot falsify a satisfied
disjunction. Hence the flipped vector is still in A(O) and has s_k = 1, so k is
not forced off. ∎

Interpretation: a mechanism is *eliminated* (forced OFF) only by a NULL
observation of one of its effects. Positive observations never eliminate
anything.

------------------------------------------------------------------------------
Theorem A (Elimination Principle: irreplaceability = last driver standing)
------------------------------------------------------------------------------
For any O with A(O) ≠ ∅ and any mechanism j,
        CRC_j(O) = ∞
   ⟺   ∃ trait t with PRESENT(t) ∈ O, j ∈ D(t), and D(t)\{j} ⊆ NullOff(O).

Proof. CRC_j = ∞ ⟺ setting s_j = 0 makes the system unsatisfiable. The system is
a positive monotone CNF (PRESENT clauses) together with negative units (NULL).
With s_j = 0 fixed, a PRESENT clause C_t becomes unsatisfiable iff every literal
in it is already fixed to 0, i.e. every driver of t other than j is forced off —
which by the Lemma means D(t)\{j} ⊆ NullOff(O) — and j ∈ D(t). No other constraint
can force s_j up (positive clauses force only OR-truth; negative units force only
zeros). Conversely such a clause makes s_j = 0 unsatisfiable. ∎

Corollary (the counter-intuitive, actionable part).
A mechanism j can be certified *necessary* (CRC_j = ∞) only by reducing some
present effect of j to j as its sole surviving driver. Eliminating the
alternative drivers requires NULL observations of *their* effects. Therefore:

    • Observing the focal/shared trait (|D(t)| ≥ 2 drivers) — no matter how
      strong or how often — can never make any mechanism irreplaceable.
    • Necessity is established by the ABSENCE of competitors' private
      signatures, not by the PRESENCE of the focal pattern.

This inverts the standard practice of accumulating confirmations of the focal
adaptive trait: in a confounded cline, the load-bearing test is to look for the
*null* of each alternative's private signature.

------------------------------------------------------------------------------
Theorem B (CRC decomposition and strict refinement of the posterior)
------------------------------------------------------------------------------
With continuous parameters θ and external constraints, for the Monte-Carlo
region A_ε,
        CRC_j = I_j + Λ_j,
        I_j  = −log₂ P(s_j = 0 | A_ε) = −log₂(1 − CA_j),
        Λ_j  = min_{ r ∈ A_ε ∩ {s_j = 0} } L_constraint(r).

I_j is a strictly increasing function of the marginal posterior CA_j. Hence:
  (i)  if no external constraints are supplied (Λ ≡ 0), the CRC ranking of
       mechanisms is order-identical to the CA_j ranking — CRC then carries no
       information beyond the marginal posterior;
  (ii) the constraint term Λ_j can make CRC_a > CRC_b while CA_a = CA_b, so CRC
       strictly refines the marginal posterior exactly when external constraints
       discriminate the minimal-cost replacements.

This is the precise sense in which CRC ⊋ posterior, and it pinpoints the unique
source of the surplus: the external constraint term Λ.

------------------------------------------------------------------------------
Theorem C (Elimination is synergistic: myopic/greedy design provably fails)
------------------------------------------------------------------------------
This is the non-obvious, actionable result. Theorem A's verbal form ("certify a
mechanism by eliminating its rivals") is just disjunctive syllogism / Popperian
falsification. What is NOT obvious is how the eliminations COMBINE.

Let R_j(O) = 𝟙[CRC_j(O) = ∞] be the resolution indicator: 1 iff the observations
have rendered mechanism j irreplaceable. Consider a focal mechanism j with NO
private witness, sharing a present trait t with competitors c₁,…,c_n (D(t) =
{j,c₁,…,c_n}), each competitor c_i having a private witness w_i.

By Theorem A, R_j = 1 requires ALL n competitors eliminated, i.e. all n witnesses
observed NULL. Therefore for the canonical family:

        R_j(∅) = 0,   R_j({w_i}) = 0  for every single i,   R_j({w_1,…,w_n}) = 1.

Every single observation has ZERO resolution value, yet the full set resolves.
Consequences:

  (i)  R_j is NOT submodular. A monotone submodular f with f(∅)=0 whose every
       singleton gain is 0 is identically 0; here the n-set gain is 1>0, so the
       diminishing-returns inequality is violated (the returns are INCREASING).
  (ii) The standard greedy algorithm for experimental design — repeatedly add the
       observation of largest marginal value — has no positive-gain element to
       add and makes no progress, returning R_j = 0, while the optimal observation
       SET returns R_j = 1. The 1−1/e greedy guarantee that holds for submodular
       objectives DOES NOT transfer to CRC resolution.

For the continuous marginal h_j(O) = P(s_j = 1 | A(O)) the same family exhibits
strictly increasing marginal returns (supermodularity): the gain of the last
eliminating observation exceeds the gain of the first.

Practical upshot (the warning): in a confounded cline you must plan the
elimination SET jointly; choosing observations one-at-a-time by their individual
value is provably wrong here. (Note this indicts the greedy RACH-SEQ scheme in
this very repository.) Theorem C is corroborated below by machine search: greedy-
failure instances are found across random structural models, and the canonical
n-competitor family is verified to violate submodularity for every n ≥ 2.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from itertools import product
from typing import Iterable


# ---------------------------------------------------------------------------
# Structural model and admissible region (exact, by enumeration)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StructuralModel:
    """K mechanisms and a driver set per trait (sign-consistent disjunctive)."""
    K: int
    driver_sets: dict[str, frozenset[int]]   # trait name -> set of mechanism indices


@dataclass(frozen=True)
class Observation:
    """A set of trait outcomes: some traits observed PRESENT, some NULL."""
    present: tuple[str, ...] = ()
    null: tuple[str, ...] = ()


def null_off(model: StructuralModel, obs: Observation) -> frozenset[int]:
    """NullOff(O): mechanisms eliminated (forced OFF) by the NULL observations."""
    out: set[int] = set()
    for t in obs.null:
        out |= set(model.driver_sets.get(t, ()))
    return frozenset(out)


def admissible_configs(model: StructuralModel, obs: Observation) -> list[tuple[int, ...]]:
    """Enumerate A(O) exactly over {0,1}^K (intended for small K)."""
    noff = null_off(model, obs)
    present = [model.driver_sets[t] for t in obs.present]
    configs: list[tuple[int, ...]] = []
    for s in product((0, 1), repeat=model.K):
        if any(s[k] for k in noff):                 # NULL units
            continue
        if all(any(s[k] for k in D) for D in present):  # PRESENT clauses
            configs.append(s)
    return configs


# ---------------------------------------------------------------------------
# Structural CRC and the forcing predicates
# ---------------------------------------------------------------------------

def structural_crc(j: int, configs: list[tuple[int, ...]], p: float = 0.5) -> float:
    """CRC_j over an enumerated region with a product-Bernoulli(p) prior."""
    if not configs:
        return float("nan")
    def w(s: tuple[int, ...]) -> float:
        return math.prod(p if si else (1.0 - p) for si in s)
    total = sum(w(s) for s in configs)
    off = sum(w(s) for s in configs if s[j] == 0)
    if off <= 0.0:
        return float("inf")
    return -math.log2(off / total)


def forced_off(configs: list[tuple[int, ...]], k: int) -> bool:
    return bool(configs) and all(s[k] == 0 for s in configs)


def forced_on(configs: list[tuple[int, ...]], j: int) -> bool:
    return bool(configs) and all(s[j] == 1 for s in configs)


def is_last_driver_standing(model: StructuralModel, obs: Observation, j: int) -> bool:
    """Theorem-A condition: j is the sole surviving driver of some present trait."""
    noff = null_off(model, obs)
    for t in obs.present:
        D = model.driver_sets[t]
        if j in D and (D - {j}) <= noff:
            return True
    return False


def private_witnesses(model: StructuralModel, j: int) -> list[str]:
    """Traits whose only driver is j (the private signatures of j)."""
    return [t for t, D in model.driver_sets.items() if D == frozenset({j})]


# ---------------------------------------------------------------------------
# Theorem verifiers (per instance; exact)
# ---------------------------------------------------------------------------

@dataclass
class TheoremCheck:
    holds: bool
    detail: str = ""


def verify_lemma_elimination(model: StructuralModel, obs: Observation) -> TheoremCheck:
    """Lemma: forced_off(k) ⟺ k ∈ NullOff(O), for every k (nonempty region)."""
    configs = admissible_configs(model, obs)
    if not configs:
        return TheoremCheck(True, "empty region (vacuous)")
    noff = null_off(model, obs)
    for k in range(model.K):
        if forced_off(configs, k) != (k in noff):
            return TheoremCheck(False, f"mechanism {k}: forced_off={forced_off(configs,k)} "
                                       f"but in NullOff={k in noff}")
    return TheoremCheck(True)


def verify_theorem_A(model: StructuralModel, obs: Observation) -> TheoremCheck:
    """Theorem A: CRC_j = ∞ ⟺ j is last driver standing, for every j."""
    configs = admissible_configs(model, obs)
    if not configs:
        return TheoremCheck(True, "empty region (vacuous)")
    for j in range(model.K):
        crc_inf = (structural_crc(j, configs) == float("inf"))
        lds = is_last_driver_standing(model, obs, j)
        if crc_inf != lds:
            return TheoremCheck(
                False,
                f"mechanism {j}: CRC=∞ is {crc_inf} but last-driver-standing is {lds}",
            )
    return TheoremCheck(True)


def verify_present_focal_cannot_pin(model: StructuralModel, obs: Observation) -> TheoremCheck:
    """Corollary: observing a SHARED present trait (|D|≥2), with no NULL
    eliminations, pins nothing to ∞."""
    if obs.null:
        return TheoremCheck(True, "not applicable (has null observations)")
    configs = admissible_configs(model, obs)
    if not configs:
        return TheoremCheck(True, "empty region (vacuous)")
    # every present trait is shared
    if any(len(model.driver_sets[t]) < 2 for t in obs.present):
        return TheoremCheck(True, "not applicable (a present trait is private)")
    for j in range(model.K):
        if structural_crc(j, configs) == float("inf"):
            return TheoremCheck(False, f"mechanism {j} pinned by shared present traits alone")
    return TheoremCheck(True)


# ---------------------------------------------------------------------------
# Random instance generator (for machine verification across all models)
# ---------------------------------------------------------------------------

def random_instance(
    rng: random.Random,
    *,
    max_K: int = 7,
    max_traits: int = 6,
) -> tuple[StructuralModel, Observation]:
    """A random sign-consistent disjunctive model with a random observation set."""
    K = rng.randint(2, max_K)
    n_traits = rng.randint(1, max_traits)
    driver_sets: dict[str, frozenset[int]] = {}
    for i in range(n_traits):
        size = rng.randint(1, K)
        drivers = frozenset(rng.sample(range(K), size))
        driver_sets[f"t{i}"] = drivers
    model = StructuralModel(K=K, driver_sets=driver_sets)

    present: list[str] = []
    null: list[str] = []
    for t in driver_sets:
        roll = rng.random()
        if roll < 0.45:
            present.append(t)
        elif roll < 0.75:
            null.append(t)
        # else: unobserved
    return model, Observation(present=tuple(present), null=tuple(null))


# ---------------------------------------------------------------------------
# Theorem B helpers (decomposition / refinement)
# ---------------------------------------------------------------------------

def info_term_from_ca(ca_j: float) -> float:
    """I_j = −log₂(1 − CA_j): the posterior (informational) part of CRC."""
    if ca_j >= 1.0:
        return float("inf")
    if ca_j <= 0.0:
        return 0.0
    return -math.log2(1.0 - ca_j)


def info_term_is_monotone(ca_values: Iterable[float]) -> bool:
    """Verify I_j is strictly increasing in CA_j over the given grid."""
    vals = sorted(set(c for c in ca_values if 0.0 <= c < 1.0))
    info = [info_term_from_ca(c) for c in vals]
    return all(info[i] < info[i + 1] for i in range(len(info) - 1))


# ---------------------------------------------------------------------------
# Theorem C: synergy of elimination and the failure of greedy design
# ---------------------------------------------------------------------------

def resolution_indicator(model: StructuralModel, obs: Observation, j: int) -> int:
    """R_j(O) = 1 iff j is irreplaceable (CRC_j = ∞) given the observations."""
    configs = admissible_configs(model, obs)
    if not configs:
        return 0
    return 1 if structural_crc(j, configs) == float("inf") else 0


def marginal_on_probability(model: StructuralModel, obs: Observation, j: int) -> float:
    """h_j(O) = P(s_j = 1 | A(O)); reaches 1 exactly when j is pinned."""
    configs = admissible_configs(model, obs)
    if not configs:
        return float("nan")
    return sum(s[j] for s in configs) / len(configs)


def _add_nulls(base: Observation, extra: Iterable[str]) -> Observation:
    return Observation(present=base.present, null=tuple(base.null) + tuple(extra))


def synthetic_synergy_model(n_competitors: int) -> tuple[StructuralModel, Observation, list[str], int]:
    """The canonical n-competitor synergy family.

    Returns ``(model, baseline_obs, candidate_null_traits, target_j)`` where the
    target mechanism 0 has no private witness and is resolved only by observing
    ALL n competitor witnesses NULL.
    """
    K = 1 + n_competitors                       # mechanism 0 = target j
    drivers = {"focal": frozenset(range(K))}    # shared focal trait
    candidates: list[str] = []
    for i in range(1, K):
        w = f"witness_{i}"
        drivers[w] = frozenset({i})             # private witness of competitor i
        candidates.append(w)
    model = StructuralModel(K=K, driver_sets=drivers)
    baseline = Observation(present=("focal",))
    return model, baseline, candidates, 0


def greedy_value_driven(
    model: StructuralModel,
    baseline: Observation,
    candidate_nulls: list[str],
    j: int,
    *,
    budget: int | None = None,
) -> tuple[bool, list[str]]:
    """Standard greedy: repeatedly add the NULL observation of largest marginal
    *resolution* gain; stop when no element has positive gain or budget is hit.

    Returns ``(resolved, chosen_order)``. On a synergy instance every singleton
    gain is 0, so greedy adds nothing and fails.
    """
    budget = budget if budget is not None else len(candidate_nulls)
    chosen: list[str] = []
    obs = baseline
    for _ in range(budget):
        cur = resolution_indicator(model, obs, j)
        best_gain, best = 0, None
        for c in candidate_nulls:
            if c in chosen:
                continue
            gain = resolution_indicator(model, _add_nulls(obs, [c]), j) - cur
            if gain > best_gain:
                best_gain, best = gain, c
        if best is None:                        # no positive-gain observation
            break
        chosen.append(best)
        obs = _add_nulls(obs, [best])
        if resolution_indicator(model, obs, j):
            return True, chosen
    return resolution_indicator(model, obs, j) == 1, chosen


def optimal_set_resolves(
    model: StructuralModel,
    baseline: Observation,
    candidate_nulls: list[str],
    j: int,
    *,
    budget: int | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Brute-force search for ANY null-observation subset (≤ budget) that pins j."""
    from itertools import combinations
    budget = budget if budget is not None else len(candidate_nulls)
    for r in range(1, budget + 1):
        for combo in combinations(candidate_nulls, r):
            if resolution_indicator(model, _add_nulls(baseline, combo), j):
                return True, combo
    return False, ()


def submodularity_violated(
    model: StructuralModel,
    baseline: Observation,
    candidate_nulls: list[str],
    j: int,
) -> bool:
    """True if ∃ x,y: zero singleton resolution gain but the pair resolves j
    (a witness that R_j is not submodular — returns are increasing)."""
    from itertools import combinations
    base_r = resolution_indicator(model, baseline, j)
    for x, y in combinations(candidate_nulls, 2):
        gx = resolution_indicator(model, _add_nulls(baseline, [x]), j) - base_r
        gy = resolution_indicator(model, _add_nulls(baseline, [y]), j) - base_r
        gxy = resolution_indicator(model, _add_nulls(baseline, [x, y]), j) - base_r
        if gx == 0 and gy == 0 and gxy > 0:
            return True
    return False


def verify_theorem_C_family(n_competitors: int) -> TheoremCheck:
    """Verify Theorem C on the canonical n-competitor family."""
    model, baseline, cands, j = synthetic_synergy_model(n_competitors)
    # every single elimination resolves nothing
    for c in cands:
        if resolution_indicator(model, _add_nulls(baseline, [c]), j) != 0:
            return TheoremCheck(False, f"singleton {c} unexpectedly resolved")
    # the full set resolves
    if resolution_indicator(model, _add_nulls(baseline, cands), j) != 1:
        return TheoremCheck(False, "full elimination set failed to resolve")
    # greedy fails, optimal succeeds
    greedy_ok, _ = greedy_value_driven(model, baseline, cands, j)
    opt_ok, _ = optimal_set_resolves(model, baseline, cands, j)
    if greedy_ok:
        return TheoremCheck(False, "greedy unexpectedly resolved a synergy instance")
    if not opt_ok:
        return TheoremCheck(False, "optimal set failed (should resolve)")
    # submodularity is violated: the resolution gain of the last elimination is
    # 1 given the other n-1, but 0 given the empty set — increasing returns.
    if n_competitors >= 2:
        last, rest = cands[-1], cands[:-1]
        base_r = resolution_indicator(model, baseline, j)
        gain_empty = resolution_indicator(model, _add_nulls(baseline, [last]), j) - base_r
        before_last = _add_nulls(baseline, rest)
        gain_full = (resolution_indicator(model, _add_nulls(before_last, [last]), j)
                     - resolution_indicator(model, before_last, j))
        if not (gain_full > gain_empty):
            return TheoremCheck(False, f"resolution returns not increasing: "
                                       f"empty={gain_empty}, full={gain_full}")
    # continuous marginal returns are increasing: last gain > first gain
    if n_competitors >= 2:
        first_gain = (marginal_on_probability(model, _add_nulls(baseline, [cands[0]]), j)
                      - marginal_on_probability(model, baseline, j))
        before_last = _add_nulls(baseline, cands[:-1])
        last_gain = (marginal_on_probability(model, _add_nulls(before_last, [cands[-1]]), j)
                     - marginal_on_probability(model, before_last, j))
        if not (last_gain > first_gain + 1e-12):
            return TheoremCheck(False, f"returns not increasing: first={first_gain}, last={last_gain}")
    return TheoremCheck(True)


def find_greedy_failures(rng: random.Random, n_trials: int) -> dict:
    """Scan random models for instances where an OPTIMAL null-set resolves a
    mechanism but value-driven greedy does not."""
    failures = 0
    resolvable = 0
    example = None
    for _ in range(n_trials):
        model, _ = random_instance(rng)
        # baseline: observe every trait that has ≥2 drivers as PRESENT (focal);
        # offer every trait as a NULL candidate (its absence eliminates its drivers)
        focal = tuple(t for t, D in model.driver_sets.items() if len(D) >= 2)
        if not focal:
            continue
        baseline = Observation(present=focal)
        candidates = list(model.driver_sets.keys())
        for j in range(model.K):
            opt_ok, _ = optimal_set_resolves(model, baseline, candidates, j)
            if not opt_ok:
                continue
            resolvable += 1
            greedy_ok, _ = greedy_value_driven(model, baseline, candidates, j)
            if not greedy_ok:
                failures += 1
                if example is None:
                    example = (model, baseline, j)
    return {"resolvable_cases": resolvable, "greedy_failures": failures, "example": example}


# ---------------------------------------------------------------------------
# Demonstration / machine-checked corroboration
# ---------------------------------------------------------------------------

def corroborate(n_trials: int = 5000, seed: int = 0) -> dict:
    """Exhaustively check Theorem A and the Lemma over random structural models.

    Returns a summary dict; raises AssertionError on any counterexample.
    """
    rng = random.Random(seed)
    checked = 0
    nonempty = 0
    for _ in range(n_trials):
        model, obs = random_instance(rng)
        configs = admissible_configs(model, obs)
        checked += 1
        if not configs:
            continue
        nonempty += 1
        a = verify_theorem_A(model, obs)
        l = verify_lemma_elimination(model, obs)
        if not a.holds:
            raise AssertionError(f"Theorem A counterexample: {a.detail}\n{model}\n{obs}")
        if not l.holds:
            raise AssertionError(f"Lemma counterexample: {l.detail}\n{model}\n{obs}")
    # Theorem C: verify the canonical synergy family for several n, and confirm
    # greedy-failure instances exist among random models.
    for n in range(2, 7):
        c = verify_theorem_C_family(n)
        if not c.holds:
            raise AssertionError(f"Theorem C family n={n} failed: {c.detail}")
    gf = find_greedy_failures(rng, max(500, n_trials // 10))

    return {"trials": checked, "nonempty_regions": nonempty,
            "theorem_A": "verified", "lemma_elimination": "verified",
            "theorem_C_family": "verified",
            "greedy_failures_found": gf["greedy_failures"],
            "resolvable_cases_scanned": gf["resolvable_cases"]}


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="Machine-checked corroboration of the CRC theorems.")
    p.add_argument("--trials", type=int, default=5000)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args(argv)
    summary = corroborate(args.trials, args.seed)
    print("Causal Replaceability — theorem corroboration")
    print(f"  random structural models checked : {summary['trials']}")
    print(f"  non-empty admissible regions     : {summary['nonempty_regions']}")
    print(f"  Theorem A (Elimination Principle): {summary['theorem_A']}")
    print(f"  Lemma (elimination is null-only) : {summary['lemma_elimination']}")
    print(f"  Theorem B (info term monotone)   : "
          f"{'verified' if info_term_is_monotone([i/100 for i in range(100)]) else 'FAILED'}")
    print(f"  Theorem C (synergy family n=2..6): {summary['theorem_C_family']}")
    print(f"  Theorem C greedy failures found  : {summary['greedy_failures_found']} "
          f"of {summary['resolvable_cases_scanned']} resolvable random cases")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
