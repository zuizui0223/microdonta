"""Auditable ledger for projecting identifiability theorems onto repository models.

Theorems N1--N4 are exact only for a declared positive factorisation
``W(z)=F(z)E(z)`` and declared observation map.  This module prevents a common
category error: treating an ABM's total invasion growth rate or an empirical trait
pattern as though it already supplied those factors.

Every target is assigned one status:

``exact``
    The target *is* the theorem's mathematical model.
``requires_factorization_extension``
    The target contains relevant biological channels but does not currently emit
    a declared trait-level W=F*E decomposition or the observations needed by the
    theorem.
``not_applicable``
    The target record does not yet contain the required observation class.

The entries are an explicit scope boundary, not evidence against the ABMs or the
empirical system. They specify what must be added before each theorem may be
invoked there.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ProjectionStatus = Literal[
    "exact",
    "requires_factorization_extension",
    "not_applicable",
]


@dataclass(frozen=True)
class TheoremProjection:
    """One target's admissible relationship to the N1--N4 theorem family."""

    key: str
    target: str
    status: ProjectionStatus
    theorem_ids: tuple[str, ...]
    current_output: str
    current_factorisation: str
    permitted_conclusion: str
    prohibited_conclusion: str
    missing_requirements: tuple[str, ...]
    next_outputs: tuple[str, ...]


_PROJECTIONS: tuple[TheoremProjection, ...] = (
    TheoremProjection(
        key="abstract_positive_two_factor_model",
        target="Positive two-factor mathematical model",
        status="exact",
        theorem_ids=("N1", "N2", "N3", "N4"),
        current_output="Trait-specific positive net performance W(z) and declared factors F(z), E(z).",
        current_factorisation="Exact by definition: W(z)=F(z)E(z), with a shared trait domain.",
        permitted_conclusion=(
            "Net-only observations are non-identifying; W plus a factor, or a stable "
            "proxy for a factor, identifies relative channel changes under the stated theorems."
        ),
        prohibited_conclusion="None beyond the theorems' own positivity, factorisation, and calibration assumptions.",
        missing_requirements=(),
        next_outputs=(),
    ),
    TheoremProjection(
        key="spatial_pollination_abm",
        target="Spatial metapopulation ABM: pollination-loss backend",
        status="requires_factorization_extension",
        theorem_ids=(),
        current_output=(
            "A stochastic multi-step rare-invader log growth rate lambda(z'|Z*) and "
            "a viable set Omega_inv. The deterministic helper has G(z)=survival(z)*(1+repro(z))."
        ),
        current_factorisation=(
            "The available product separates survival from one-step reproductive output, "
            "not a declared local pollination factor F from an establishment/reachability factor E. "
            "Multi-step lambda also contains density dependence, mate matching, resources, "
            "dispersal, and demographic stochasticity."
        ),
        permitted_conclusion=(
            "The backend can test conditional responses to its isolated pollination intervention; "
            "it cannot by itself invoke N1--N4 to identify pollination versus establishment channels."
        ),
        prohibited_conclusion=(
            "An Omega_inv geometry or lambda change proves that pollinator-mediated F, rather than "
            "reachability/recruitment E, changed."
        ),
        missing_requirements=(
            "A declared trait-level performance W on the same comparison scale.",
            "A separately emitted local reproductive/pollination factor F.",
            "A separately emitted establishment/reachability factor E.",
            "A checked equality or explicitly bounded approximation W=F*E.",
        ),
        next_outputs=(
            "trait_specific_net_performance",
            "trait_specific_local_reproductive_factor",
            "trait_specific_establishment_factor",
            "factorisation_residual",
        ),
    ),
    TheoremProjection(
        key="colonization_connectivity_abm",
        target="Colonization metapopulation ABM: corridor-loss backend",
        status="requires_factorization_extension",
        theorem_ids=(),
        current_output=(
            "A stochastic multi-step invasion log growth rate. Individual transitions include survival, "
            "conception, dispersal investment, corridor connectivity, and target-patch density."
        ),
        current_factorisation=(
            "The biological ingredients suggest local offspring production and establishment channels, "
            "but the current lambda is not emitted as a declared trait-level W=F*E product."
        ),
        permitted_conclusion=(
            "The backend can test whether connectivity loss changes its simulated invasion and endpoint patterns; "
            "it cannot yet apply N1--N4 as an exact channel-identification result."
        ),
        prohibited_conclusion=(
            "A connectivity-associated trait-space geometry uniquely establishes an E-channel change "
            "relative to all local reproductive alternatives."
        ),
        missing_requirements=(
            "A one-generation or otherwise declared decomposition of lineage performance.",
            "Trait-specific local offspring factor F and establishment factor E.",
            "A documented treatment of density, extinction, and multi-step feedback in the factorisation.",
        ),
        next_outputs=(
            "trait_specific_local_offspring_factor",
            "trait_specific_dispersal_settlement_factor",
            "trait_specific_net_performance",
            "factorisation_residual",
        ),
    ),
    TheoremProjection(
        key="defense_metapopulation_abm",
        target="Defense metapopulation ABM: predator-loss backend",
        status="requires_factorization_extension",
        theorem_ids=(),
        current_output=(
            "A survival-mediated trait system evaluated through resident dynamics and invasion outcomes."
        ),
        current_factorisation=(
            "The current backend separates neither a designated local F channel nor a designated "
            "establishment E channel on the theorem's observation scale."
        ),
        permitted_conclusion=(
            "The backend is an independent survival-channel robustness model, not an exact instance "
            "of the two-factor N1--N4 theorem."
        ),
        prohibited_conclusion=(
            "A defense-model shift or contraction directly validates the N1--N4 channel-identification boundary."
        ),
        missing_requirements=(
            "Declared W=F*E factorisation for the chosen trait-performance quantity.",
            "Channel-resolved observations on a common trait domain.",
        ),
        next_outputs=(
            "declared_trait_performance_factorisation",),
    ),
    TheoremProjection(
        key="campanula_published_record",
        target="Campanula microdonta published Izu-island record",
        status="not_applicable",
        theorem_ids=(),
        current_output=(
            "Published directional gradients in selfing and flower size with isolation, plus a documented "
            "pollinator transition."
        ),
        current_factorisation=(
            "No trait-specific W, no declared F/E factorisation, and no before/after channel proxy with "
            "calibration stability established."
        ),
        permitted_conclusion=(
            "The published record retains multiple mechanisms and supports next-observation design; it does not "
            "identify an F or E channel under N1--N4."
        ),
        prohibited_conclusion=(
            "Flower-size or selfing gradients, pollinator identity, or trait-space geometry alone identify a "
            "pollination/fecundity channel versus establishment/reachability channel."
        ),
        missing_requirements=(
            "A declared trait-specific total-performance measure W.",
            "One direct factor or a proxy whose trait-specific calibration is stable or measured across regimes.",
            "A biologically justified mapping from field quantities onto W, F, and E.",
        ),
        next_outputs=(
            "trait_specific_total_performance",
            "calibrated_pollination_or_establishment_proxy",
            "proxy_calibration_stability_check",
        ),
    ),
)


def theorem_projections() -> tuple[TheoremProjection, ...]:
    """Return the immutable projection ledger in reviewable order."""
    return _PROJECTIONS


def projection_for(key: str) -> TheoremProjection:
    """Return one projection entry or raise a descriptive lookup error."""
    for projection in _PROJECTIONS:
        if projection.key == key:
            return projection
    available = ", ".join(item.key for item in _PROJECTIONS)
    raise KeyError(f"unknown projection {key!r}; available: {available}")


def validate_projection_ledger() -> None:
    """Guard against silently upgrading an incomplete backend to theorem-exact status."""
    keys = [entry.key for entry in _PROJECTIONS]
    if len(keys) != len(set(keys)):
        raise ValueError("projection ledger keys must be unique")
    for entry in _PROJECTIONS:
        if entry.status == "exact":
            if not entry.theorem_ids:
                raise ValueError(f"exact projection {entry.key} must name theorem ids")
            if entry.missing_requirements:
                raise ValueError(f"exact projection {entry.key} cannot retain missing requirements")
        else:
            if entry.theorem_ids:
                raise ValueError(
                    f"non-exact projection {entry.key} cannot claim direct theorem applicability"
                )
            if not entry.missing_requirements:
                raise ValueError(f"non-exact projection {entry.key} must state its blocking requirements")


def summary_by_status() -> dict[ProjectionStatus, tuple[str, ...]]:
    """Return a compact auditable view of which targets are theorem-exact."""
    return {
        status: tuple(entry.key for entry in _PROJECTIONS if entry.status == status)
        for status in ("exact", "requires_factorization_extension", "not_applicable")
    }
