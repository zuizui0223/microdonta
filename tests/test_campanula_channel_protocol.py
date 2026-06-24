from causal_model.campanula_channel_protocol import (
    ChannelProtocol,
    assess_protocol,
    planned_recruitment_protocol,
    published_campanula_protocol,
)


def _has_requirement(assessment, phrase):
    return any(phrase in item for item in assessment.missing_requirements)


def test_published_campanula_record_cannot_be_promoted_to_channel_identification():
    assessment = assess_protocol(published_campanula_protocol())
    assert assessment.data_status == "published_only"
    assert assessment.readiness == "not_ready"
    assert assessment.pollinator_attribution == "not_addressed"
    assert _has_requirement(assessment, "trait-specific total-performance definition W(z)")
    assert _has_requirement(assessment, "local reproductive-factor definition F(z)")
    assert "cannot identify F versus E" in assessment.permitted_conclusion


def test_planned_recruitment_design_is_structurally_ready_but_not_collected_evidence():
    assessment = assess_protocol(planned_recruitment_protocol())
    assert assessment.data_status == "planned"
    assert assessment.readiness == "ready_direct_factor"
    assert assessment.pollinator_attribution == "component_model_declared"
    assert assessment.permitted_conclusion.startswith("The required measurements have not been collected")


def test_stable_validated_proxy_supports_relative_channel_inference():
    protocol = ChannelProtocol(
        name="stable_proxy_protocol",
        data_status="collected",
        trait_definition="common flower-size bins",
        comparison_definition="two regimes with the same seedling census window",
        common_trait_domain=True,
        net_performance_definition="retained recruits per maternal individual",
        local_factor_definition="local viable seed output",
        factor_observation="stable_validated_proxy",
        positive_interior_handling=True,
        factorisation_statement="W=F*E on the declared trait bins",
        pollinator_component_design=None,
    )
    assessment = assess_protocol(protocol)
    assert assessment.readiness == "ready_relative_stable_proxy"
    assert assessment.pollinator_attribution == "requires_component_decomposition"
    assert "provided the stated proxy calibration is stable" in assessment.permitted_conclusion
    assert "does not by itself identify its pollinator-mediated" in assessment.prohibited_conclusion


def test_unstable_or_unknown_proxy_does_not_break_n1_nonidentifiability():
    for observation in ("unknown_proxy", "known_drifting_proxy"):
        protocol = ChannelProtocol(
            name=observation,
            data_status="collected",
            trait_definition="common trait bins",
            comparison_definition="two regimes",
            common_trait_domain=True,
            net_performance_definition="W",
            local_factor_definition="F",
            factor_observation=observation,
            positive_interior_handling=True,
            factorisation_statement="W=F*E",
        )
        assessment = assess_protocol(protocol)
        assert assessment.readiness == "not_ready"
        assert _has_requirement(assessment, "stable or calibrated proxy-to-factor conversion")


def test_proxy_stability_assumption_is_not_silently_called_validation():
    protocol = ChannelProtocol(
        name="assumed_stable_proxy",
        data_status="collected",
        trait_definition="common trait bins",
        comparison_definition="two regimes",
        common_trait_domain=True,
        net_performance_definition="W",
        local_factor_definition="F",
        factor_observation="stable_assumed_proxy",
        positive_interior_handling=True,
        factorisation_statement="W=F*E",
    )
    assessment = assess_protocol(protocol)
    assert assessment.readiness == "conditional_on_proxy_stability"
    assert "only if its proxy-calibration stability assumption" in assessment.permitted_conclusion


def test_direct_factor_protocol_still_requires_common_domain_and_boundary_handling():
    protocol = ChannelProtocol(
        name="broken_direct_factor",
        data_status="collected",
        trait_definition="",
        comparison_definition="",
        common_trait_domain=False,
        net_performance_definition="W",
        local_factor_definition="F",
        factor_observation="direct_factor",
        positive_interior_handling=False,
        factorisation_statement="W=F*E",
    )
    assessment = assess_protocol(protocol)
    assert assessment.readiness == "not_ready"
    assert _has_requirement(assessment, "a common trait domain across the compared regimes")
    assert _has_requirement(assessment, "a predeclared trait definition")
    assert _has_requirement(assessment, "a declared treatment of zero W, F, or E boundary states")
