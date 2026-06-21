"""Minimal sufficient explanations — an explanation-level summary of A_ε.

Motivation
----------
The per-switch marginals ``CA_j = P(s_j = 1 | A_ε)`` and the raw joint degeneracy
``D = H(S | A_ε)`` *undersell* what an admissible region actually establishes when
the mechanisms form a disjunction confound. On the published Campanula pattern,
the marginals read ``CA(S2) ≈ CA(S3) ≈ 0.71`` and ``R ≈ 0.13`` — which looks like
"nothing is resolved". But the real content of A_ε is sharp and useful:

    the minimal explanation is **either {S2} alone or {S3} alone**, ~50 / 50.

That is a precise finding (the confound is *between two single-mechanism
explanations*), not an absence of one. Two pathologies of the marginal/raw-entropy
summary produce the misleadingly low numbers:

  * a disjunction member has marginal ``CA ≈ 2/3`` by construction, so two
    confounded mechanisms both sit near 0.7 and neither looks decisive;
  * ``D = H(S | A_ε)`` counts entropy over *every* switch, including ones that
    are irrelevant or merely redundant given the pattern, inflating D and
    deflating ``R = 1 − D/K``.

This module summarises A_ε by its **minimal sufficient explanations** instead: the
inclusion-minimal sets of active mechanisms that reproduce the observed pattern,
each with its posterior mass. The associated *explanation* degeneracy /
resolvability then measure how concentrated the posterior is on a *single*
explanation — which is what a reader actually wants to know.

Why this also fixes the "resolution needs an idealised assay" problem
---------------------------------------------------------------------
When an honest, observable-based observation (e.g. the Campanula neutral-diversity
cline, which only the common-cause mechanism drives) pins one mechanism ON, every
accepted configuration becomes a *superset* of that mechanism, so the inclusion-
minimal explanation collapses to the single set ``{S3}`` and ``R_expl → 1``. The
switch-marginal ``R`` only crawls from 0.13 to 0.27 on the same observation
(because the now-*redundant* second mechanism keeps its marginal near 0.6); the
explanation-level summary correctly reports full resolution without resorting to a
direct switch-readout assay.

Definitions
-----------
on-set of a row
    the set of mechanisms that are ON in that accepted draw.
support
    the distinct on-sets appearing in A_ε.
minimal explanation
    an inclusion-minimal element of the support (no accepted on-set is a strict
    subset of it). The minimal explanations form an antichain.
mass of a minimal explanation E
    the posterior probability assigned to E, computed by giving each accepted row
    to the minimal explanation(s) it contains (a row whose on-set is a superset of
    several minimal explanations splits its weight equally among them — it is
    equally consistent with each as "the" cause).
explanation degeneracy  D_expl
    Shannon entropy (bits) of the mass distribution over minimal explanations.
explanation resolvability  R_expl
    ``1 − D_expl / log2(M)`` for ``M`` minimal explanations (``1.0`` if ``M ≤ 1``):
    1 when the posterior concentrates on a single explanation, 0 when the minimal
    explanations are equiprobable.

The functions are simulator-agnostic: they consume accepted rows and a list of
switch objects (anything with a ``.name``) and have no Campanula dependency.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Explanation:
    """One inclusion-minimal sufficient explanation and its posterior mass."""
    mechanisms: frozenset[str]
    mass: float

    def describe(self) -> str:
        body = "{" + ", ".join(sorted(self.mechanisms)) + "}" if self.mechanisms else "{∅ (no mechanism)}"
        return f"{body}  mass={self.mass:.3f}"


@dataclass
class ExplanationDecomposition:
    """The minimal-sufficient-explanation summary of an admissible region."""
    n_accepted: int
    n_configs: int                       # distinct on-sets present in A_ε
    explanations: list[Explanation]      # minimal explanations, sorted by mass desc
    D_expl: float                        # entropy over explanation mass (bits)
    R_expl: float                        # 1 − D_expl/log2(M), in [0,1]; 1.0 if M ≤ 1

    def describe(self) -> str:
        lines = [
            f"Minimal sufficient explanations (|A_ε| = {self.n_accepted}, "
            f"{self.n_configs} distinct configurations)",
            f"  D_expl = {self.D_expl:.3f} bits   R_expl = {self.R_expl:.3f}",
        ]
        for e in self.explanations:
            lines.append(f"    {e.describe()}")
        return "\n".join(lines)


def _on_set(row: dict, names: list[str]) -> frozenset[str]:
    return frozenset(n for n in names if row.get(n))


def _minimal_elements(support: list[frozenset[str]]) -> list[frozenset[str]]:
    """Inclusion-minimal elements (antichain) of a family of sets."""
    return [s for s in support
            if not any(other < s for other in support)]


def minimal_explanations(accepted_rows: list[dict], switches) -> ExplanationDecomposition:
    """Decompose A_ε into its minimal sufficient explanations.

    Parameters
    ----------
    accepted_rows:
        Accepted (theta, s) rows from A_ε; each exposes the switch states as
        truthy/falsy values under the switch ``.name`` keys.
    switches:
        Sequence of switch objects (anything with a ``.name`` attribute).

    Returns
    -------
    ExplanationDecomposition
        The minimal explanations with masses, plus ``D_expl`` / ``R_expl``.

    Notes
    -----
    Empty ``A_ε`` is non-estimable: the explanations list is empty and
    ``D_expl`` / ``R_expl`` are ``NaN`` (consistent with the conditional-quantity
    NaN policy used elsewhere in RACH).
    """
    names = [sw.name for sw in switches]
    n = len(accepted_rows)
    if n == 0:
        return ExplanationDecomposition(
            n_accepted=0, n_configs=0, explanations=[],
            D_expl=float("nan"), R_expl=float("nan"),
        )

    config_counts = Counter(_on_set(r, names) for r in accepted_rows)
    support = list(config_counts)
    minimal = _minimal_elements(support)

    # Assign each row's mass to the minimal explanation(s) it contains. A row
    # whose on-set is a superset of several minimal explanations is equally
    # consistent with each being "the" cause, so it splits its weight.
    mass = {m: 0.0 for m in minimal}
    for on_set, count in config_counts.items():
        contained = [m for m in minimal if m <= on_set]
        if not contained:
            continue                              # cannot happen: on_set ⊇ some minimal
        share = count / len(contained)
        for m in contained:
            mass[m] += share
    total = sum(mass.values())
    mass = {m: v / total for m, v in mass.items()} if total else mass

    D_expl = -sum(p * math.log2(p) for p in mass.values() if p > 0)
    D_expl = abs(D_expl)                          # entropy ≥ 0; avoid -0.0 from rounding
    M = len(minimal)
    R_expl = 1.0 if M <= 1 else max(0.0, 1.0 - D_expl / math.log2(M))

    explanations = sorted(
        (Explanation(mechanisms=m, mass=round(p, 4)) for m, p in mass.items()),
        key=lambda e: -e.mass,
    )
    return ExplanationDecomposition(
        n_accepted=n, n_configs=len(support), explanations=explanations,
        D_expl=round(D_expl, 4), R_expl=round(R_expl, 4),
    )


def explanation_resolvability(accepted_rows: list[dict], switches) -> float:
    """Convenience: the explanation-level resolvability ``R_expl`` of A_ε."""
    return minimal_explanations(accepted_rows, switches).R_expl


def explanation_nov(candidate, accepted_rows: list[dict], switches) -> float:
    """Exact preposterior EVSI of a candidate observation on ``R_expl``.

    For a candidate whose outcomes partition (or sub-select) A_ε, this is

        EVSI(q) = Σ_outcome  p(outcome | A_ε) · [ R_expl(A_ε | outcome) − R_expl(A_ε) ]

    where ``p(outcome | A_ε)`` is the empirical predictive probability of the
    outcome — the fraction of the current admissible region consistent with it.
    Unlike the heuristic ordinal NOV, this is a genuine expectation over the
    region's own predictive distribution and needs no fresh ABC re-inference.

    Parameters
    ----------
    candidate:
        A ``CandidateObservation`` (with ``.outcomes``, each exposing
        ``.extra_pattern_rows``).
    accepted_rows, switches:
        The current admissible region and the switch list.
    """
    from causal_model.rach_seq import filter_by_outcome

    n = len(accepted_rows)
    if n == 0:
        return float("nan")
    R0 = explanation_resolvability(accepted_rows, switches)
    evsi = 0.0
    for outcome in candidate.outcomes:
        sub = filter_by_outcome(accepted_rows, outcome.extra_pattern_rows)
        if not sub:
            continue
        p = len(sub) / n
        R_sub = explanation_resolvability(sub, switches)
        evsi += p * (R_sub - R0)
    return round(evsi, 4)
