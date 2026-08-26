import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "examples/island_pollination_translation/CURRENT_STATE.json"


def test_current_state_separates_epistemic_from_empirical_resolution():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    assert data["schema_version"] == "2.0"
    assert data["source_programme"] == "zuizui0223/izu-core"
    assert data["target_framework"] == "microdonta/RACH"
    assert data["role"] == (
        "epistemically_resolved_empirically_open_translation_tracks_not_current_submission_blockers"
    )
    assert [row["track_id"] for row in data["tracks"]] == [
        "signed_functional_starting_position",
        "network_context_effective_service",
        "complete_service_dependency_response_bridge",
    ]

    # All three inherited questions are closed as Methods/identifiability problems:
    # the estimand, missing observations and forbidden shortcuts are explicit.
    assert all(row["methods_question_resolved"] is True for row in data["tracks"])
    assert all(row["epistemic_resolution"].startswith("closed_") for row in data["tracks"])

    # None is promoted to a real-system causal result without new qualifying data.
    assert all(row["empirical_claim_established"] is False for row in data["tracks"])
    assert all(row["empirical_resolution"].startswith("open_") for row in data["tracks"])

    # The empirical follow-ups do not reopen either frozen submission mainline.
    assert all(row["izu_core_submission_blocker"] is False for row in data["tracks"])
    assert all(row["microdonta_submission_blocker"] is False for row in data["tracks"])

    assert (
        "do_not_equate_visitor_abundance_identity_or_richness_with_effective_service"
        in data["protected_boundaries"]
    )
    assert (
        "do_not_equate_unsigned_matching_with_signed_functional_position"
        in data["protected_boundaries"]
    )
    assert (
        "do_not_call_a_track_empirically_solved_merely_because_its_identifiability_and_measurement_contract_is_closed"
        in data["protected_boundaries"]
    )
