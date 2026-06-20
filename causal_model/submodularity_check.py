"""Is RACH-SEQ's greedy observation selection near-optimal? Submodularity check.

RACH-SEQ picks observations greedily (largest expected edge-cut / resolvability
gain first). Greedy maximisation carries a classical guarantee — it reaches at
least ``(1 − 1/e) ≈ 0.63`` of the optimal value — **iff** the objective is a
monotone non-decreasing, non-negative, *submodular* set function (Nemhauser,
Wolsey & Fisher 1978). This module tests, empirically and per system, whether
the RACH resolvability objective

    g(O) = R_RACH( A_ε filtered by the realised outcomes of the observations in O )

actually has those three properties, and if so reports that the greedy guarantee
applies. It also brute-forces the true optimum on small observation sets and
checks the realised greedy/optimum ratio against the bound.

Submodularity (diminishing returns) for ``A ⊆ B`` and ``e ∉ B``:

    g(A ∪ {e}) − g(A)  ≥  g(B ∪ {e}) − g(B)

Information gain is *not* submodular in general; it is when the observations are
conditionally independent given the latent state. RACH's observations are
deterministic feature thresholds, so submodularity is a property to be *checked*,
not assumed — which is what this module does.

Usage
-----
    python -m causal_model.submodularity_check
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from itertools import combinations


# ---------------------------------------------------------------------------
# Realised-filter objective
# ---------------------------------------------------------------------------

def realised_filters(candidates, outcome_overrides: dict[str, str]) -> dict[str, list[dict]]:
    """Map each candidate to the pattern rows of its realised outcome (under the
    chosen truth ``outcome_overrides``)."""
    out: dict[str, list[dict]] = {}
    for cand in candidates:
        if not cand.outcomes:
            continue
        name = outcome_overrides.get(cand.name)
        if name is None:
            continue
        oc = next((o for o in cand.outcomes if o.name == name), None)
        if oc is not None:
            out[cand.name] = oc.extra_pattern_rows
    return out


def _g(accepted_rows, switches, filters_by_name, subset, min_size: int):
    """g(subset) = resolvability of A_ε filtered by every observation in subset.
    Returns None when the filtered region is smaller than ``min_size``."""
    from causal_model.rach_seq import filter_by_outcome
    from causal_model.causal_admissibility import causal_resolvability
    rows = accepted_rows
    for name in subset:
        rows = filter_by_outcome(rows, filters_by_name[name])
    if len(rows) < min_size:
        return None
    return causal_resolvability(rows, switches)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@dataclass
class SubmodularityResult:
    n_observations: int
    n_pairs_checked: int
    n_violations: int
    max_violation: float            # largest g-increase that breaks diminishing returns
    monotone: bool                  # g never decreases when an observation is added
    nonnegative: bool               # g(O) >= 0 everywhere it is estimable
    submodular: bool                # within tolerance
    greedy_guarantee_applies: bool  # monotone & nonneg & submodular
    greedy_value: float = float("nan")
    optimal_value: float = float("nan")
    greedy_ratio: float = float("nan")     # greedy / optimal (>= 1-1/e if guarantee holds)
    bound: float = 1.0 - 0.36787944117144233  # 1 - 1/e
    violations: list[tuple[str, float]] = field(default_factory=list)

    def describe(self) -> str:
        lines = [
            f"submodularity check over {self.n_observations} observations",
            f"  pairs checked       : {self.n_pairs_checked}",
            f"  violations          : {self.n_violations} "
            f"(max magnitude {self.max_violation:.4f})",
            f"  monotone            : {self.monotone}",
            f"  non-negative        : {self.nonnegative}",
            f"  submodular          : {self.submodular}",
            f"  greedy guarantee    : {self.greedy_guarantee_applies} "
            f"(1 - 1/e = {self.bound:.3f})",
        ]
        if self.optimal_value == self.optimal_value:  # not nan
            lines.append(
                f"  greedy/optimal      : {self.greedy_ratio:.3f} "
                f"(greedy R={self.greedy_value:.3f}, optimal R={self.optimal_value:.3f})")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Submodularity test
# ---------------------------------------------------------------------------

def check_submodularity(
    accepted_rows: list[dict],
    switches,
    filters_by_name: dict[str, list[dict]],
    *,
    min_size: int = 8,
    tol: float = 1e-9,
) -> SubmodularityResult:
    """Exhaustively test diminishing returns over all ``A ⊆ B, e ∉ B`` triples.

    Estimable subsets only (those whose filtered region is ≥ ``min_size``) enter
    the comparison; a subset that filters away is treated as not estimable and
    skipped, never as a violation.
    """
    names = sorted(filters_by_name)
    n = len(names)

    # cache g over all subsets
    gcache: dict[frozenset, float | None] = {}

    def g(subset) -> float | None:
        key = frozenset(subset)
        if key not in gcache:
            gcache[key] = _g(accepted_rows, switches, filters_by_name, key, min_size)
        return gcache[key]

    n_pairs = 0
    n_viol = 0
    max_viol = 0.0
    monotone = True
    nonneg = True
    violations: list[tuple[str, float]] = []

    # monotonicity + non-negativity over every estimable subset/extension
    for size in range(0, n + 1):
        for sub in combinations(names, size):
            gv = g(sub)
            if gv is None:
                continue
            if gv < -tol:
                nonneg = False
            for e in names:
                if e in sub:
                    continue
                gve = g(tuple(sorted(set(sub) | {e})))
                if gve is None:
                    continue
                if gve < gv - 1e-6:
                    monotone = False

    # diminishing returns: for A ⊆ B and e ∉ B
    for sa in range(0, n + 1):
        for A in combinations(names, sa):
            gA = g(A)
            if gA is None:
                continue
            setA = set(A)
            for sb in range(sa, n + 1):
                for B in combinations(names, sb):
                    setB = set(B)
                    if not setA <= setB:
                        continue
                    gB = g(B)
                    if gB is None:
                        continue
                    for e in names:
                        if e in setB:
                            continue
                        gAe = g(tuple(sorted(setA | {e})))
                        gBe = g(tuple(sorted(setB | {e})))
                        if gAe is None or gBe is None:
                            continue
                        marg_A = gAe - gA
                        marg_B = gBe - gB
                        n_pairs += 1
                        if marg_B - marg_A > 1e-6:   # diminishing returns broken
                            n_viol += 1
                            v = marg_B - marg_A
                            if v > max_viol:
                                max_viol = v
                            violations.append((f"A={A} B={B} +{e}", round(v, 4)))

    submodular = n_viol == 0
    guarantee = submodular and monotone and nonneg

    res = SubmodularityResult(
        n_observations=n, n_pairs_checked=n_pairs, n_violations=n_viol,
        max_violation=round(max_viol, 4), monotone=monotone, nonnegative=nonneg,
        submodular=submodular, greedy_guarantee_applies=guarantee,
        violations=violations[:10],
    )

    # brute-force greedy vs optimal on the full ground set (target size = n)
    gv, ov = _greedy_vs_optimal(g, names)
    if gv is not None and ov is not None and ov > 1e-9:
        res.greedy_value = round(gv, 4)
        res.optimal_value = round(ov, 4)
        res.greedy_ratio = round(gv / ov, 4)
    return res


def _greedy_vs_optimal(g, names):
    """Greedy selection value vs brute-force optimum over all subsets."""
    # greedy: add the element with the largest marginal gain until none helps
    chosen: set = set()
    cur = g(())
    if cur is None:
        cur = 0.0
    while True:
        best_e, best_val = None, cur
        for e in names:
            if e in chosen:
                continue
            gv = g(tuple(sorted(chosen | {e})))
            if gv is None:
                continue
            if gv > best_val + 1e-9:
                best_val, best_e = gv, e
        if best_e is None:
            break
        chosen.add(best_e)
        cur = best_val
    greedy_value = cur

    # optimal: best estimable subset value
    optimal = None
    for size in range(0, len(names) + 1):
        for sub in combinations(names, size):
            gv = g(sub)
            if gv is None:
                continue
            if optimal is None or gv > optimal:
                optimal = gv
    return greedy_value, optimal


# ---------------------------------------------------------------------------
# Demonstration on the Bergmann confound
# ---------------------------------------------------------------------------

def run_bergmann_submodularity(truth: str = "fasting_endurance",
                               n_attempts: int = 4000, seed: int = 1,
                               min_size: int = 8) -> SubmodularityResult:
    """Check submodularity of the resolvability objective on the Bergmann assays."""
    from causal_model.bergmann_worked_example import (
        _switches, _abc_accept, _candidate_observations, _truth_overrides,
    )
    switches = _switches()
    acc = _abc_accept(n_attempts, seed)
    cands = _candidate_observations(truth)
    filters = realised_filters(cands, _truth_overrides(truth))
    return check_submodularity(acc, switches, filters, min_size=min_size)


def run_eco_rules_submodularity(n_attempts: int = 4000, seed: int = 1,
                                min_size: int = 8) -> dict[str, SubmodularityResult]:
    """Check submodularity for each resolvable ecological rule's assay panel."""
    from causal_model.ecological_rules_validation import (
        ECOLOGICAL_RULES, _rule_switches, _abc_accept, _mechanism_assays,
    )
    out: dict[str, SubmodularityResult] = {}
    for rule in ECOLOGICAL_RULES:
        switches = _rule_switches(rule)
        acc = _abc_accept(rule, n_attempts, seed)
        cands = _mechanism_assays(rule)
        # realised truth: each driving mechanism present iff it is the attributed
        # truth; for unresolved rules use the first mechanism as a representative
        truth = rule.literature_truth if rule.literature_truth != "unresolved" else rule.mechanisms[0]
        overrides = {}
        for c in cands:
            if not c.outcomes:
                continue
            mech = c.target_switches[0]
            present = (mech == truth)
            overrides[c.name] = c.outcomes[0].name if present else c.outcomes[1].name
        filters = realised_filters(cands, overrides)
        out[rule.name] = check_submodularity(acc, switches, filters, min_size=min_size)
    return out


def print_report(res: SubmodularityResult, title: str = "") -> None:
    print("=" * 64)
    print(f"RACH-SEQ greedy near-optimality (submodularity) {title}".rstrip())
    print("=" * 64)
    print(res.describe())


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Check RACH-SEQ greedy submodularity guarantee.")
    p.add_argument("--n-attempts", type=int, default=4000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--min-size", type=int, default=8)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    berg = run_bergmann_submodularity(n_attempts=args.n_attempts, seed=args.seed,
                                      min_size=args.min_size)
    print_report(berg, "— Bergmann assays")
    print()
    for name, res in run_eco_rules_submodularity(n_attempts=args.n_attempts, seed=args.seed,
                                                 min_size=args.min_size).items():
        print_report(res, f"— {name}")
        print()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
