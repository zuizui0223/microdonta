"""Internal, finite-pool limitations report using MROD's existing target API.

Run from the repository root: python -m examples.target_limitation_report
The printed demonstration is synthetic, not evidence about a natural population.
No new selection policy or cross-repository runtime dependency is introduced.
"""
from __future__ import annotations

from itertools import product
import json
import math
from typing import Sequence

from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.sequential_observation import filter_by_outcome
from causal_model.target_observation_value import (
    target_entropy_bits,
    target_observation_information_value,
)


def _image(rows: Sequence[dict], columns: tuple[str, ...]) -> list[tuple]:
    # Target validation is performed by the production API before this helper.
    return list(dict.fromkeys(tuple(row[c] for c in columns) for row in rows))


def build_target_report(
    accepted_rows: Sequence[dict],
    candidates: Sequence[CandidateObservation],
    *,
    target_columns: Sequence[str],
    information_tolerance: float = 1e-12,
) -> dict:
    """Report current target disagreement and candidate-specific outcome branches.

    All rows have equal positive mass. Identification/repair are certified only
    over these represented rows, not an unenumerated feasible-world domain.
    The tolerance affects information ranking, never target-image cardinality.
    Costs, acquisition order and joint/sequence feasibility are not optimized.
    """
    if not math.isfinite(information_tolerance) or information_tolerance < 0:
        raise ValueError("information_tolerance must be finite and non-negative")
    rows = list(accepted_rows)
    current_h = target_entropy_bits(rows, target_columns)
    columns = tuple(target_columns)
    candidate_list = list(candidates)
    if len({c.name for c in candidate_list}) != len(candidate_list):
        raise ValueError("candidate names must be unique")
    for candidate in candidate_list:
        names = [outcome.name for outcome in candidate.outcomes or []]
        if len(set(names)) != len(names):
            raise ValueError("outcome names must be unique within a candidate")

    image = _image(rows, columns)
    resolved = len(image) == 1
    witness = None
    if not resolved:
        first = tuple(rows[0][c] for c in columns)
        other = next(i for i, row in enumerate(rows) if tuple(row[c] for c in columns) != first)
        witness = {
            "row_indices": [0, other],
            "target_values": [first, tuple(rows[other][c] for c in columns)],
            "scope": "disagreement_in_current_pool_not_proof_of_equal_sampling_laws",
        }

    values = target_observation_information_value(
        rows, candidate_list, target_columns=columns
    )
    by_name = {value.candidate: value for value in values}
    candidate_reports = []
    for candidate in candidate_list:
        value = by_name[candidate.name]
        record = {
            "candidate": candidate.name,
            "estimable": value.estimable,
            "partition_verified_in_pool": value.partition_verified,
            "reason": value.reason,
            "information_bits": value.mutual_information_bits,
            "expected_remaining_target_entropy_bits": None,
            "complete_repair_in_pool": None,
            "outcomes": [],
        }
        if value.estimable:
            residual = 0.0
            complete = True
            for outcome in candidate.outcomes:
                sub = filter_by_outcome(rows, outcome.extra_pattern_rows)
                probability = len(sub) / len(rows)
                sub_image = _image(sub, columns)
                sub_h = target_entropy_bits(sub, columns) if sub else None
                branch_resolved = len(sub_image) == 1 if sub else None
                record["outcomes"].append({
                    "outcome": outcome.name,
                    "probability": probability,
                    "n_rows": len(sub),
                    "target_values": sub_image,
                    "target_entropy_bits": sub_h,
                    "target_identified_in_pool": branch_resolved,
                })
                if sub:
                    residual += probability * sub_h
                    complete = complete and branch_resolved
            if not math.isclose(current_h - residual, value.mutual_information_bits, abs_tol=1e-10):
                raise RuntimeError("target information and explicit outcome branches disagree")
            record["expected_remaining_target_entropy_bits"] = residual
            record["complete_repair_in_pool"] = complete
        candidate_reports.append(record)

    estimable = [r for r in candidate_reports if r["estimable"]]
    missing = [r["candidate"] for r in candidate_reports if not r["estimable"]]
    coverage = (
        "empty_candidate_set" if not candidate_list else
        "complete" if not missing else "partial" if estimable else "none"
    )
    positive = [r for r in estimable if r["information_bits"] > information_tolerance]
    best = []
    if positive:
        highest = max(r["information_bits"] for r in positive)
        best = sorted(r["candidate"] for r in positive
                      if highest - r["information_bits"] <= information_tolerance)
    if resolved:
        action = "report_target_resolution_without_full_mechanism_claim"
    elif not candidate_list:
        action = "declare_candidate_observations"
    elif not estimable:
        action = "build_candidate_predictive_models"
    elif best:
        action = ("provisional_selection_and_complete_predictions" if missing
                  else "collect_best_verified_singleton")
    elif missing:
        action = "complete_predictions_before_one_step_stop"
    else:
        action = "audit_joint_information_before_changing_vocabulary"

    return {
        "scope": "stored_finite_uniform_pool_only",
        "feasible_domain_exhaustiveness": "not_certified",
        "target_columns": columns,
        "n_rows": len(rows),
        "target_values": image,
        "target_entropy_bits": current_h,
        "target_identified_in_pool": resolved,
        "unresolved_witness": witness,
        "predictive_coverage": coverage,
        "nonestimable_candidates": missing,
        "best_positive_candidates": best,
        "recommendation_scope": "estimable_subset_only" if missing else "declared_candidates_only",
        "one_step_stop_within_tolerance": bool(not resolved and coverage == "complete" and not positive),
        "information_tolerance_bits": information_tolerance,
        "sequence_information_limit": None,
        "next_action": action,
        "candidates": candidate_reports,
    }


def _candidate(name: str, variable: str, labels: Sequence[int]) -> CandidateObservation:
    return CandidateObservation(
        name=name,
        description="Controlled finite-world measurement, not empirical calibration",
        target_switches=[],
        rationale="Declared outcomes partition the same synthetic current pool",
        outcomes=[CandidateOutcome(
            name=str(label), description=str(label), prior_probability=1 / len(labels),
            extra_pattern_rows=[{
                "type": "absolute_summary", "population": "pop", "variable": variable,
                "observed_value": str(label), "scale": "0.01",
            }],
        ) for label in labels],
    )


def build_demo() -> dict:
    """Three explanatory programs, four submechanism states inside each program."""
    rows = []
    for code, (program, p, a) in enumerate((
        ("pollination_only", 1, 0), ("abiotic_only", 0, 1), ("combined", 1, 1),
    )):
        for u1, u2 in product((0, 1), repeat=2):
            rows.append({
                "program": program, "P": p, "A": a, "U1": u1, "U2": u2,
                "pop_contact": p, "pop_physiology": a,
                "pop_deep": 2 * u1 + u2, "pop_joint": code,
            })
    contact = _candidate("contact_channel", "contact", (0, 1))
    physiology = _candidate("physiology_channel", "physiology", (0, 1))
    deep = _candidate("deep_submechanism", "deep", (0, 1, 2, 3))
    joint = _candidate("joint_channel_bundle", "joint", (0, 1, 2))
    unmodelled = CandidateObservation(
        name="unmodelled_followup", description="No prospective prediction supplied",
        target_switches=[], rationale="Coverage remains explicitly incomplete", outcomes=[],
    )
    branches = {}
    for outcome in contact.outcomes:
        sub = filter_by_outcome(rows, outcome.extra_pattern_rows)
        branches[outcome.name] = build_target_report(
            sub, [physiology, deep], target_columns=["program"]
        )
    return {
        "evidence_role": "synthetic_controlled_example_not_field_evidence",
        "assumptions": (
            "12 equally weighted model worlds; idealized deterministic channel predictions; "
            "same predeclared program target; no causal, evolutionary or cost-optimality claim"
        ),
        "current": build_target_report(rows, [contact, physiology, deep, unmodelled], target_columns=["program"]),
        "conditional_contact_branches": branches,
        "explicit_joint_bundle": build_target_report(rows, [joint], target_columns=["program"]),
    }


if __name__ == "__main__":
    print(json.dumps(build_demo(), indent=2, allow_nan=False))
