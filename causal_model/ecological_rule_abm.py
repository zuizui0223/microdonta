"""Abstract ecological-evolutionary ABM backend for Rule-Transition RACH.

The model is deliberately role-based rather than taxon-specific.  It represents
an interaction channel, an alternative persistence/reproduction route, population
constraint, and trait investment.  After a sustained loss of the interaction
relation, different causal programs reconfigure those relations differently.

Each program does not just report a trait decline; it returns the structural
**rule transition** as an ordered three-stage chain

    relation change  ->  constraint reconfiguration  ->  trait-space reconfiguration

so the invariant layer can ask which stage motifs are necessary across robust
programs. ``relation_change`` is the loss of the interaction relation;
``constraint_reconfiguration`` is the program-specific way the surviving
constraints are rewired (selection / reproductive / demographic); and
``trait_space_reconfiguration`` is the resulting shift of the admissible trait
space.

This is not a claim that one numerical simulation proves a rule.  It produces
parameter-sweep ``SweepRecord``s (carrying region id, seed, and any fragility
flags) for the robust/fragile layer in :mod:`causal_model.abm_family_adapter`.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Iterable

from causal_model.abm_family_adapter import SweepRecord


#: The ordered rule-transition chain every program returns.
RULE_TRANSITION_CHAIN: tuple[str, str, str] = (
    "relation_change",
    "constraint_reconfiguration",
    "trait_space_reconfiguration",
)

#: Program-specific constraint-reconfiguration motif (the middle chain stage).
_CONSTRAINT_MOTIF: dict[str, str] = {
    "direct_selection": "selection_reconfiguration",
    "reproductive_reconfiguration": "reproductive_reconfiguration",
    "demographic_reconfiguration": "demographic_reconfiguration",
    # A deliberately fragile program: it reproduces the trait decline only
    # through an exact cancellation of opposing routes, so its match is flagged
    # and can never earn a robust verdict (see DISQUALIFYING_FRAGILITY_FLAGS).
    "knife_edge_cancellation": "selection_reconfiguration",
}

#: Fragility flags a program's records always carry (boundary / cancellation).
_PROGRAM_FRAGILITY: dict[str, frozenset[str]] = {
    "knife_edge_cancellation": frozenset({"exact_cancellation"}),
}


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


@dataclass(frozen=True)
class RuleTransitionChain:
    """The ordered structural transition a program embodies after relation loss."""

    relation_change: str
    constraint_reconfiguration: str
    trait_space_reconfiguration: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.relation_change, self.constraint_reconfiguration, self.trait_space_reconfiguration)


def rule_transition_chain(program_id: str) -> RuleTransitionChain:
    """Return the relation -> constraint -> trait-space chain for a program."""
    if program_id not in _CONSTRAINT_MOTIF:
        raise ValueError(f"Unknown program_id: {program_id}")
    return RuleTransitionChain(
        relation_change="relation_change",
        constraint_reconfiguration=_CONSTRAINT_MOTIF[program_id],
        trait_space_reconfiguration="trait_space_reconfiguration",
    )


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
    - ``knife_edge_cancellation``: reproduces the decline only through an exact
      cancellation of opposing routes (a fragile explanation).

    All programs begin with a functioning interaction channel and then experience
    a sustained loss. The returned motifs encode the structural transition as the
    ordered chain ``relation_change -> constraint_reconfiguration ->
    trait_space_reconfiguration`` plus the program-specific reconfiguration; they
    are NOT a fitted causal truth.
    """

    if program_id not in _CONSTRAINT_MOTIF:
        raise ValueError(f"Unknown program_id: {program_id}")

    rng = Random(seed)
    before = EcologicalRuleState(1.0, 0.0, 1.0, 0.75)
    state = before
    # Stage 1 of the chain: the interaction relation is being lost.
    motifs = {"interaction_loss", "relation_change", "selection_reconfiguration"}

    for _ in range(steps):
        interaction = _clip(state.interaction_opportunity - 1.0 / steps)
        alternative = state.alternative_route
        persistence = state.population_persistence
        trait_benefit = params.interaction_benefit * interaction

        if program_id in ("direct_selection", "knife_edge_cancellation"):
            pass  # interaction loss reduces trait benefit directly
        elif program_id == "reproductive_reconfiguration":
            alternative = _clip(alternative + params.alternative_route_strength * (1.0 - interaction) / steps)
            trait_benefit *= 1.0 - alternative
        elif program_id == "demographic_reconfiguration":
            persistence = _clip(persistence - params.demographic_pressure * (1.0 - interaction) / steps)
            trait_benefit *= persistence

        # Stage 2: the surviving constraints are reconfigured (program-specific).
        motifs.add("constraint_reconfiguration")
        motifs.add(_CONSTRAINT_MOTIF[program_id])
        motifs |= _PROGRAM_FRAGILITY.get(program_id, frozenset())

        noise = rng.uniform(-params.noise_scale, params.noise_scale)
        target = _clip((trait_benefit - params.trait_cost + 1.0) / 2.0)
        trait = _clip(state.trait_investment + params.adaptation_rate * (target - state.trait_investment) + noise)
        state = EcologicalRuleState(interaction, alternative, persistence, trait)

    # Stage 3: the admissible trait space has shifted.
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
    """Generate RACH-compatible records from an abstract parameter sweep.

    Each draw is treated as a distinct declared region (``region_id``) with its
    own ``seed``, and any program-level fragility (e.g. exact cancellation) is
    attached as ``fragile_flags`` so the adapter can record *why* a match would
    be fragile.
    """
    records: list[SweepRecord] = []
    draws = tuple(parameter_draws)
    for program_id in program_ids:
        fragile_flags = _PROGRAM_FRAGILITY.get(program_id, frozenset())
        for index, params in enumerate(draws):
            before, after, motifs = simulate_rule_transition(program_id, params, steps=steps, seed=index)
            region_id = f"{region_prefix}_{index}"
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
                metadata={"region_id": region_id},
                region_id=region_id,
                seed=index,
                fragile_flags=fragile_flags,
            ))
    return tuple(records)
