"""Post-frozen comparator for the G2 controlled selection family.

This module does **not** modify or reinterpret the frozen G2 protocol. G2 remains
exactly the preregistered comparison between information-guided sequential design
(`rach_seq`) and uniform random order. The purpose here is narrower: test whether
G2's favourable guided-vs-random result requires adaptive *recomputation* or can
already be matched by a nonadaptive information policy that ranks candidates
once at the initial admissible region.

The supplemental policy is:

``static_initial_information``
    Compute each candidate's current `sequential_candidate_value` once at the
    initial A_epsilon, sort candidates by decreasing value (deterministic name
    tie-break), discard candidates whose initial value is non-positive, and then
    follow that fixed order without recomputing scores after observed outcomes.

All policies are evaluated on the same generated systems, accepted rows, hidden
truths, candidate vocabulary and outcome overrides. This is a post-frozen
supplemental analysis and must never be written back into
`g2_frozen_benchmark_protocol.json` or represented as preregistered G2.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from causal_model.causal_admissibility import causal_resolvability
from causal_model.generality_sweep import (
    SystemRecord,
    SweepResult,
    _abc_accept,
    _candidates_for_system,
    _make_random_system,
    _outcome_by_name,
    _run_rach_policy,
    _run_random_order,
    _sample_driver_coefficients,
    _summarize,
    _truth_outcome_overrides,
    _truth_retained,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure
from causal_model.sequential_observation import filter_by_outcome, sequential_candidate_value

ROOT = Path(__file__).resolve().parents[1]
FROZEN_PROTOCOL = ROOT / "paper" / "g2_frozen_benchmark_protocol.json"
SUPPLEMENT_ID = "mrod-g2-post-frozen-static-information-v1"
POLICIES = ("rach_seq", "static_initial_information", "random_order")


@dataclass(frozen=True)
class PreparedSystem:
    K: int
    n_confounds: int
    switches: tuple
    drivers: tuple
    truth_driver: tuple
    driver_coeffs: tuple[float, float]
    accepted: tuple[dict, ...]
    candidates: tuple
    outcome_overrides: dict[str, str]
    sequence_seed: int
    n_distractors: int


@dataclass(frozen=True)
class AggregateRow:
    policy: str
    budget: int
    n_systems: int
    frac_converged: float
    mean_frac_resolved: float
    mean_steps: float
    mean_distractors_selected: float
    false_exclusion_rate: float


def _prepare_seed_systems(
    *,
    n_systems: int,
    seed: int,
    n_attempts: int,
    K_choices: tuple[int, ...],
    confound_choices: tuple[int, ...],
    min_sub_size: int,
    n_distractors: int,
) -> list[PreparedSystem]:
    """Generate each system once so all policies/budgets share the same carrier."""
    master = random.Random(seed)
    prepared: list[PreparedSystem] = []
    for _ in range(n_systems):
        sys_rng = random.Random(master.randrange(1 << 30))
        K = sys_rng.choice(K_choices)
        n_confounds = min(sys_rng.choice(confound_choices), K // 2)
        switches, drivers, truth_driver = _make_random_system(sys_rng, K, n_confounds)
        driver_coeffs = _sample_driver_coefficients(sys_rng)
        distractor_truth = [bool(sys_rng.getrandbits(1)) for _ in range(n_distractors)]
        accepted = _abc_accept(
            sys_rng,
            switches,
            drivers,
            n_attempts,
            driver_coeffs=driver_coeffs,
            n_distractors=n_distractors,
        )
        if len(accepted) < min_sub_size:
            continue
        candidates = _candidates_for_system(
            drivers,
            accepted,
            driver_coeffs=driver_coeffs,
            n_distractors=n_distractors,
        )
        overrides = _truth_outcome_overrides(
            drivers,
            truth_driver,
            distractor_truth=distractor_truth,
        )
        prepared.append(
            PreparedSystem(
                K=K,
                n_confounds=n_confounds,
                switches=tuple(switches),
                drivers=tuple(drivers),
                truth_driver=tuple(truth_driver),
                driver_coeffs=driver_coeffs,
                accepted=tuple(accepted),
                candidates=tuple(candidates),
                outcome_overrides=overrides,
                sequence_seed=sys_rng.randrange(1 << 30),
                n_distractors=n_distractors,
            )
        )
    return prepared


def _run_static_initial_information(
    prepared: PreparedSystem,
    *,
    budget: int,
    min_sub_size: int,
):
    """Follow one initial information ranking without branchwise recomputation."""
    current_rows = list(prepared.accepted)
    switches = list(prepared.switches)
    candidates = list(prepared.candidates)
    initial_structure = mechanism_equivalence_structure(current_rows, switches)
    current_structure = initial_structure

    ranked: list[tuple[float, str, object]] = []
    for candidate in candidates:
        score, _ = sequential_candidate_value(
            candidate,
            current_rows,
            switches,
            current_structure,
            min_sub_size=min_sub_size,
        )
        ranked.append((float(score), candidate.name, candidate))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    observations: list[str] = []
    for score, _, candidate in ranked:
        if len(observations) >= budget or not current_structure.edges:
            break
        # This is a deliberately strong nonadaptive comparator: it does not
        # spend effort on candidates judged mechanism-uninformative at baseline.
        if score <= 0.0:
            break
        outcome_name = prepared.outcome_overrides.get(candidate.name)
        if outcome_name is None:
            raise RuntimeError(
                f"supplement requires a pre-generated hidden outcome for {candidate.name!r}"
            )
        outcome = _outcome_by_name(candidate, outcome_name)
        filtered = filter_by_outcome(current_rows, outcome.extra_pattern_rows)
        observations.append(candidate.name)
        current_rows = filtered
        current_structure = mechanism_equivalence_structure(current_rows, switches)
        if len(filtered) < min_sub_size:
            break

    initial_ids = {(edge.a, edge.b) for edge in initial_structure.edges}
    final_ids = {(edge.a, edge.b) for edge in current_structure.edges}
    final_R = causal_resolvability(current_rows, switches) if current_rows else float("nan")

    # Match the minimal attribute surface consumed below by using a tiny object.
    class Outcome:
        pass

    out = Outcome()
    out.final_rows = current_rows
    out.n_resolved = len(initial_ids - final_ids)
    out.n_unresolved = len(current_structure.edges)
    out.converged = not bool(current_structure.edges)
    out.steps_taken = len(observations)
    out.R_final = final_R
    out.observations_taken = observations
    return out


def _record_for_policy(
    prepared: PreparedSystem,
    *,
    policy: str,
    budget: int,
    min_sub_size: int,
) -> SystemRecord:
    accepted = list(prepared.accepted)
    switches = list(prepared.switches)
    candidates = list(prepared.candidates)
    initial = mechanism_equivalence_structure(accepted, switches)
    R0 = causal_resolvability(accepted, switches)

    if policy == "rach_seq":
        outcome = _run_rach_policy(
            accepted,
            switches,
            candidates,
            budget=budget,
            min_sub_size=min_sub_size,
            seed=prepared.sequence_seed,
            outcome_overrides=prepared.outcome_overrides,
        )
    elif policy == "random_order":
        outcome = _run_random_order(
            accepted,
            switches,
            candidates,
            budget=budget,
            min_sub_size=min_sub_size,
            seed=prepared.sequence_seed,
            outcome_overrides=prepared.outcome_overrides,
        )
    elif policy == "static_initial_information":
        outcome = _run_static_initial_information(
            prepared,
            budget=budget,
            min_sub_size=min_sub_size,
        )
    else:
        raise ValueError(f"unknown supplemental policy: {policy!r}")

    distractors_selected = sum(
        name.startswith("measure_decoy") for name in outcome.observations_taken
    )
    return SystemRecord(
        K=prepared.K,
        n_confounds=prepared.n_confounds,
        n_initial_edges=len(initial.edges),
        n_resolved=outcome.n_resolved,
        n_unresolved=outcome.n_unresolved,
        converged=outcome.converged,
        steps_taken=outcome.steps_taken,
        R0=round(R0, 4),
        R_final=(
            round(outcome.R_final, 4)
            if math.isfinite(outcome.R_final)
            else outcome.R_final
        ),
        truth_retained=_truth_retained(
            outcome.final_rows,
            list(prepared.drivers),
            list(prepared.truth_driver),
        ),
        truth_peek_free=True,
        driver_coeff_a=prepared.driver_coeffs[0],
        driver_coeff_b=prepared.driver_coeffs[1],
        policy=policy,
        n_distractors=prepared.n_distractors,
        distractors_selected=distractors_selected,
    )


def run_supplement(
    *,
    seeds: Iterable[int],
    budgets: Iterable[int],
    n_systems_per_seed: int,
    n_attempts: int,
    K_choices: tuple[int, ...],
    confound_choices: tuple[int, ...],
    min_sub_size: int,
    n_distractors: int,
) -> dict:
    seeds = tuple(int(x) for x in seeds)
    budgets = tuple(int(x) for x in budgets)
    per_seed: list[dict] = []

    for seed in seeds:
        prepared = _prepare_seed_systems(
            n_systems=n_systems_per_seed,
            seed=seed,
            n_attempts=n_attempts,
            K_choices=K_choices,
            confound_choices=confound_choices,
            min_sub_size=min_sub_size,
            n_distractors=n_distractors,
        )
        for policy in POLICIES:
            for budget in budgets:
                result = SweepResult(n_systems=n_systems_per_seed, policy=policy)
                result.records = [
                    _record_for_policy(
                        system,
                        policy=policy,
                        budget=budget,
                        min_sub_size=min_sub_size,
                    )
                    for system in prepared
                ]
                _summarize(result)
                per_seed.append(
                    {
                        "seed": seed,
                        "policy": policy,
                        "budget": budget,
                        "n_systems": len(result.records),
                        "frac_converged": result.frac_converged,
                        "mean_frac_resolved": result.mean_frac_resolved,
                        "mean_steps": result.mean_steps,
                        "mean_distractors_selected": result.mean_distractors_selected,
                        "false_exclusion_rate": result.false_exclusion_rate,
                    }
                )

    aggregate: list[dict] = []
    metrics = (
        "frac_converged",
        "mean_frac_resolved",
        "mean_steps",
        "mean_distractors_selected",
        "false_exclusion_rate",
    )
    for policy in POLICIES:
        for budget in budgets:
            rows = [
                row for row in per_seed
                if row["policy"] == policy and row["budget"] == budget
            ]
            out = {
                "policy": policy,
                "budget": budget,
                "n_seeds": len(rows),
                "total_systems": sum(row["n_systems"] for row in rows),
            }
            for metric in metrics:
                values = [float(row[metric]) for row in rows]
                out[f"{metric}_mean"] = statistics.mean(values)
                out[f"{metric}_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0
            aggregate.append(out)

    return {
        "supplement_id": SUPPLEMENT_ID,
        "status": "post_frozen_not_part_of_preregistered_g2",
        "policies": list(POLICIES),
        "seeds": list(seeds),
        "budgets": list(budgets),
        "n_systems_per_seed_requested": n_systems_per_seed,
        "per_seed": per_seed,
        "aggregate": aggregate,
    }


def run_from_frozen_protocol() -> dict:
    protocol = json.loads(FROZEN_PROTOCOL.read_text(encoding="utf-8"))
    sweep = protocol["sweep"]
    return run_supplement(
        seeds=sweep["seeds"],
        budgets=sweep["budgets"],
        n_systems_per_seed=int(sweep["n_systems_per_seed"]),
        n_attempts=int(sweep["n_attempts"]),
        K_choices=tuple(int(x) for x in sweep["K_choices"]),
        confound_choices=tuple(int(x) for x in sweep["confound_choices"]),
        min_sub_size=int(sweep["min_sub_size"]),
        n_distractors=int(protocol["generator"]["distractor_candidates"]["count"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a small deterministic subset rather than all frozen seeds/systems.",
    )
    args = parser.parse_args()

    if args.smoke:
        payload = run_supplement(
            seeds=(101, 202),
            budgets=(0, 1, 2, 4),
            n_systems_per_seed=30,
            n_attempts=500,
            K_choices=(4, 5, 6),
            confound_choices=(1, 2),
            min_sub_size=8,
            n_distractors=2,
        )
    else:
        payload = run_from_frozen_protocol()

    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
