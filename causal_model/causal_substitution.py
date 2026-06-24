"""Causal Substitution Matrix (CSM) — which mechanisms compensate for which.

The CSM reveals the replacement network among mechanisms: when mechanism j
is counterfactually ablated, which other mechanisms k tend to become more
active in the surviving accepted draws?

Definition
----------
    CSM_{j→k} = E[s_k | A_ε, s_j=0] − E[s_k | A_ε]

A positive entry means k *substitutes* for j: when j is absent, k must be
present more often to reproduce the observed pattern.  A negative entry means
k *co-requires* j: removing j also tends to remove k from the accepted
region.  An entry near zero means k is informationally independent of j.

Interpretation
--------------
In a two-mechanism disjunction confound (S2 OR S3 generates the pattern),
the CSM will show:

    CSM_{S2→S3} > 0  (when S2 is absent, S3 compensates)
    CSM_{S3→S2} > 0  (when S3 is absent, S2 compensates)

A common-cause mechanism that co-activates several pathways will show
negative off-diagonal entries: ablating the common cause removes its
downstream pathways from A_ε simultaneously.

Constraint bottleneck linkage
-----------------------------
A high |CSM_{j→k}| combined with a high constraint penalty for k (from
external_constraints.py) identifies the substitution-bottleneck pair: the
pathway that most needs to be constrained to prevent the replacement of j.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model.counterfactual_ablation import ablate_switch


@dataclass
class CSMEntry:
    """One off-diagonal entry of the Causal Substitution Matrix."""
    ablated: str       # j: the mechanism that was removed
    target: str        # k: the mechanism whose activity changed
    delta: float       # E[s_k | A_ε, s_j=0] − E[s_k | A_ε]
    baseline: float    # E[s_k | A_ε]
    conditional: float # E[s_k | A_ε, s_j=0]
    n_ablated: int     # |A_ε ∩ {s_j=0}|

    @property
    def is_substitute(self) -> bool:
        return self.delta > 0.05

    @property
    def is_corequired(self) -> bool:
        return self.delta < -0.05

    def describe(self) -> str:
        sign = "+" if self.delta >= 0 else ""
        rel = "substitutes" if self.is_substitute else ("co-requires" if self.is_corequired else "independent")
        return (f"CSM[{self.ablated}→{self.target}] = {sign}{self.delta:.3f}  "
                f"({self.baseline:.3f} → {self.conditional:.3f})  [{rel}]")


def causal_substitution_matrix(
    accepted_rows: list[dict],
    switches,
) -> list[CSMEntry]:
    """Compute all off-diagonal CSM entries.

    Parameters
    ----------
    accepted_rows:
        The admissible region A_ε.
    switches:
        Sequence of switch objects with a ``.name`` attribute.

    Returns
    -------
    list[CSMEntry]
        One entry per ordered pair (j, k) with j ≠ k.  Sorted by |delta|
        descending (largest substitution effects first).
    """
    names = [sw.name for sw in switches]
    n = len(accepted_rows)
    if n == 0:
        return []

    # Baseline marginals E[s_k | A_ε]
    baseline = {name: sum(1 for r in accepted_rows if r.get(name)) / n
                for name in names}

    entries: list[CSMEntry] = []
    for j in names:
        ablated = ablate_switch(accepted_rows, j)
        n_abl = len(ablated)
        if n_abl == 0:
            # j is indispensable — conditional expectations undefined
            for k in names:
                if k == j:
                    continue
                entries.append(CSMEntry(
                    ablated=j, target=k,
                    delta=float("nan"),
                    baseline=round(baseline[k], 4),
                    conditional=float("nan"),
                    n_ablated=0,
                ))
            continue

        for k in names:
            if k == j:
                continue
            cond = sum(1 for r in ablated if r.get(k)) / n_abl
            delta = cond - baseline[k]
            entries.append(CSMEntry(
                ablated=j, target=k,
                delta=round(delta, 4),
                baseline=round(baseline[k], 4),
                conditional=round(cond, 4),
                n_ablated=n_abl,
            ))

    entries.sort(key=lambda e: abs(e.delta) if e.delta == e.delta else -1, reverse=True)
    return entries


def csm_dict(
    accepted_rows: list[dict],
    switches,
) -> dict[tuple[str, str], float]:
    """Return CSM as a dict ``{(j, k): delta}`` for easy lookup.

    Keys are ``(ablated_switch, target_switch)`` pairs.
    """
    return {(e.ablated, e.target): e.delta
            for e in causal_substitution_matrix(accepted_rows, switches)}


def substitutes_for(
    switch_name: str,
    accepted_rows: list[dict],
    switches,
    *,
    threshold: float = 0.05,
) -> list[tuple[str, float]]:
    """Which switches tend to substitute for *switch_name* when it is ablated?

    Returns
    -------
    list of (switch_name, delta) pairs, sorted by delta descending,
    filtered to |delta| > threshold.
    """
    entries = [e for e in causal_substitution_matrix(accepted_rows, switches)
               if e.ablated == switch_name and e.delta == e.delta  # finite
               and e.delta > threshold]
    return [(e.target, e.delta) for e in sorted(entries, key=lambda e: -e.delta)]
