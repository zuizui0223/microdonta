"""Head-to-head: what CRC / CSM add over existing causal-inference summaries.

A methods paper must show its quantity is not a re-packaging of an established
one. This module computes, on the *same* admissible region A_ε, the verdicts of
the standard tools next to CRC / CSM, so the differences are numerical rather
than rhetorical.

The established summaries
-------------------------
Bayesian model averaging / model selection (``model_posteriors``)
    Treat each distinct mechanism on-set as a discrete model M and report its
    posterior probability P(M | data) = (fraction of A_ε with that on-set). This
    is exactly model selection over the 2^K structures, with no structures
    pre-enumerated. It answers "which combination is most probable", but every
    quantity it yields is a function of the *data-only* posterior.

Marginal switch posterior (``marginal_posteriors``)
    CA_j = P(s_j = 1 | A_ε). The per-mechanism inclusion probability. A monotone
    function of nothing external — pure posterior.

What CRC / CSM add
------------------
Causal Replaceability Cost
    CRC_j folds in *external constraints* (literature effect sizes, hard
    probability bounds) by costing the cheapest pattern-preserving replacement
    of mechanism j. When constraints are absent CRC is a monotone function of
    CA_j and adds nothing — but with constraints it can separate mechanisms that
    every data-only summary (BMA, marginal posterior, model selection) ties.
    This is the formal sense in which CRC ⊋ posterior.

Causal Substitution Matrix
    CSM_{j→k} = E[s_k | s_j=0] − E[s_k] is a *conditional* structure that no
    marginal summary exposes: it names which mechanism compensates for which.
    Sensitivity analysis perturbs inputs and watches outputs; CSM instead reads
    the substitution network directly off the admissible region.

The headline comparison (``compare_on_constraint_separated``)
-------------------------------------------------------------
On the constraint-separated scenario, model selection, BMA and the marginal
posterior all tie thermal vs resource; CRC-with-constraints separates them.
The function returns the numbers that make this concrete.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from causal_model.causal_replaceability import crc_profile
from causal_model.causal_substitution import csm_dict
from causal_model.external_constraints import Constraint


# ---------------------------------------------------------------------------
# The established data-only summaries
# ---------------------------------------------------------------------------

def _on_set(row: dict, names: list[str]) -> frozenset[str]:
    return frozenset(n for n in names if row.get(n))


def model_posteriors(accepted_rows: list[dict], switches) -> dict[frozenset, float]:
    """Bayesian model probabilities over mechanism on-sets (model selection / BMA).

    Returns ``{on_set: P(model | data)}`` — the posterior probability of each
    distinct mechanism combination, sorted by probability descending.
    """
    names = [sw.name for sw in switches]
    n = len(accepted_rows)
    if n == 0:
        return {}
    counts = Counter(_on_set(r, names) for r in accepted_rows)
    return dict(sorted(((k, v / n) for k, v in counts.items()),
                       key=lambda kv: -kv[1]))


def marginal_posteriors(accepted_rows: list[dict], switches) -> dict[str, float]:
    """Marginal switch posteriors CA_j = P(s_j = 1 | A_ε)."""
    names = [sw.name for sw in switches]
    n = len(accepted_rows)
    if n == 0:
        return {name: float("nan") for name in names}
    return {name: round(sum(1 for r in accepted_rows if r.get(name)) / n, 4)
            for name in names}


# ---------------------------------------------------------------------------
# Side-by-side comparison
# ---------------------------------------------------------------------------

@dataclass
class MethodComparison:
    """All summaries computed on one admissible region."""
    n_accepted: int
    model_posteriors: dict[frozenset, float]
    marginal_posteriors: dict[str, float]
    crc_data_only: dict[str, float]
    crc_constrained: dict[str, float]
    csm: dict[tuple[str, str], float]

    def separates(self, a: str, b: str, *, tol: float = 0.1) -> dict[str, bool]:
        """Does each method distinguish mechanisms *a* and *b*?

        Returns a dict ``{method_name: bool}`` — True if the method assigns the
        two mechanisms materially different scores.
        """
        def _diff(d):
            va, vb = d.get(a), d.get(b)
            if va == float("inf") or vb == float("inf"):
                return va != vb
            if va is None or vb is None or va != va or vb != vb:
                return False
            return abs(va - vb) > tol

        # model selection: compare P({a}) vs P({b}) single-mechanism models
        p_a = self.model_posteriors.get(frozenset({a}), 0.0)
        p_b = self.model_posteriors.get(frozenset({b}), 0.0)
        model_sep = abs(p_a - p_b) > tol

        return {
            "model_selection_BMA": model_sep,
            "marginal_posterior": _diff(self.marginal_posteriors),
            "CRC_data_only": _diff(self.crc_data_only),
            "CRC_with_constraints": _diff(self.crc_constrained),
        }


def compare_methods(
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
) -> MethodComparison:
    """Compute every summary on one admissible region."""
    return MethodComparison(
        n_accepted=len(accepted_rows),
        model_posteriors=model_posteriors(accepted_rows, switches),
        marginal_posteriors=marginal_posteriors(accepted_rows, switches),
        crc_data_only=crc_profile(accepted_rows, switches, constraints=None),
        crc_constrained=crc_profile(accepted_rows, switches, constraints=constraints or []),
        csm=csm_dict(accepted_rows, switches),
    )


def compare_on_constraint_separated(
    n_attempts: int = 30000, seed: int = 1,
) -> tuple[MethodComparison, dict[str, bool]]:
    """The headline demonstration: only CRC-with-constraints separates the pair.

    Returns ``(comparison, separation_verdicts)`` where the verdicts dict shows
    each method's True/False on distinguishing thermal vs resource.
    """
    from causal_model.worked_examples.constraint_separated_replacement import (
        _abc_accept, _switches, literature_constraints,
    )
    sw = _switches()
    acc = _abc_accept(n_attempts, seed)
    comp = compare_methods(acc, sw, constraints=literature_constraints())
    verdict = comp.separates("thermal", "resource")
    return comp, verdict


def print_comparison(comp: MethodComparison, a: str, b: str) -> None:
    """Print a readable side-by-side of all methods for mechanisms a vs b."""
    def fmt(x):
        if x == float("inf"):
            return "∞"
        if x != x:
            return "nan"
        return f"{x:.3f}"

    print("=" * 70)
    print(f"Method comparison on |A_ε| = {comp.n_accepted}   ({a} vs {b})")
    print("=" * 70)
    pa = comp.model_posteriors.get(frozenset({a}), 0.0)
    pb = comp.model_posteriors.get(frozenset({b}), 0.0)
    print(f"  model selection / BMA   P({{{a}}})={pa:.3f}   P({{{b}}})={pb:.3f}")
    print(f"  marginal posterior CA   {a}={comp.marginal_posteriors[a]:.3f}   "
          f"{b}={comp.marginal_posteriors[b]:.3f}")
    print(f"  CRC (data only)         {a}={fmt(comp.crc_data_only[a])}   "
          f"{b}={fmt(comp.crc_data_only[b])}")
    print(f"  CRC (+ constraints)     {a}={fmt(comp.crc_constrained[a])}   "
          f"{b}={fmt(comp.crc_constrained[b])}")
    print("-" * 70)
    verdict = comp.separates(a, b)
    for method, sep in verdict.items():
        mark = "SEPARATES" if sep else "ties     "
        print(f"  {mark}  {method}")
    print("=" * 70)


def main(argv=None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--n-attempts", type=int, default=30000)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args(argv)
    comp, _ = compare_on_constraint_separated(args.n_attempts, args.seed)
    print_comparison(comp, "thermal", "resource")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
