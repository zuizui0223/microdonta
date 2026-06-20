"""Mechanism-structure discovery: infer the causal path from the pattern alone.

Every other entry point in this package takes a *hand-enumerated* set of
mechanism switches (guide_attracts_bombus, selfing_syndrome_active, ...). This
module removes that requirement. It asks the harder question the cline itself
poses:

    Fitness and cost (the selective economics) are not measurable; only the
    trait pattern along the cline is. WITHOUT assuming which mechanism is at
    work, can we randomly generate candidate causal structures and infer, from
    the pattern, which pathway is most likely — including indirect, mediated
    paths?

The move is to make the *mechanism itself* the random object. A "mechanism" is
a directed causal structure over a small vocabulary of variables:

    X            the cline driver (isolation / latitude / distance), exogenous
    Ma, Mb       latent, UNMEASURED mediators (e.g. pollinator loss, selfing
                 pressure) — the unobservable economics
    T1, T2       observed traits whose cline response IS measured (e.g. guide,
                 flower size)

The candidate edges among these (X→T1 direct, X→Ma→T1 mediated, ...) form the
hypothesis space. We do NOT pick which edges are real; we randomly switch each
edge on/off and assign each present edge a random sign and magnitude — this last
step marginalises over the unmeasurable fitness/cost economics. Forward
propagation gives each structure's predicted trait directions along the cline;
ABC keeps the structures whose predicted pattern matches the observed one. The
posterior over edges is then the support each causal path receives from the
pattern, computed with the existing RACH machinery (causal admissibility,
degeneracy, mechanism equivalence) applied to the edge space.

What it can and cannot do
-------------------------
It does NOT assume which mechanism is true. It DOES assume the variable set and
the allowed edges (the vocabulary) — a much weaker commitment than enumerating
named mechanisms. The expected and honest result is high *structural*
degeneracy: a direct path X→T1 and a mediated path X→Ma→T1 produce the same
cline and are observationally equivalent. RACH reports that equivalence rather
than hiding it, and identifies the measurement (the mediator's own cline
response) that would separate direct from mediated — exactly the Campanula
"is guide loss direct relaxed-selection or selfing-mediated?" question, now
*discovered* from random structures instead of hand-coded.

Usage
-----
    python -m causal_model.structure_discovery --figure outputs/mee/structure_discovery.png
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass, field

# Vocabulary: nodes in topological order (edges only go forward => acyclic).
_NODES = ("X", "Ma", "Mb", "T1", "T2")
_MEDIATORS = ("Ma", "Mb")
_TRAITS = ("T1", "T2")

# Candidate directed edges (the hypothesis space). parents listed per node.
_EDGES = (
    "X->Ma", "X->Mb", "X->T1", "X->T2",
    "Ma->Mb", "Ma->T1", "Ma->T2", "Mb->T1", "Mb->T2",
)
_PARENTS = {
    "Ma": [("X", "X->Ma")],
    "Mb": [("X", "X->Mb"), ("Ma", "Ma->Mb")],
    "T1": [("X", "X->T1"), ("Ma", "Ma->T1"), ("Mb", "Mb->T1")],
    "T2": [("X", "X->T2"), ("Ma", "Ma->T2"), ("Mb", "Mb->T2")],
}

_DIR_TOL = 0.05            # |effect| must exceed this to count as a direction
_EDGE_PRIOR = 0.5         # prior probability each edge is present


def _switches():
    from causal_model.switch_inference import BiologicalSwitch
    return [BiologicalSwitch(name=e, pathway_key=e, biological_question="", description="")
            for e in _EDGES]


def _propagate(present: dict[str, bool], weight: dict[str, float]) -> dict[str, float]:
    """Linear forward propagation of a unit cline increase X=+1 through the
    structure. v[T] is the net effect summed over all directed X→T paths."""
    v = {"X": 1.0}
    for node in _NODES[1:]:
        s = 0.0
        for parent, edge in _PARENTS[node]:
            if present[edge]:
                s += weight[edge] * v[parent]
        v[node] = s
    return v


def _abc_accept(observed: dict[str, int], n_attempts: int, seed: int) -> list[dict]:
    """Sample (structure, weights); accept those whose predicted trait
    directions match the observed cline pattern. Weights carry a random sign and
    magnitude, marginalising the unmeasurable fitness/cost economics."""
    rng = random.Random(seed)
    accepted = []
    for _ in range(n_attempts):
        present = {e: (rng.random() < _EDGE_PRIOR) for e in _EDGES}
        weight = {e: rng.choice((-1.0, 1.0)) * rng.uniform(0.5, 1.5) for e in _EDGES}
        v = _propagate(present, weight)
        # observed traits must match their measured direction; |effect| > tol
        ok = True
        for t, d in observed.items():
            if d == 0:
                continue
            if not (abs(v[t]) > _DIR_TOL and (1 if v[t] > 0 else -1) == d):
                ok = False
                break
        if not ok:
            continue
        row = {e: present[e] for e in _EDGES}
        for n in _NODES[1:]:
            row[f"v{n}"] = round(v[n], 4)
            row[f"dir_{n}"] = 0 if abs(v[n]) <= _DIR_TOL else (1 if v[n] > 0 else -1)
        accepted.append(row)
    return accepted


def _path_support(acc: list[dict], trait: str) -> dict[str, float]:
    """Posterior support for each route from X to ``trait``: direct vs mediated."""
    n = len(acc)
    if n == 0:
        return {}
    out = {}
    out["direct"] = sum(1 for r in acc if r[f"X->{trait}"]) / n
    for m in _MEDIATORS:
        # mediated via m: X reaches m and m reaches trait
        reaches_m = (lambda r, m=m: r[f"X->{m}"] or (m == "Mb" and r["X->Ma"] and r["Ma->Mb"]))
        out[f"via_{m}"] = sum(1 for r in acc if reaches_m(r) and r[f"{m}->{trait}"]) / n
    return out


@dataclass
class DiscoveryResult:
    observed: dict[str, int]
    n_accepted: int
    n_attempts: int
    edge_posterior: dict[str, float]       # P(edge present | pattern)
    D_structural: float                    # degeneracy over the edge space (bits)
    R_structural: float
    confounded_edges: list[str]            # human-readable confounded edge pairs
    path_support: dict[str, dict[str, float]]   # trait -> {direct, via_Ma, via_Mb}
    nov: list[tuple[str, float]]           # (mediator measured, structural D reduction)
    path_support_after: dict[str, dict[str, float]] = field(default_factory=dict)


def _structural_degeneracy(acc, switches):
    from causal_model.causal_admissibility import causal_degeneracy, causal_resolvability
    return (round(causal_degeneracy(acc, switches), 4),
            round(causal_resolvability(acc, switches), 4))


def _mediator_nov(acc, switches, mediator: str) -> float:
    """Expected structural-degeneracy reduction from measuring a mediator's own
    cline direction (preposterior EVSI over the edge space)."""
    from causal_model.causal_admissibility import causal_degeneracy
    n = len(acc)
    if n == 0:
        return 0.0
    D0 = causal_degeneracy(acc, switches)
    exp_D = 0.0
    for d in (-1, 0, 1):
        sub = [r for r in acc if r[f"dir_{mediator}"] == d]
        if not sub:
            continue
        exp_D += (len(sub) / n) * causal_degeneracy(sub, switches)
    return round(D0 - exp_D, 4)


def run_structure_discovery(observed: dict[str, int] | None = None,
                            n_attempts: int = 20000, seed: int = 1) -> DiscoveryResult:
    from causal_model.causal_admissibility import causal_admissibility
    from causal_model.mechanism_equivalence import mechanism_equivalence_structure

    # default observed cline pattern: both traits DECLINE along the cline
    observed = observed or {"T1": -1, "T2": -1}
    switches = _switches()
    acc = _abc_accept(observed, n_attempts, seed)

    ca = {r.switch_name: round(r.CA_j, 4) for r in causal_admissibility(acc, switches)}
    D, R = _structural_degeneracy(acc, switches)
    struct = mechanism_equivalence_structure(acc, switches)
    confounded = [e.describe() for e in struct.edges[:8]]

    paths = {t: _path_support(acc, t) for t in _TRAITS}

    # NOV: which mediator measurement most reduces structural degeneracy?
    nov = sorted(((m, _mediator_nov(acc, switches, m)) for m in _MEDIATORS),
                 key=lambda x: -x[1])

    res = DiscoveryResult(
        observed=observed, n_accepted=len(acc), n_attempts=n_attempts,
        edge_posterior=ca, D_structural=D, R_structural=R,
        confounded_edges=confounded, path_support=paths, nov=nov,
    )

    # demonstrate resolution: measure the top-NOV mediator's cline response.
    # If that mediator does NOT respond to the cline (dir == 0), every path
    # mediated through it is ruled out and the trait's decline must be direct
    # or routed elsewhere — separating direct from mediated.
    if nov and nov[0][1] > 0:
        top_m = nov[0][0]
        sub = [r for r in acc if r[f"dir_{top_m}"] == 0]   # mediator silent
        if len(sub) >= 10:
            res.path_support_after = {t: _path_support(sub, t) for t in _TRAITS}
    return res


def print_report(res: DiscoveryResult) -> None:
    print("=" * 72)
    print("Mechanism-structure discovery — infer the path from the pattern alone")
    print("=" * 72)
    obs = ", ".join(f"{t}{'↓' if d < 0 else '↑'}" for t, d in res.observed.items())
    print(f"observed cline pattern : {obs}")
    print(f"accepted structures    : {res.n_accepted} / {res.n_attempts}")
    print(f"structural degeneracy  : D = {res.D_structural} of {len(_EDGES)} bits  "
          f"(R = {res.R_structural})")
    print("-" * 72)
    print("edge posterior  P(edge present | pattern):")
    for e in _EDGES:
        bar = "█" * int(round(res.edge_posterior[e] * 20))
        print(f"   {e:9s} {res.edge_posterior[e]:.3f}  {bar}")
    print("-" * 72)
    print("path support to each observed trait (direct vs mediated):")
    for t, ps in res.path_support.items():
        parts = "   ".join(f"{k}={v:.2f}" for k, v in ps.items())
        print(f"   {t}: {parts}")
    print("   → direct and mediated routes are jointly supported: the cline alone")
    print("     cannot tell relaxed-selection (direct) from mediation. That is the")
    print("     structural degeneracy, made explicit.")
    print("-" * 72)
    print("NOV — expected structural-degeneracy reduction from measuring a mediator:")
    for m, val in res.nov:
        print(f"   measure {m} cline response: ΔD = {val:+.4f}")
    if res.path_support_after:
        top_m = res.nov[0][0]
        print(f"resolution — if {top_m} is silent (no cline response), paths through it drop:")
        for t, ps in res.path_support_after.items():
            parts = "   ".join(f"{k}={v:.2f}" for k, v in ps.items())
            print(f"   {t}: {parts}")


def make_figure(res: DiscoveryResult, path: str) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception:
        print("matplotlib unavailable — skipping figure.")
        return None
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

    # Panel A: edge posterior
    ax = axes[0]
    edges = list(_EDGES)
    vals = [res.edge_posterior[e] for e in edges]
    # colour direct X->T edges vs mediated edges
    colors = ["#1f77b4" if e.startswith("X->T") else
              ("#9aa0a6" if e.startswith("X->M") or "->M" in e else "#d62728")
              for e in edges]
    ax.barh(edges, vals, color=colors)
    ax.axvline(0.5, color="gray", ls="--", lw=1)
    ax.set_xlim(0, 1); ax.invert_yaxis()
    ax.set_xlabel("P(edge present | pattern)")
    ax.set_title(f"(A) Discovered edge posterior\nstructural D = {res.D_structural}/{len(_EDGES)} bits")

    # Panel B: path support for T1, before vs after measuring the mediator
    ax = axes[1]
    t = "T1"
    before = res.path_support[t]
    keys = list(before.keys())
    x = np.arange(len(keys)); w = 0.38
    b = [before[k] for k in keys]
    ax.bar(x - w/2, b, w, label="pattern only", color="#bbbbbb")
    if res.path_support_after:
        a = [res.path_support_after[t][k] for k in keys]
        ax.bar(x + w/2, a, w, label=f"+ {res.nov[0][0]} measured", color="#d62728")
    ax.set_xticks(x); ax.set_xticklabels(keys, fontsize=9)
    ax.set_ylim(0, 1); ax.set_ylabel(f"path support to {t}")
    ax.set_title("(B) Direct vs mediated paths\nconfounded, then separated by the mediator")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Mechanism-structure discovery from a cline pattern.")
    p.add_argument("--n-attempts", type=int, default=20000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--figure", default="")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    res = run_structure_discovery(n_attempts=args.n_attempts, seed=args.seed)
    print_report(res)
    if args.figure:
        out = make_figure(res, args.figure)
        if out:
            print(f"\nFigure written: {out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
