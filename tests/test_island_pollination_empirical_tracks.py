from examples.island_pollination_empirical_tracks import (
    audit_empirical_track,
    default_empirical_tracks,
    rank_empirical_tracks_by_missing_gates,
)


def test_registry_contains_exactly_three_standalone_tracks():
    tracks = default_empirical_tracks()
    assert [track.track_id for track in tracks] == [
        "signed_functional_starting_position",
        "network_context_effective_service",
        "complete_service_dependency_response_bridge",
    ]


def test_signed_position_requires_outcome_blind_source_native_mapping():
    track = default_empirical_tracks()[0]
    assert "outcome_blind_signed_position_formula" in track.required_gates
    assert "source_native_pollinator_functional_center" in track.required_gates
    assert track.derived_estimand == "signed_position = plant_matching_trait - pollinator_functional_center"
    assessment = audit_empirical_track(
        track.track_id,
        {
            "predeclared_plant_matching_trait",
            "matched_trait_units_and_comparison_unit",
            "downstream_reproductive_or_evolutionary_response",
            "sampling_hierarchy_and_uncertainty",
        },
    )
    assert assessment.ready is False
    assert assessment.missing_gates == (
        "source_native_pollinator_functional_center",
        "outcome_blind_signed_position_formula",
    )


def test_network_context_requires_direct_effectiveness():
    track = default_empirical_tracks()[1]
    assert track.derived_estimand == "effective_service = sum_k(visitor_rate_k * direct_effectiveness_k)"
    assessment = audit_empirical_track(
        track.track_id,
        {
            "matched_transition_or_context_unit",
            "repeated_local_context_support",
            "visitor_specific_rate",
            "downstream_reproductive_outcome",
        },
    )
    assert assessment.ready is False
    assert assessment.missing_gates == ("visitor_specific_direct_effectiveness",)


def test_complete_chain_is_conjunctive():
    track = default_empirical_tracks()[2]
    partial = set(track.required_gates) - {"reproductive_dependency_or_autonomous_assurance"}
    assert audit_empirical_track(track.track_id, partial).ready is False
    assert audit_empirical_track(track.track_id, set(track.required_gates)).ready is True


def test_structural_closeness_ranking_preserves_gate_logic():
    ranked = rank_empirical_tracks_by_missing_gates(
        {
            "network_context_effective_service": {
                "matched_transition_or_context_unit",
                "repeated_local_context_support",
                "visitor_specific_rate",
                "downstream_reproductive_outcome",
            }
        }
    )
    assert ranked[0].track_id == "network_context_effective_service"
    assert len(ranked[0].missing_gates) == 1
    assert ranked[0].ready is False


def test_unknown_track_is_rejected():
    try:
        audit_empirical_track("not_a_track", set())
    except ValueError as exc:
        assert "unknown empirical track" in str(exc)
    else:
        raise AssertionError("unknown track should raise ValueError")
