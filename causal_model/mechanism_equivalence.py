"""Mechanism equivalence structure — the structured object RACH reports in place
of (or alongside) the scalar causal degeneracy.

Given an accepted admissible region A_e (list of accepted (theta, s) rows, each
exposing the boolean switch states), this module recovers *which mechanisms the
data can and cannot tell apart*, as a structure rather than a single number:

  * pinned switches   — CA_j near 0 or 1 (the data fix them);
  * free switches     — CA_j near 1/2 (the data leave them open);
  * a confounding graph over switches, whose edges are the statistically coupled
    (high mutual-information) pairs within A_e;
  * for each edge, a *logical relation* read off the within-A_e joint table:
    disjunction ("at least one"), mutual exclusion ("at most one"), or
    equivalence ("always equal / always opposite");
  * the count of admissible vs. forbidden switch configurations.

This is the simulation-based, switch-space analogue of an observational
equivalence (Markov-equivalence) class: it characterises the *set* of mechanism
combinations the data admit and the relations among them, not just the entropy of
that set. The primitives (mutual information, a coupling graph) are standard; the
contribution is using them to report the mechanism equivalence structure as the
inference's output object.

The functions here are simulator-agnostic: they consume accepted rows and a list
of switches (anything with a ``.name``) and have no Campanula dependency.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations


PIN_LOW = 0.2          # CA_j <= PIN_LOW  -> pinned OFF
PIN_HIGH = 0.8         # CA_j >= PIN_HIGH -> pinned ON
# NB: a switch in a disjunction (A∨B) has marginal CA ≈ 2/3 by construction, so
# the pin thresholds are deliberately strict — disjunction members are "free but
# coupled", reported via the confounding edges, not as pinned.
EDGE_MI = 0.03          # mutual information (bits) above which a pair is an edge
ZERO_CELL = 0.02        # joint-cell probability treated as "structurally absent"


@dataclass
class ConfoundingEdge:
    """A coupled switch pair within A_e and the logical relation it encodes."""
    a: str
    b: str
    phi: float                  # binary correlation in [-1, 1]
    mutual_information: float    # bits
    relation: str                # disjunction / mutual_exclusion / equivalence / anti_equivalence / coupled
    joint: dict[tuple[int, int], float]  # P(a=x, b=y) over A_e

    def describe(self) -> str:
        rel = {
            "disjunction":      f"{self.a} ∨ {self.b} required (at least one ON)",
            "mutual_exclusion": f"at most one of {self.a}, {self.b} (not both)",
            "equivalence":      f"{self.a} ≡ {self.b} (always equal)",
            "anti_equivalence": f"{self.a} = ¬{self.b} (always opposite)",
            "coupled":          f"{self.a}, {self.b} statistically coupled",
        }[self.relation]
        return f"{rel}  [phi={self.phi:+.2f}, MI={self.mutual_information:.3f} bits]"


@dataclass
class EquivalenceStructure:
    """The mechanism equivalence structure recovered from A_e."""
    n_accepted: int
    ca_j: dict[str, float]
    pinned_on: list[str]
    pinned_off: list[str]
    free: list[str]
    edges: list[ConfoundingEdge]
    n_admissible_configs: int
    n_total_configs: int
    substitutable_groups: list[list[str]] = field(default_factory=list)

    def describe(self) -> str:
        lines = [
            f"Mechanism equivalence structure (|A_ε| = {self.n_accepted})",
            f"  admissible configurations: {self.n_admissible_configs} of {self.n_total_configs}",
        ]
        if self.pinned_on:
            lines.append(f"  pinned ON : {', '.join(self.pinned_on)}")
        if self.pinned_off:
            lines.append(f"  pinned OFF: {', '.join(self.pinned_off)}")
        if self.free:
            lines.append(f"  free      : {', '.join(self.free)}")
        if self.edges:
            lines.append("  confounding edges:")
            for e in self.edges:
                lines.append(f"    {e.describe()}")
        else:
            lines.append("  confounding edges: none (no coupled mechanisms)")
        if self.substitutable_groups:
            grps = "; ".join("{" + ", ".join(g) + "}" for g in self.substitutable_groups)
            lines.append(f"  substitutable groups: {grps}")
        return "\n".join(lines)


def _column(rows: list[dict], name: str) -> list[int]:
    return [1 if r.get(name) else 0 for r in rows]


def _phi(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / n
    va, vb = ma - ma * ma, mb - mb * mb
    return cov / math.sqrt(va * vb) if va > 0 and vb > 0 else float("nan")


def _joint(a: list[int], b: list[int]) -> dict[tuple[int, int], float]:
    n = len(a)
    out: dict[tuple[int, int], float] = {}
    for x in (0, 1):
        for y in (0, 1):
            out[(x, y)] = sum(1 for i in range(n) if a[i] == x and b[i] == y) / n if n else 0.0
    return out


def _mutual_information(joint: dict[tuple[int, int], float]) -> float:
    px = {x: joint[(x, 0)] + joint[(x, 1)] for x in (0, 1)}
    py = {y: joint[(0, y)] + joint[(1, y)] for y in (0, 1)}
    mi = 0.0
    for (x, y), pxy in joint.items():
        if pxy > 0 and px[x] > 0 and py[y] > 0:
            mi += pxy * math.log2(pxy / (px[x] * py[y]))
    return mi


def _relation(joint: dict[tuple[int, int], float]) -> str:
    """Read the logical relation off a within-A_e 2x2 joint table."""
    p00, p01, p10, p11 = joint[(0, 0)], joint[(0, 1)], joint[(1, 0)], joint[(1, 1)]
    if p00 < ZERO_CELL and p11 >= ZERO_CELL:
        return "disjunction"          # (0,0) absent: at least one ON
    if p11 < ZERO_CELL and p00 >= ZERO_CELL:
        return "mutual_exclusion"     # (1,1) absent: not both ON
    if p01 < ZERO_CELL and p10 < ZERO_CELL:
        return "equivalence"          # off-diagonal absent: always equal
    if p00 < ZERO_CELL and p11 < ZERO_CELL:
        return "anti_equivalence"     # diagonal absent: always opposite
    return "coupled"


def mechanism_equivalence_structure(
    accepted_rows: list[dict],
    switches,
    *,
    pin_low: float = PIN_LOW,
    pin_high: float = PIN_HIGH,
    edge_mi: float = EDGE_MI,
) -> EquivalenceStructure:
    """Recover the mechanism equivalence structure from an admissible region.

    Parameters
    ----------
    accepted_rows:
        Accepted (theta, s) rows from A_e; each must expose the switch states as
        truthy/falsy values under the switch ``.name`` keys.
    switches:
        Sequence of switch objects (anything with a ``.name`` attribute).
    pin_low, pin_high:
        CA_j thresholds for calling a switch pinned OFF / ON.
    edge_mi:
        Minimum mutual information (bits) for a switch pair to be a confounding
        edge.

    Returns
    -------
    EquivalenceStructure
    """
    names = [s.name for s in switches]
    n = len(accepted_rows)
    K = len(names)
    if n == 0:
        return EquivalenceStructure(
            n_accepted=0, ca_j={s: float("nan") for s in names},
            pinned_on=[], pinned_off=[], free=list(names), edges=[],
            n_admissible_configs=0, n_total_configs=2 ** K,
        )

    cols = {s: _column(accepted_rows, s) for s in names}
    ca_j = {s: sum(cols[s]) / n for s in names}

    pinned_on = [s for s in names if ca_j[s] >= pin_high]
    pinned_off = [s for s in names if ca_j[s] <= pin_low]
    free = [s for s in names if pin_low < ca_j[s] < pin_high]

    edges: list[ConfoundingEdge] = []
    for a, b in combinations(names, 2):
        joint = _joint(cols[a], cols[b])
        mi = _mutual_information(joint)
        if mi >= edge_mi:
            edges.append(ConfoundingEdge(
                a=a, b=b, phi=_phi(cols[a], cols[b]),
                mutual_information=mi, relation=_relation(joint), joint=joint,
            ))
    edges.sort(key=lambda e: -e.mutual_information)

    # substitutable groups: connected components of the disjunction edges
    adj: dict[str, set[str]] = {s: set() for s in names}
    for e in edges:
        if e.relation == "disjunction":
            adj[e.a].add(e.b)
            adj[e.b].add(e.a)
    seen: set[str] = set()
    groups: list[list[str]] = []
    for s in names:
        if s in seen or not adj[s]:
            continue
        stack, comp = [s], []
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            comp.append(u)
            stack.extend(adj[u] - seen)
        if len(comp) > 1:
            groups.append(sorted(comp))

    n_configs = len(Counter(tuple(cols[s][i] for s in names) for i in range(n)))

    return EquivalenceStructure(
        n_accepted=n, ca_j=ca_j,
        pinned_on=pinned_on, pinned_off=pinned_off, free=free,
        edges=edges, n_admissible_configs=n_configs, n_total_configs=2 ** K,
        substitutable_groups=groups,
    )
