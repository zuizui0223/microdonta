"""Bridge from causal hypotheses to biological generator inputs.

This module defines the Issue #4 interface between:

1. `causal_model` causal structures and pathway switches,
2. latent benefit/cost/fitness parameters, and
3. the `attraction_trait_model` biological generator.

The functions here are intentionally lightweight. They document and expose the
translation layer without implementing a full stochastic ABM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from attraction_trait_model import ModelParameters

from .structures import CausalStructure
from .switches import PathwaySwitches, switches_for_structure


@dataclass(frozen=True)
class GeneratorBridgeInput:
    """Inputs passed from a causal hypothesis to a biological generator."""

    structure_name: str
    switches: PathwaySwitches
    parameters: ModelParameters
    latent_overrides: dict[str, float] = field(default_factory=dict)
    notes: str = ""


def bridge_inputs_for_structure(
    structure: CausalStructure,
    base_parameters: ModelParameters | None = None,
    latent_overrides: Mapping[str, float] | None = None,
) -> GeneratorBridgeInput:
    """Translate a causal structure into generator-ready inputs.

    Later full simulations should use this object to decide how pathway switches
    modify outcrossing probability, selfing probability, guide benefit, fitness,
    inheritance, drift, and next-generation trait states.
    """

    params = base_parameters or ModelParameters()
    overrides = dict(latent_overrides or {})
    return GeneratorBridgeInput(
        structure_name=structure.name,
        switches=switches_for_structure(structure.name),
        parameters=apply_latent_overrides(params, overrides),
        latent_overrides=overrides,
        notes=(
            "Bridge object only; full stochastic reproduction and inheritance "
            "will be connected after the biological generator stabilizes."
        ),
    )


def apply_latent_overrides(
    parameters: ModelParameters,
    latent_overrides: Mapping[str, float],
) -> ModelParameters:
    """Apply latent parameter overrides where names match ModelParameters fields."""

    updated = ModelParameters(**parameters.__dict__)
    for name, value in latent_overrides.items():
        if hasattr(updated, name):
            setattr(updated, name, float(value))
    return updated
