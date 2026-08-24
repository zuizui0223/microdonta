"""RACH bridge for the three non-blocking empirical translation tracks from izu-core.

The current izu-core island-ecology paper has closed its primary synthetic
hypotheses.  What remains unresolved is not another simulation layer, but three
empirical mappings that would reduce causal degeneracy in real island systems.

This module keeps those questions in microdonta as next-observation design
objects.  It deliberately does not import izu-core or silently promote its
synthetic results into empirical causal claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TranslationTrack:
    """One empirical translation question exported from the izu-core mainline."""

    track_id: str
    title: str
    izu_core_starting_point: str
    unresolved_empirical_claim: str
    rach_role: str
    required_gates: tuple[str, ...]
    derived_estimand: str | None
    forbidden_shortcuts: tuple[str, ...]
    completion_condition: str
    current_state: str
    submission_blocker_for_izu_core: bool = False


@dataclass(frozen=True)
class TranslationAssessment:
    """Readiness result for a proposed empirical bundle."""

    track_id: str
    ready: bool
    passed_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]
    permitted_conclusion: str
    prohibited_conclusion: str


def default_translation_tracks() -> tuple[TranslationTrack, ...]:
    """Return the three frozen, non-blocking izu-core -> microdonta tracks."""

    return (
        TranslationTrack(
            track_id="signed_functional_starting_position",
            title="Real signed functional starting position",
            izu_core_starting_point=(
                "The frozen ABM identifies pre-existing lineage position in an abstract "
                "functional matching space as the replicated minimal generator of "
                "within-run response-sign branching."
            ),
            unresolved_empirical_claim=(
                "A source-native signed plant position relative to the pollinator "
                "functional environment predicts the direction or magnitude of a real "
                "island response."
            ),
            rach_role=(
                "Next observation that separates a real starting-state mechanism from "
                "downstream context, lineage identity, and other propagation filters. "
                "If either plant or pollinator trait is proxied, RACH N3/N4 proxy "
                "calibration applies."
            ),
            required_gates=(
                "predeclared_plant_matching_trait",
                "source_native_pollinator_functional_center",
                "matched_trait_units_and_comparison_unit",
                "outcome_blind_signed_position_formula",
                "downstream_reproductive_or_evolutionary_response",
                "sampling_hierarchy_and_uncertainty",
            ),
            derived_estimand=(
                "signed_position = plant_matching_trait - pollinator_functional_center"
            ),
            forbidden_shortcuts=(
                "use an unsigned matching score as if it encoded signed position",
                "impute pollinator trait from guild midpoint, family, body size, or syndrome",
                "choose the sign convention or functional center after inspecting the outcome",
                "equate the synthetic ABM coordinate with one named floral trait without a mapping gate",
            ),
            completion_condition=(
                "A prespecified empirical unit provides plant trait, pollinator functional "
                "center and downstream response on compatible scales, with the signed "
                "mapping frozen before outcome inspection."
            ),
            current_state=(
                "blocked_for_direct_signed_position_test_in_current_izu_record; synthetic "
                "mechanism identified, empirical trait mapping unresolved"
            ),
        ),
        TranslationTrack(
            track_id="network_context_effective_service",
            title="Real network context to effective service",
            izu_core_starting_point=(
                "Local support is a strong bidirectional branch allocator in the frozen "
                "ABM: it can attenuate, sign-rescue, or worsen matched declines."
            ),
            unresolved_empirical_claim=(
                "A measured change in local partner context changes rate-weighted effective "
                "pollination service and thereby changes the downstream reproductive response "
                "in a named real island system."
            ),
            rach_role=(
                "Direct calibration problem for a commonly used proxy. Visitor abundance, "
                "identity, richness or network degree is not effective service unless the "
                "proxy-to-service conversion is stable or direct effectiveness is measured."
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
                "The same prespecified context hierarchy supplies V_k, E_k, local context and "
                "reproductive outcome, allowing a matched effective-service contrast."
            ),
            current_state=(
                "no_current_strict_system_is_mapping_ready; partial bridges exist but the "
                "required rate-by-effectiveness linkage is incomplete"
            ),
        ),
        TranslationTrack(
            track_id="complete_service_dependency_response_bridge",
            title="Complete pollinator-change to service to dependency/assurance to response bridge",
            izu_core_starting_point=(
                "The island-ecology synthesis separates upstream pollinator functional change, "
                "network-mediated effective service, reproductive dependency or assurance, and "
                "the final reproductive/evolutionary response."
            ),
            unresolved_empirical_claim=(
                "At least one independent non-Izu island system links the complete causal chain "
                "on the same or a prespecified compatible unit."
            ),
            rach_role=(
                "Sequential observation package for cutting several mechanism-equivalence edges. "
                "It is a RACH-SEQ target: adjacent links are measured separately so missing links "
                "are not inferred from neighbouring observations."
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
                "One independent system supplies at least the four causal links on compatible "
                "units with uncertainty and provenance; a formal cross-system model remains a "
                "separate gate."
            ),
            current_state=(
                "multiple_partial_bridges_but_zero_complete_bridge_systems; source-triggered or "
                "prospective completion only"
            ),
        ),
    )


def _track_map() -> dict[str, TranslationTrack]:
    return {track.track_id: track for track in default_translation_tracks()}


def audit_track(track_id: str, observed_gates: Iterable[str]) -> TranslationAssessment:
    """Audit whether a proposed observation bundle closes one translation track.

    Extra observed gates are harmless.  Readiness is deliberately conjunctive:
    every required gate must be present.  This prevents a convenient proxy from
    silently replacing a missing mechanism link.
    """

    try:
        track = _track_map()[track_id]
    except KeyError as exc:
        raise ValueError(f"unknown translation track: {track_id}") from exc

    observed = frozenset(observed_gates)
    passed = tuple(gate for gate in track.required_gates if gate in observed)
    missing = tuple(gate for gate in track.required_gates if gate not in observed)
    ready = not missing

    if ready:
        permitted = (
            "The observation bundle closes the declared structural gate for this track. "
            "Any causal conclusion still remains conditional on the declared comparison, "
            "measurement model and RACH admissible family."
        )
    else:
        permitted = (
            "Retain the competing empirical explanations and use the missing gates as the "
            "next-observation target; do not promote the izu-core synthetic mechanism to a "
            "real-system causal claim."
        )

    prohibited = (
        "Missing gates may not be filled by visitor identity, syndrome labels, geography, "
        "unsigned matching, unmatched cross-study transport, or post-outcome remapping."
    )

    return TranslationAssessment(
        track_id=track_id,
        ready=ready,
        passed_gates=passed,
        missing_gates=missing,
        permitted_conclusion=permitted,
        prohibited_conclusion=prohibited,
    )


def rank_tracks_by_missing_gates(
    observed_by_track: dict[str, Iterable[str]],
) -> list[TranslationAssessment]:
    """Rank tracks by structural closeness without claiming scientific priority.

    Fewer missing gates means closer to *structural* completion only.  It is not a
    causal-effect ranking and should not override biological leverage or field cost.
    """

    assessments = [
        audit_track(track.track_id, observed_by_track.get(track.track_id, ()))
        for track in default_translation_tracks()
    ]
    return sorted(assessments, key=lambda item: (len(item.missing_gates), item.track_id))
