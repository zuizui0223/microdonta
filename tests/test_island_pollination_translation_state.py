import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "examples/island_pollination_translation/CURRENT_STATE.json"


def test_current_state_keeps_three_tracks_nonblocking():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    assert data["source_programme"] == "zuizui0223/izu-core"
    assert data["target_framework"] == "microdonta/RACH"
    assert data["role"] == "future_empirical_translation_not_current_izu_core_submission_blocker"
    assert [row["track_id"] for row in data["tracks"]] == [
        "signed_functional_starting_position",
        "network_context_effective_service",
        "complete_service_dependency_response_bridge",
    ]
    assert all(row["izu_core_submission_blocker"] is False for row in data["tracks"])
    assert "do_not_equate_visitor_abundance_identity_or_richness_with_effective_service" in data["protected_boundaries"]
    assert "do_not_equate_unsigned_matching_with_signed_functional_position" in data["protected_boundaries"]
