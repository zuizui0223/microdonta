"""Standalone RACH observation-design tracks for island pollination systems.

These tracks are owned by microdonta. They do not import, depend on, validate,
or extend any external manuscript or repository.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EmpiricalTrack:
    track_id: str
    title: str
    scientific_starting_point: str
    unresolved_empirical_claim: str
    rach_role: str
    required_gates: tuple[str, ...]
    derived_estimand: str | None
    forbidden_shortcuts: tuple[str, ...]
    completion_condition: str
    current_state: str


@dataclass(frozen=True)
class EmpiricalAssessment:
    track_id: str
    ready: bool
    passed_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]
    permitted_conclusion: str
    prohibited_conclusion: str


def default_empirical_tracks() -> tuple[EmpiricalTrack, ...]:
    return (
        EmpiricalTrack(
            track_id="signed_functional_starting_position",
            title="Signed functional starting position",
            scientific_starting_point=(
                "A lineage can occupy a signed position relative to a functional partner environment; "
                "the empirical question is whether that prespecified position predicts downstream response."
            ),
            unresolved_empirical_claim=(
                "A source-native signed plant position relative to the pollinator functional environment "
                "predicts the direction or magnitude of an island response."
            ),
            rach_role=(
                "Next observation separating a starting-state mechanism from downstream context, lineage "
                "identity, and other propagation filters; proxy calibration applies when needed."
            ),
            required_gates=(
                "predeclared_plant_matching_trait",
                "source_native_pollinator_functional_center",
                "matched_trait_units_and_comparison_unit",
                "outcome_blind_signed_position_formula",
                "downstream_reproductive_or_evolutionary_response",
                "sampling_hierarchy_and_uncertainty",
            ),
            derived_estimand="signed_position = plant_matching_trait - pollinator_functional_center",
            forbidden_shortcuts=(
                "use an unsigned matching score as if it encoded signed position",
                "impute pollinator trait from guild midpoint, family, body size, or syndrome",
                "choose the sign convention or functional center after inspecting the outcome",
                "equate an abstract functional coordinate with one named floral trait without a mapping gate",
            ),
            completion_condition=(
                "A prespecified empirical unit provides plant trait, pollinator functional center and "
                "downstream response on compatible scales, with signed mapping frozen before outcome inspection."
            ),
            current_state="blocked_for_direct_empirical_test",
        ),
        EmpiricalTrack(
            track_id="network_context_effective_service",
            title="Network context to effective service",
            scientific_starting_point=(
                "Local partner context may redistribute service among lineages; the empirical problem is to "
                "measure the service channel rather than infer it from network descriptors alone."
            ),
            unresolved_empirical_claim=(
                "A measured change in local partner context changes rate-weighted effective pollination "
                "service and downstream reproductive response in a real island system."
            ),
            rach_role=(
                "Channel-measurement and proxy-calibration problem: visitor abundance, identity, richness "
                "or degree is not effective service unless the conversion is calibrated."
            ),
            required_gates=(
                "matched_transition_or_context_unit",
                "repeated_local_context_support",
                "visitor_specific_rate",
                "visitor_specific_direct_effectiveness",
                "downstream_reproductive_outcome",
            ),
            derived_estimand="effective_service = sum_k(visitor_rate_k * direct_effectiveness_k)",
            forbidden_shortcuts=(
                "treat visitation frequency as effective service without effectiveness calibration",
                "treat visitor identity or richness as direct effectiveness",
                "transport effectiveness numerically across unmatched sites, years, or populations",
                "call any attenuation a unique network-buffer mechanism",
            ),
            completion_condition=(
                "The same prespecified hierarchy supplies visitor-specific rate, direct effectiveness, "
                "local context and reproductive outcome for a matched effective-service contrast."
            ),
            current_state="partial_empirical_bridges_only_no_mapping_ready_system",
        ),
        EmpiricalTrack(
            track_id="complete_service_dependency_response_bridge",
            title="Complete pollinator-change to service to dependency/assurance to response bridge",
            scientific_starting_point=(
                "Pollinator functional change, effective service, reproductive dependency or assurance, "
                "and downstream response are distinct causal links that should be measured separately."
            ),
            unresolved_empirical_claim=(
                "At least one island system links the complete causal chain on the same or prespecified "
                "compatible units."
            ),
            rach_role=(
                "RACH-SEQ observation package in which each measured link removes a different causal "
                "equivalence edge and missing links remain explicitly unresolved."
            ),
            required_gates=(
                "pollinator_functional_change",
                "effective_service_or_direct_pollen_function",
                "reproductive_dependency_or_autonomous_assurance",
                "downstream_floral_reproductive_or_evolutionary_response",
                "compatible_unit_linkage",
                "sampling_hierarchy_and_uncertainty",
                "source_provenance",
            ),
            derived_estimand=None,
            forbidden_shortcuts=(
                "infer dependency from floral syndrome or self-compatibility alone",
                "infer effective service from visitor occurrence or abundance alone",
                "splice unmatched studies without a prespecified transfer rule",
                "treat within-system replication as independent archipelago replication",
            ),
            completion_condition=(
                "One system supplies the causal links on compatible units with uncertainty and provenance; "
                "formal cross-system synthesis remains a separate gate."
            ),
            current_state="multiple_partial_bridges_zero_complete_bridge",
        ),
    )


def _track_map() -> dict[str, EmpiricalTrack]:
    return {track.track_id: track for track in default_empirical_tracks()}


def audit_empirical_track(track_id: str, observed_gates: Iterable[str]) -> EmpiricalAssessment:
    try:
        track = _track_map()[track_id]
    except KeyError as exc:
        raise ValueError(f"unknown empirical track: {track_id}") from exc

    observed = frozenset(observed_gates)
    passed = tuple(gate for gate in track.required_gates if gate in observed)
    missing = tuple(gate for gate in track.required_gates if gate not in observed)
    ready = not missing

    permitted = (
        "The observation bundle closes the declared structural gate for this track; any causal conclusion "
        "remains conditional on the comparison, measurement model and RACH admissible family."
        if ready
        else "Retain competing explanations and use the missing gates as the next-observation target."
    )
    prohibited = (
        "Missing gates may not be filled by visitor identity, syndrome labels, geography, unsigned matching, "
        "unmatched cross-study transport, or post-outcome remapping."
    )
    return EmpiricalAssessment(track_id, ready, passed, missing, permitted, prohibited)


def rank_empirical_tracks_by_missing_gates(
    observed_by_track: dict[str, Iterable[str]],
) -> list[EmpiricalAssessment]:
    assessments = [
        audit_empirical_track(track.track_id, observed_by_track.get(track.track_id, ()))
        for track in default_empirical_tracks()
    ]
    return sorted(assessments, key=lambda item: (len(item.missing_gates), item.track_id))
