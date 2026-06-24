"""Protocol checker for projecting N1--N4 onto a Campanula field study.

The module deliberately does not turn the existing published Izu-island patterns
into channel identification.  Instead it checks whether a proposed or collected
observation set supplies the inputs required by the theorem family:

    W(z) = F(z) E(z),

where ``W`` is a declared trait-specific performance measure, ``F`` is a local
reproductive factor, and ``E`` is establishment/reachability.  N2 identifies F
versus E from W plus a direct F (or E); N3 permits a proxy only when its
proxy-to-factor conversion is stable or calibrated across the compared regimes.

A second boundary is kept explicit: identifying total local reproduction F versus
establishment E does not, by itself, identify the pollinator-mediated component
inside F.  That requires a separately declared experimental decomposition.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


DataStatus = Literal["published_only", "planned", "collected"]
FactorObservation = Literal[
    "none",
    "direct_factor",
    "stable_validated_proxy",
    "stable_assumed_proxy",
    "unknown_proxy",
    "known_drifting_proxy",
]
Readiness = Literal[
    "not_ready",
    "ready_direct_factor",
    "ready_relative_stable_proxy",
    "conditional_on_proxy_stability",
]
PollinatorAttribution = Literal[
    "not_addressed",
    "requires_component_decomposition",
    "component_model_declared",
]


@dataclass(frozen=True)
class ChannelProtocol:
    """Pre-registered mapping from a Campanula comparison to theorem quantities.

    The protocol is trait-specific: the same trait bins or individual trait values
    must be evaluable across the compared populations/regimes.  ``net_performance``
    and ``local_factor`` are definitions, not data values; ``data_status`` tells
    whether those definitions have been measured yet.
    """

    name: str
    data_status: DataStatus
    trait_definition: str
    comparison_definition: str
    common_trait_domain: bool
    net_performance_definition: str | None
    local_factor_definition: str | None
    factor_observation: FactorObservation
    positive_interior_handling: bool
    factorisation_statement: str | None
    pollinator_component_design: str | None = None


@dataclass(frozen=True)
class ProtocolAssessment:
    """Theorem readiness and remaining limits for one field protocol."""

    protocol_name: str
    data_status: DataStatus
    readiness: Readiness
    pollinator_attribution: PollinatorAttribution
    missing_requirements: tuple[str, ...]
    permitted_conclusion: str
    prohibited_conclusion: str
    next_measurements: tuple[str, ...]


def assess_protocol(protocol: ChannelProtocol) -> ProtocolAssessment:
    """Assess whether the protocol can support N1--N4 channel conclusions.

    A planned design can be structurally adequate but is never treated as a
    collected theorem application.  Its assessment records what it would support
    after collection, while the current data status remains visible.
    """
    missing: list[str] = []
    if not protocol.common_trait_domain:
        missing.append("a common trait domain across the compared regimes")
    if not protocol.trait_definition.strip():
        missing.append("a predeclared trait definition")
    if not protocol.comparison_definition.strip():
        missing.append("a predeclared before/after or cross-regime comparison")
    if not protocol.net_performance_definition:
        missing.append("a trait-specific total-performance definition W(z)")
    if not protocol.local_factor_definition:
        missing.append("a local reproductive-factor definition F(z)")
    if not protocol.factorisation_statement:
        missing.append("a biological factorisation linking W(z), F(z), and E(z)")
    if not protocol.positive_interior_handling:
        missing.append("a declared treatment of zero W, F, or E boundary states")

    base_ready = not missing
    observation = protocol.factor_observation
    if observation == "none":
        missing.append("a direct local factor or an informative proxy")
        readiness: Readiness = "not_ready"
    elif observation in {"unknown_proxy", "known_drifting_proxy"}:
        missing.append("stable or calibrated proxy-to-factor conversion across regimes")
        readiness = "not_ready"
    elif observation == "stable_assumed_proxy":
        readiness = "conditional_on_proxy_stability" if base_ready else "not_ready"
    elif observation == "stable_validated_proxy":
        readiness = "ready_relative_stable_proxy" if base_ready else "not_ready"
    elif observation == "direct_factor":
        readiness = "ready_direct_factor" if base_ready else "not_ready"
    else:  # defensive coverage for future literal expansion
        raise ValueError(f"unknown factor observation state: {observation}")

    if protocol.pollinator_component_design is None:
        pollinator_attribution: PollinatorAttribution = (
            "not_addressed" if protocol.local_factor_definition is None
            else "requires_component_decomposition"
        )
    else:
        pollinator_attribution = "component_model_declared"

    current_prefix = (
        "The required measurements have not been collected; "
        if protocol.data_status != "collected" else ""
    )
    if readiness == "ready_direct_factor":
        permitted = current_prefix + (
            "within the declared positive factorisation, the data can identify "
            "relative local-reproduction F versus establishment E changes."
        )
    elif readiness == "ready_relative_stable_proxy":
        permitted = current_prefix + (
            "within the declared factorisation, the data can identify relative F/E "
            "changes provided the stated proxy calibration is stable."
        )
    elif readiness == "conditional_on_proxy_stability":
        permitted = current_prefix + (
            "the design becomes N3-informative only if its proxy-calibration stability "
            "assumption is independently defended or calibrated."
        )
    else:
        permitted = current_prefix + (
            "the observation set can retain competing explanations and guide the next "
            "measurement, but cannot identify F versus E under N1--N4."
        )

    prohibited = (
        "A flower-trait gradient, selfing rate, visit count, or pollinator identity alone "
        "identifies a pollination/fecundity channel versus establishment/reachability."
    )
    if pollinator_attribution != "component_model_declared":
        prohibited += (
            " Even an identified total local-reproduction factor F does not by itself "
            "identify its pollinator-mediated versus autonomous-selfing components."
        )

    next_measurements: list[str] = []
    if not protocol.net_performance_definition:
        next_measurements.append(
            "define and measure W(z): retained recruits per maternal individual over a stated census window"
        )
    if not protocol.local_factor_definition:
        next_measurements.append(
            "define and measure F(z): viable seed output per maternal individual conditional on adult survival"
        )
    if observation in {"none", "unknown_proxy", "known_drifting_proxy", "stable_assumed_proxy"}:
        next_measurements.append(
            "directly measure F or validate/calibrate proxy-to-F conversion across compared regimes"
        )
    if not protocol.positive_interior_handling:
        next_measurements.append(
            "pre-register how zero performance, seed output, or recruitment states are analysed"
        )
    if protocol.pollinator_component_design is None:
        next_measurements.append(
            "declare a pollinator-component experiment rather than equating total F with pollinator service"
        )

    return ProtocolAssessment(
        protocol_name=protocol.name,
        data_status=protocol.data_status,
        readiness=readiness,
        pollinator_attribution=pollinator_attribution,
        missing_requirements=tuple(missing),
        permitted_conclusion=permitted,
        prohibited_conclusion=prohibited,
        next_measurements=tuple(next_measurements),
    )


def published_campanula_protocol() -> ChannelProtocol:
    """Represent the actual published record without adding unmeasured variables.

    The source-confirmed inputs are aggregate directional selfing and flower-size
    gradients plus a pollinator transition. They are deliberately not recoded as
    trait-specific W or F measurements.
    """
    return ChannelProtocol(
        name="published_izu_record",
        data_status="published_only",
        trait_definition="aggregate selfing-rate and flower-size directional gradients",
        comparison_definition="isolation gradient among Izu-island populations",
        common_trait_domain=False,
        net_performance_definition=None,
        local_factor_definition=None,
        factor_observation="none",
        positive_interior_handling=False,
        factorisation_statement=None,
        pollinator_component_design=None,
    )


def planned_recruitment_protocol() -> ChannelProtocol:
    """A theorem-compatible prospective design, not a claim of collected data.

    ``F`` is intentionally defined as *total local viable seed output*, which can
    be measured without pretending it is purely pollinator mediated. An additional
    component experiment is required before interpreting variation inside F as a
    pollinator-specific effect.
    """
    return ChannelProtocol(
        name="planned_trait_specific_recruitment_design",
        data_status="planned",
        trait_definition=(
            "predeclared individual flower-trait values or fixed trait bins, evaluated "
            "on the same scale in every compared population"
        ),
        comparison_definition="predeclared island or isolation regimes with a shared census window",
        common_trait_domain=True,
        net_performance_definition=(
            "W(z): expected retained recruits per maternal individual over the stated census window"
        ),
        local_factor_definition=(
            "F(z): viable seed output per maternal individual conditional on adult survival"
        ),
        factor_observation="direct_factor",
        positive_interior_handling=True,
        factorisation_statement=(
            "W(z)=F(z)E(z), where E(z) is recruitment/reachability conditional on viable seed output"
        ),
        pollinator_component_design=(
            "predeclared trait-specific open, exclusion, and/or supplementation contrast with an explicit "
            "component model"
        ),
    )


def assessment_as_dict(protocol: ChannelProtocol) -> dict:
    """Return a JSON-ready protocol and assessment record for reports/examples."""
    return {
        "protocol": asdict(protocol),
        "assessment": asdict(assess_protocol(protocol)),
    }
