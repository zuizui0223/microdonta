import pytest

from causal_model.theorem_projection_ledger import (
    projection_for,
    summary_by_status,
    theorem_projections,
    validate_projection_ledger,
)


def test_projection_ledger_is_internally_valid():
    validate_projection_ledger()
    assert tuple(item.key for item in theorem_projections()) == (
        "abstract_positive_two_factor_model",
        "spatial_pollination_abm",
        "colonization_connectivity_abm",
        "defense_metapopulation_abm",
        "campanula_published_record",
    )


def test_only_the_abstract_factor_model_is_marked_theorem_exact():
    summary = summary_by_status()
    assert summary["exact"] == ("abstract_positive_two_factor_model",)
    assert set(summary["requires_factorization_extension"]) == {
        "spatial_pollination_abm",
        "colonization_connectivity_abm",
        "defense_metapopulation_abm",
    }
    assert summary["not_applicable"] == ("campanula_published_record",)


def test_spatial_and_colonization_backends_cannot_claim_direct_channel_identification():
    for key in ("spatial_pollination_abm", "colonization_connectivity_abm"):
        projection = projection_for(key)
        assert projection.status == "requires_factorization_extension"
        assert projection.theorem_ids == ()
        assert "cannot" in projection.permitted_conclusion
        assert "factorisation_residual" in projection.next_outputs


def test_published_campanula_record_is_explicitly_not_a_channel_identification_case():
    projection = projection_for("campanula_published_record")
    assert projection.status == "not_applicable"
    assert projection.theorem_ids == ()
    assert "does not" in projection.permitted_conclusion
    assert "calibrated_pollination_or_establishment_proxy" in projection.next_outputs


def test_unknown_projection_is_not_silently_coerced():
    with pytest.raises(KeyError, match="unknown projection"):
        projection_for("made_up_backend")
