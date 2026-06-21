"""Abstract ecological-evolutionary ABM backend for Rule-Transition RACH.

The model is deliberately role-based rather than taxon-specific.  It represents
an interaction channel, an alternative persistence/reproduction route, population
constraint, and trait investment.  Different causal programs reconfigure those
relations differently after interaction loss.

This is not a claim that one numerical simulation proves a rule.  It produces
parameter-sweep `SweepRecord`s for the robust/fragile layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Iterable

from causal_model.abm_family_adapter import SweepRecord


@dataclass(frozen=True)
class EcologicalRuleParameters:
    """One admissible draw for an abstract ecological-evolutionary system."""

    interaction_benefit: float
    alternative_route_strength: float
    demographic_pressure: float
    trait_cost: float
    adaptation_rate: float
    noise_scale: float


@dataclass(frozen=True)
class EcologicalRuleState:
    interaction_opportunity: float
    alternative_route: float
    population_persistence: float
    trait_investment: float


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def simulate_rule_transition(
    program_id: str,
    params: EcologicalRuleParameters,
    *,
    steps: int = 40,
    seed: int = 0,
) -> tuple[EcologicalRuleState, EcologicalRuleState, frozenset[str]]:
    """Simulate one relationship-loss transition under an abstract program.

    Programs:
    - ``direct_selection``: interaction loss directly reduces trait benefit.
    - ``reproductive_reconfiguration``: interaction loss opens an alternative
      route; trait investment becomes less beneficial indirectly.
    - ``demographic_reconfiguration``: interaction loss changes persistence and
      amplifies demographic constraint on trait investment.

    All programs begin with a functioning interaction channel and then experience
    a sustained loss. Returned motifs describe the *structural transition*, not a
    fitted causal truth.
    """

    rng = Random(seed)
    before = EcologicalRuleState(1.0, 0.0, 1.0, 0.75)
    state = before
    motifs = {"interaction_loss"}

    for _ in range(steps):
        interaction = _clip(state.interaction_opportunity - 1.0 / steps)
        alternative = state.alternative_route
        persistence = state.population_persistence
        trait_benefit = params.interaction_benefit * interaction

        if program_id == "direct_selection":
            motifs.add("selection_reconfiguration")
        elif program_id == "reproductive_reconfiguration":
            alternative = _clip(alternative + params.alternative_route_strength * (1.0 - interaction) / steps)
            trait_benefit *= 1.0 - alternative
            motifs.update({"reproductive_reconfiguration", "selection_reconfiguration"})
        elif program_id == "demographic_reconfiguration":
            persistence = _clip(persistence - params.demographic_pressure * (1.0 - interaction) / steps)
            trait_benefit *= persistence
            motifs.update({"demographic_reconfiguration", "selection_reconfiguration"})
        else:
            raise ValueError(f"Unknown program_id: {program_id}")

        noise = rng.uniform(-params.noise_scale, params.noise_scale)
        target = _clip((trait_benefit - params.trait_cost + 1.0) / 2.0)
        trait = _clip(state.trait_investment + params.adaptation_rate * (target - state.trait_investment) + noise)
        state = EcologicalRuleState(interaction, alternative, persistence, trait)

    motifs.add("trait_space_reconfiguration")
    return before, state, frozenset(motifs)


def ordinal_trait_decline(before: EcologicalRuleState, after: EcologicalRuleState, *, tolerance: float = 0.08) -> bool:
    """Target qualitative pattern used by the MVP: sustained trait decline."""
    return after.trait_investment < before.trait_investment - tolerance


def generate_sweep_records(
    scenario: str,
    program_ids: Iterable[str],
    parameter_draws: Iterable[EcologicalRuleParameters],
    *,
    region_prefix: str = "draw",
    steps: int = 40,
) -> tuple[SweepRecord, ...]:
    """Generate RACH-compatible records from an abstract parameter sweep."""
    records: list[SweepRecord] = []
    draws = tuple(parameter_draws)
    for program_id in program_ids:
        for index, params in enumerate(draws):
            before, after, motifs = simulate_rule_transition(program_id, params, steps=steps, seed=index)
            records.append(SweepRecord(
                scenario=scenario,
                program_id=program_id,
                motifs=motifs,
                pattern_matched=ordinal_trait_decline(before, after),
                parameters={
                    "interaction_benefit": params.interaction_benefit,
                    "alternative_route_strength": params.alternative_route_strength,
                    "demographic_pressure": params.demographic_pressure,
                    "trait_cost": params.trait_cost,
                    "adaptation_rate": params.adaptation_rate,
                    "noise_scale": params.noise_scale,
                },
                initial_state={"trait_investment": before.trait_investment},
                metadata={"region_id": f"{region_prefix}_{index}"},
            ))
    return tuple(records)
