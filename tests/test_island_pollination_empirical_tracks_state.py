import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "examples/island_pollination_empirical_tracks/CURRENT_STATE.json"


def test_current_state_is_standalone_and_has_three_tracks():
    data = json.loads(STATE.read_text(encoding="utf-8"))
    assert data["owner_framework"] == "microdonta/RACH"
    assert data["programme"] == "island_pollination_empirical_observation_design"
    assert data["role"] == "standalone_empirical_causal_observation_design"
    assert data["external_manuscript_dependency"] is False
    assert data["external_repository_dependency"] is False
    assert [row["track_id"] for row in data["tracks"]] == [
        "signed_functional_starting_position",
        "network_context_effective_service",
        "complete_service_dependency_response_bridge",
    ]
    assert "do_not_equate_visitor_abundance_identity_or_richness_with_effective_service" in data["protected_boundaries"]
    assert "do_not_equate_unsigned_matching_with_signed_functional_position" in data["protected_boundaries"]
    assert "do_not_make_track_readiness_depend_on_an_external_manuscript_or_repository" in data["protected_boundaries"]
