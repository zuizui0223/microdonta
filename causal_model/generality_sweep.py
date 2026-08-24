"""Truth-peek-free generality benchmark for RACH-SEQ.

Candidate observations are constructed only from the current admissible region.
The hidden benchmark truth is used *after* a candidate has been ranked, solely to
materialise the realised observation through ``outcome_overrides``.

That separation is essential: a benchmark that inserts the true observation into
the candidate distribution before ranking would measure an oracle-assisted
procedure rather than RACH-SEQ.
"""
from __future__ import annotations

import argparse
import csv
import random
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from causal_model.causal_admissibility import (
    CandidateObservation,
    CandidateOutcome,
    causal_resolvability,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure
from causal_model.rach_seq import filter_by_outcome, rach_seq


# The coefficient ratio is chosen so the three quantitative outcome bands
# (driver A only, driver B only, both on) remain separated for theta in [0.8, 1.2].
_DRIVER_COEFFS = (0.35, 0.60)
_THETA_LO, _THETA_HI = 0.8, 1.2
_SLOPE_TOL = 0.05


class _SW:
    """Minimal switch object; the inference layer needs only ``.name``."""

    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name


@dataclass
class SystemRecord:
    """RACH-SEQ outcome for one random system."""

    K: int
    n_confounds: int
    n_initial_edges: int
    n_resolved: int
    n_unresolved: int
    converged: bool
    steps_taken: int
    R0: float
    R_final: float
    truth_retained: bool = True
    truth_peek_free: bool = True

    @property
    def frac_resolved(self) -> float:
        if self.n_initial_edges == 0:
            return 1.0
        return self.n_resolved / self.n_initial_edges


@dataclass
class SweepResult:
    n_systems: int
    records: list[SystemRecord] = field(default_factory=list)
    frac_converged: float = float("nan")
    mean_frac_resolved: float = float("nan")
    median_frac_resolved: float = float("nan")
    mean_R0: float = float("nan")
    mean_R_final: float = float("nan")
    mean_steps: float = float("nan")
    systems_with_edges: int = 0
    false_exclusion_rate: float = float("nan")


@dataclass(frozen=True)
class BudgetSummary:
    budget: int
    n_systems: int
    systems_with_edges: int
    frac_converged: float
    mean_frac_resolved: float
    mean_steps: float
    false_exclusion_rate: float


def _make_random_system(rng: random.Random, K: int, n_confounds: int):
    """Build one random confounded system with a hidden one-driver truth per trait."""
    names = [f"s{i}" for i in range(K)]
    switches = [_SW(n) for n in names]
    pool = names[:]
    rng.shuffle(pool)
    drivers_per_trait: list[tuple[str, str]] = []
    for t in range(n_confounds):
        drivers_per_trait.append((pool[2 * t], pool[2 * t + 1]))
    truth_driver = [rng.choice(pair) for pair in drivers_per_trait]
    return switches, drivers_per_trait, truth_driver


def _abc_accept(rng: random.Random, switches, drivers_per_trait, n_attempts: int):
    """Generate A_epsilon from ordinal-positive observations only."""
    names = [sw.name for sw in switches]
    accepted: list[dict] = []
    for _ in range(n_attempts):
        state = {name: (rng.random() < 0.5) for name in names}
        theta = rng.uniform(_THETA_LO, _THETA_HI)
        magnitudes: list[float] = []
        ok = True
        for a, b in drivers_per_trait:
            slope = theta * (
                _DRIVER_COEFFS[0] * int(state[a])
                + _DRIVER_COEFFS[1] * int(state[b])
            )
            magnitudes.append(slope)
            if slope <= _SLOPE_TOL:
                ok = False
                break
        if not ok:
            continue
        row = dict(state)
        row["theta"] = theta
        for t, magnitude in enumerate(magnitudes):
            row[f"trait{t}_mag"] = round(magnitude, 4)
        accepted.append(row)
    return accepted


def _truth_magnitude(driver_name: str, pair: tuple[str, str]) -> float:
    """Magnitude at theta=1 when exactly the hidden true driver is on."""
    return _DRIVER_COEFFS[0] if driver_name == pair[0] else _DRIVER_COEFFS[1]


def _mode_name(a_on: bool, b_on: bool) -> str:
    if a_on and not b_on:
        return "driver_a_only"
    if b_on and not a_on:
        return "driver_b_only"
    if a_on and b_on:
        return "both_on"
    return "neither_on"


def _mode_coefficient(mode: str) -> float:
    if mode == "driver_a_only":
        return _DRIVER_COEFFS[0]
    if mode == "driver_b_only":
        return _DRIVER_COEFFS[1]
    if mode == "both_on":
        return sum(_DRIVER_COEFFS)
    raise ValueError(f"unsupported mode: {mode}")


def _absolute_band_pattern(trait_index: int, mode: str) -> dict:
    """Return an absolute-summary pattern covering that mode's full theta band."""
    coeff = _mode_coefficient(mode)
    lower = coeff * _THETA_LO
    upper = coeff * _THETA_HI
    centre = (lower + upper) / 2.0
    # rach_seq interprets absolute_summary as |sim-observed| <= 2*scale.
    scale = (upper - lower) / 4.0 + 1e-6
    return {
        "type": "absolute_summary",
        "variable": "mag",
        "population": f"trait{trait_index}",
        "observed_value": f"{centre:.8f}",
        "scale": f"{scale:.8f}",
    }


def _candidates_for_system(drivers_per_trait, accepted_rows: list[dict]):
    """Construct candidate outcome distributions from A_epsilon, never from truth.

    For each trait, the predictive probabilities of ``driver_a_only``,
    ``driver_b_only`` and ``both_on`` are estimated from their frequencies in the
    current admissible region. The hidden data-generating driver is not an input.
    """
    if not accepted_rows:
        return []
    candidates: list[CandidateObservation] = []
    for t, pair in enumerate(drivers_per_trait):
        a, b = pair
        counts = {"driver_a_only": 0, "driver_b_only": 0, "both_on": 0}
        for row in accepted_rows:
            mode = _mode_name(bool(row.get(a)), bool(row.get(b)))
            if mode in counts:
                counts[mode] += 1
        total = sum(counts.values())
        if total == 0:
            continue
        outcomes = [
            CandidateOutcome(
                name=mode,
                description=f"Trait {t} quantitative magnitude falls in the {mode} band.",
                prior_probability=counts[mode] / total,
                extra_pattern_rows=[_absolute_band_pattern(t, mode)],
            )
            for mode in ("driver_a_only", "driver_b_only", "both_on")
            if counts[mode] > 0
        ]
        candidates.append(CandidateObservation(
            name=f"measure_trait{t}_magnitude",
            description=f"Measure the quantitative magnitude of trait {t}.",
            target_switches=list(pair),
            rationale=(
                f"The admissible-region predictive distribution separates which of {pair} "
                "drives the ordinal-positive trait without using benchmark truth."
            ),
            pattern_type="absolute_summary",
            outcomes=outcomes,
        ))
    return candidates


def _truth_outcome_overrides(drivers_per_trait, truth_driver) -> dict[str, str]:
    """Materialise hidden truth only after ranking, as the realised observation."""
    overrides: dict[str, str] = {}
    for t, (pair, true_driver) in enumerate(zip(drivers_per_trait, truth_driver)):
        overrides[f"measure_trait{t}_magnitude"] = (
            "driver_a_only" if true_driver == pair[0] else "driver_b_only"
        )
    return overrides


def _replay_final_rows(accepted_rows, candidates, seq) -> list[dict]:
    rows = list(accepted_rows)
    by_name = {candidate.name: candidate for candidate in candidates}
    for step in seq.steps[1:]:
        if not step.observation_taken or not step.outcome_observed:
            continue
        candidate = by_name[step.observation_taken]
        outcome = next(o for o in candidate.outcomes if o.name == step.outcome_observed)
        rows = filter_by_outcome(rows, outcome.extra_pattern_rows)
    return rows


def _truth_retained(rows, drivers_per_trait, truth_driver) -> bool:
    """Whether at least one surviving row contains every hidden one-driver mode."""
    for row in rows:
        ok = True
        for pair, true_driver in zip(drivers_per_trait, truth_driver):
            other = pair[1] if true_driver == pair[0] else pair[0]
            if not bool(row.get(true_driver)) or bool(row.get(other)):
                ok = False
                break
        if ok:
            return True
    return False


def run_generality_sweep(
    n_systems: int = 200,
    seed: int = 0,
    *,
    n_attempts: int = 1500,
    K_choices: tuple[int, ...] = (4, 5, 6),
    confound_choices: tuple[int, ...] = (1, 2),
    budget: int = 4,
    min_sub_size: int = 8,
) -> SweepResult:
    """Run a truth-peek-free RACH-SEQ sweep over random confounded systems."""
    master = random.Random(seed)
    result = SweepResult(n_systems=n_systems)

    for _ in range(n_systems):
        sys_rng = random.Random(master.randrange(1 << 30))
        K = sys_rng.choice(K_choices)
        n_confounds = min(sys_rng.choice(confound_choices), K // 2)
        switches, drivers, truth_driver = _make_random_system(sys_rng, K, n_confounds)
        accepted = _abc_accept(sys_rng, switches, drivers, n_attempts)
        if len(accepted) < min_sub_size:
            continue

        initial = mechanism_equivalence_structure(accepted, switches)
        R0 = causal_resolvability(accepted, switches)
        candidates = _candidates_for_system(drivers, accepted)
        overrides = _truth_outcome_overrides(drivers, truth_driver)

        seq = rach_seq(
            accepted,
            switches,
            candidates,
            budget=budget,
            min_sub_size=min_sub_size,
            seed=sys_rng.randrange(1 << 30),
            outcome_overrides=overrides,
        )
        final_rows = _replay_final_rows(accepted, candidates, seq)

        result.records.append(SystemRecord(
            K=K,
            n_confounds=n_confounds,
            n_initial_edges=len(initial.edges),
            n_resolved=len(seq.edges_resolved),
            n_unresolved=len(seq.edges_unresolved),
            converged=seq.converged,
            steps_taken=len(seq.observations_taken),
            R0=round(R0, 4),
            R_final=round(seq.steps[-1].R, 4),
            truth_retained=_truth_retained(final_rows, drivers, truth_driver),
            truth_peek_free=True,
        ))

    _summarize(result)
    return result


def _summarize(result: SweepResult) -> None:
    records = result.records
    if not records:
        return
    with_edges = [record for record in records if record.n_initial_edges > 0]
    result.systems_with_edges = len(with_edges)
    base = with_edges or records
    result.frac_converged = sum(record.converged for record in base) / len(base)
    result.mean_frac_resolved = statistics.mean(record.frac_resolved for record in base)
    result.median_frac_resolved = statistics.median(record.frac_resolved for record in base)
    result.mean_R0 = statistics.mean(record.R0 for record in records)
    result.mean_R_final = statistics.mean(record.R_final for record in records)
    result.mean_steps = statistics.mean(record.steps_taken for record in base)
    result.false_exclusion_rate = (
        sum(not record.truth_retained for record in records) / len(records)
    )


def run_budget_sweep(
    budgets: Sequence[int] = (0, 1, 2, 3, 4),
    *,
    n_systems: int = 200,
    seed: int = 0,
    n_attempts: int = 1500,
    K_choices: tuple[int, ...] = (4, 5, 6),
    confound_choices: tuple[int, ...] = (1, 2),
    min_sub_size: int = 8,
) -> list[BudgetSummary]:
    """Evaluate observation efficiency and false exclusion across fixed budgets."""
    summaries: list[BudgetSummary] = []
    for budget in budgets:
        if budget < 0:
            raise ValueError("budgets must be non-negative")
        result = run_generality_sweep(
            n_systems=n_systems,
            seed=seed,
            n_attempts=n_attempts,
            K_choices=K_choices,
            confound_choices=confound_choices,
            budget=int(budget),
            min_sub_size=min_sub_size,
        )
        summaries.append(BudgetSummary(
            budget=int(budget),
            n_systems=len(result.records),
            systems_with_edges=result.systems_with_edges,
            frac_converged=result.frac_converged,
            mean_frac_resolved=result.mean_frac_resolved,
            mean_steps=result.mean_steps,
            false_exclusion_rate=result.false_exclusion_rate,
        ))
    return summaries


def save_budget_table(summaries: Sequence[BudgetSummary], path: str | Path) -> Path:
    """Write the frozen error-control / observation-budget table as CSV."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "budget", "n_systems", "systems_with_edges", "frac_converged",
        "mean_frac_resolved", "mean_steps", "false_exclusion_rate",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for summary in summaries:
            writer.writerow({field: getattr(summary, field) for field in fields})
    return output


def print_report(result: SweepResult) -> None:
    print("=" * 72)
    print("RACH-SEQ generality sweep — truth-peek-free random systems")
    print("=" * 72)
    print(f"systems run            : {len(result.records)} / {result.n_systems}")
    print(f"systems with >=1 edge  : {result.systems_with_edges}")
    if not result.records:
        print("no systems produced a usable admissible region")
        return
    print(f"fully converged        : {result.frac_converged * 100:.1f}%")
    print(f"edges resolved (mean)  : {result.mean_frac_resolved * 100:.1f}%")
    print(f"resolvability R        : {result.mean_R0:.3f} -> {result.mean_R_final:.3f}")
    print(f"observations taken     : {result.mean_steps:.2f}")
    print(f"false exclusion rate   : {result.false_exclusion_rate * 100:.2f}%")


def print_budget_table(summaries: Sequence[BudgetSummary]) -> None:
    print("budget  converged  resolved  mean_steps  false_exclusion")
    for summary in summaries:
        print(
            f"{summary.budget:>6d}  {summary.frac_converged:>9.3f}  "
            f"{summary.mean_frac_resolved:>8.3f}  {summary.mean_steps:>10.3f}  "
            f"{summary.false_exclusion_rate:>15.3f}"
        )


def make_figure(result: SweepResult, path: str) -> str | None:
    """Write a compact publication diagnostic without changing benchmark logic."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable — skipping figure")
        return None

    records = [r for r in result.records if r.n_initial_edges > 0]
    if not records:
        return None
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5.0, 4.0))
    ax.scatter([r.R0 for r in records], [r.R_final for r in records], s=16, alpha=0.5)
    lim = max([r.R0 for r in records] + [r.R_final for r in records] + [0.1]) * 1.05
    ax.plot([0, lim], [0, lim], "--", linewidth=1)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("R before")
    ax.set_ylabel("R after RACH-SEQ")
    ax.set_title("Truth-peek-free sequential resolvability")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return str(output)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Truth-peek-free RACH-SEQ generality benchmark."
    )
    parser.add_argument("--n-systems", type=int, default=200)
    parser.add_argument("--n-attempts", type=int, default=1500)
    parser.add_argument("--budget", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--figure", default="")
    parser.add_argument(
        "--budget-sweep",
        default="",
        help="Comma-separated budgets; when supplied, print the error-control table.",
    )
    parser.add_argument("--budget-table", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.budget_sweep:
        budgets = [int(value) for value in args.budget_sweep.split(",") if value.strip()]
        summaries = run_budget_sweep(
            budgets,
            n_systems=args.n_systems,
            seed=args.seed,
            n_attempts=args.n_attempts,
        )
        print_budget_table(summaries)
        if args.budget_table:
            print(f"budget table written: {save_budget_table(summaries, args.budget_table)}")
        return 0

    result = run_generality_sweep(
        n_systems=args.n_systems,
        seed=args.seed,
        n_attempts=args.n_attempts,
        budget=args.budget,
    )
    print_report(result)
    if args.figure:
        output = make_figure(result, args.figure)
        if output:
            print(f"figure written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
