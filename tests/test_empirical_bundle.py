import json

from examples.island_pollination_translation import (
    audit_empirical_bundle,
    bundle_template,
    load_empirical_bundle,
)
from examples.island_pollination_translation.audit_bundle import main


def provenance(label="source"):
    return {"source_id": f"doi:{label}", "locator": "table 1"}


def direct(
    evidence_id,
    gate,
    *,
    unit="count",
    comparison_unit="population-year",
    frozen=False,
):
    return {
        "evidence_id": evidence_id,
        "gate": gate,
        "status": "present",
        "evidence_kind": "direct_measurement",
        "description": f"measured {gate}",
        "unit": unit,
        "comparison_unit": comparison_unit,
        "method": "prespecified field protocol",
        "uncertainty": "hierarchical standard error",
        "provenance": provenance(evidence_id),
        "frozen_before_outcome": frozen,
    }


def definition(
    evidence_id,
    gate,
    *,
    formula=None,
    comparison_unit="population-year",
    frozen=True,
):
    result = {
        "evidence_id": evidence_id,
        "gate": gate,
        "status": "present",
        "evidence_kind": "prespecified_definition",
        "description": f"declared {gate}",
        "comparison_unit": comparison_unit,
        "provenance": provenance(evidence_id),
        "frozen_before_outcome": frozen,
    }
    if formula:
        result["formula"] = formula
    return result


def base_bundle(track_id, evidence, *, independent=None):
    return {
        "schema_version": "1.0",
        "bundle_id": f"bundle-{track_id}",
        "track_id": track_id,
        "system_id": "real-system-A",
        "comparison_unit": "population-year",
        "compatible_comparison_units": [],
        "independent_system": independent,
        "evidence": evidence,
    }


def test_generated_template_is_explicitly_incomplete():
    payload = bundle_template("network_context_effective_service")
    assessment = audit_empirical_bundle(load_empirical_bundle(payload))
    assert assessment.schema_valid is False
    assert assessment.measurement_contract_ready is False
    assert len(assessment.missing_gates) == 5


def test_complete_signed_position_bundle_closes_all_measurement_gates():
    evidence = [
        direct(
            "plant-trait",
            "predeclared_plant_matching_trait",
            unit="mm",
            frozen=True,
        ),
        direct(
            "pollinator-center-input",
            "pollinator_trait_distribution",
            unit="mm",
        ),
        {
            "evidence_id": "pollinator-center",
            "gate": "source_native_pollinator_functional_center",
            "status": "present",
            "evidence_kind": "derived_estimand",
            "description": "source-native weighted functional center",
            "unit": "mm",
            "comparison_unit": "population-year",
            "method": "visitor-rate weighted center",
            "provenance": provenance("center"),
            "formula": "sum(rate * trait) / sum(rate)",
            "derived_from": ["pollinator-center-input"],
            "frozen_before_outcome": False,
        },
        definition("units", "matched_trait_units_and_comparison_unit"),
        definition(
            "signed-formula",
            "outcome_blind_signed_position_formula",
            formula="plant_matching_trait - pollinator_functional_center",
        ),
        direct(
            "response",
            "downstream_reproductive_or_evolutionary_response",
            unit="seeds per flower",
        ),
        definition("hierarchy", "sampling_hierarchy_and_uncertainty"),
    ]
    assessment = audit_empirical_bundle(
        load_empirical_bundle(
            base_bundle("signed_functional_starting_position", evidence)
        )
    )
    assert assessment.schema_valid is True
    assert assessment.measurement_contract_ready is True
    assert assessment.missing_gates == ()
    assert assessment.auxiliary_gates == ("pollinator_trait_distribution",)


def test_visitation_cannot_silently_replace_direct_effectiveness():
    evidence = [
        definition("context-unit", "matched_transition_or_context_unit"),
        direct("context", "repeated_local_context_support"),
        direct("rate", "visitor_specific_rate", unit="visits per flower-hour"),
        {
            **direct(
                "effect",
                "visitor_specific_direct_effectiveness",
                unit="visits per flower-hour",
            ),
            "evidence_kind": "calibrated_proxy",
            "proxy_target": "direct per-visit effectiveness",
            "calibration": {
                "status": "unverified",
                "scope": "population-year",
                "provenance": provenance("calibration"),
            },
        },
        direct(
            "reproduction",
            "downstream_reproductive_outcome",
            unit="seeds per flower",
        ),
    ]
    assessment = audit_empirical_bundle(
        load_empirical_bundle(
            base_bundle("network_context_effective_service", evidence)
        )
    )
    assert assessment.schema_valid is True
    assert assessment.measurement_contract_ready is False
    assert assessment.missing_gates == (
        "visitor_specific_direct_effectiveness",
    )
    diagnostic = next(
        row for row in assessment.diagnostics if row.evidence_id == "effect"
    )
    assert "N3/N4" in " ".join(diagnostic.reasons)


def test_calibrated_proxy_can_close_effectiveness_gate():
    evidence = [
        definition("context-unit", "matched_transition_or_context_unit"),
        direct("context", "repeated_local_context_support"),
        direct("rate", "visitor_specific_rate", unit="visits per flower-hour"),
        {
            **direct(
                "effect",
                "visitor_specific_direct_effectiveness",
                unit="pollen grains per visit",
            ),
            "evidence_kind": "calibrated_proxy",
            "proxy_target": "direct per-visit effectiveness",
            "calibration": {
                "status": "calibrated",
                "scope": "same populations, flowering season and visitor taxa",
                "provenance": provenance("calibration"),
            },
        },
        direct(
            "reproduction",
            "downstream_reproductive_outcome",
            unit="seeds per flower",
        ),
    ]
    assessment = audit_empirical_bundle(
        load_empirical_bundle(
            base_bundle("network_context_effective_service", evidence)
        )
    )
    assert assessment.measurement_contract_ready is True


def test_complete_bridge_requires_independent_system_even_with_all_gates():
    evidence = [
        direct("change", "pollinator_functional_change"),
        direct("service", "effective_service_or_direct_pollen_function"),
        direct("dependency", "reproductive_dependency_or_autonomous_assurance"),
        direct(
            "response",
            "downstream_floral_reproductive_or_evolutionary_response",
        ),
        definition("linkage", "compatible_unit_linkage"),
        definition("hierarchy", "sampling_hierarchy_and_uncertainty"),
        definition("sources", "source_provenance", frozen=False),
    ]
    assessment = audit_empirical_bundle(
        load_empirical_bundle(
            base_bundle(
                "complete_service_dependency_response_bridge",
                evidence,
                independent=False,
            )
        )
    )
    assert assessment.schema_valid is False
    assert assessment.measurement_contract_ready is False
    assert any(
        "independent_system=true" in error
        for error in assessment.schema_errors
    )


def test_derived_gate_rejects_missing_dependency():
    derived = {
        "evidence_id": "center",
        "gate": "source_native_pollinator_functional_center",
        "status": "present",
        "evidence_kind": "derived_estimand",
        "description": "weighted center",
        "unit": "mm",
        "comparison_unit": "population-year",
        "method": "weighted mean",
        "provenance": provenance("center"),
        "formula": "sum(rate * trait) / sum(rate)",
        "derived_from": ["absent-input"],
        "frozen_before_outcome": False,
    }
    assessment = audit_empirical_bundle(
        load_empirical_bundle(
            base_bundle("signed_functional_starting_position", [derived])
        )
    )
    row = assessment.diagnostics[0]
    assert row.accepted is False
    assert "missing evidence" in " ".join(row.reasons)


def test_cli_template_and_audit_round_trip(tmp_path, capsys):
    template = tmp_path / "bundle.json"
    assert (
        main(
            [
                "template",
                "network_context_effective_service",
                str(template),
            ]
        )
        == 0
    )
    payload = json.loads(template.read_text())
    assert payload["track_id"] == "network_context_effective_service"
    assert main(["audit", str(template), "--json"]) == 2
    output = capsys.readouterr().out
    assert '"measurement_contract_ready": false' in output


def test_cli_require_ready_returns_one_for_valid_but_incomplete_bundle(
    tmp_path,
):
    payload = base_bundle(
        "network_context_effective_service",
        [definition("context-unit", "matched_transition_or_context_unit")],
    )
    path = tmp_path / "partial.json"
    path.write_text(json.dumps(payload))
    assert main(["audit", str(path), "--require-ready"]) == 1
