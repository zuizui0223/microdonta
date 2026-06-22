"""Peer-review diagnostics for the spatial metapopulation rule-transition backend.

These functions exist to pre-empt the obvious reviewer objections to the headline
claim ("losing the trait-supporting relationship robustly contracts trait space"):

* **Channel decomposition** (:func:`decompose_channels`). Each intervention drops
  *two* things at once — the trait-supporting interaction AND a secondary channel
  (predation or dispersal). A reviewer will ask which one drives the contraction.
  This isolates them: full vs interaction-only vs secondary-only. It shows the
  interaction (trait-support) loss is the necessary driver, that predator removal
  *alone* does not contract trait space (a clean dissociation), and that dispersal
  loss is a *separate* spatial route to contraction.

* **Threshold sensitivity** (:func:`threshold_sensitivity`). Re-classifies a single
  collected sweep across a grid of acceptance tolerances ``epsilon`` and
  contraction tolerances, so the constrained-vs-compensated separation is shown not
  to be an artefact of one threshold choice.

* **Replicate convergence** (:func:`replicate_convergence`) and **seed spread**
  (:func:`seed_spread`) characterise the Monte-Carlo noise in the invasion-fitness
  estimate, so "your result is seed-dependent" can be answered with numbers.

All of these reuse :func:`run_intervention_experiment` and re-classify its stored
``Omega_inv`` sets, so threshold sweeps cost no extra simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Callable

from causal_model.abc_distance import accepted_by_epsilon
from causal_model.spatial_metapopulation_abm import (
    DEFAULT_EPSILON,
    Intervention,
    InterventionResult,
    MetapopParameters,
    Regime,
    classify_trait_space_change,
    make_interventions,
    run_intervention_experiment,
    sample_compensated_ecosystem,
    sample_constrained_ecosystem,
)

EcosystemSampler = Callable[[Random], tuple[MetapopParameters, dict]]


# ---------------------------------------------------------------------------
# Collecting a sweep once (so threshold sweeps need no extra simulation)
# ---------------------------------------------------------------------------

def collect_results(
    intervention: Intervention,
    ecosystem_sampler: EcosystemSampler,
    *,
    n_draws: int = 16,
    base_seed: int = 0,
    **experiment_kwargs,
) -> list[InterventionResult]:
    """Run ``n_draws`` random-ecosystem experiments and return their results."""
    out: list[InterventionResult] = []
    for i in range(n_draws):
        rng = Random(base_seed * 1213 + i)
        params, patches = ecosystem_sampler(rng)
        out.append(run_intervention_experiment(
            params, patches, intervention, seed=base_seed * 1213 + i, **experiment_kwargs,
        ))
    return out


def _stationary(results: list[InterventionResult]) -> list[InterventionResult]:
    return [r for r in results if r.stationarity == "stationary"]


def contraction_fraction_at(
    results: list[InterventionResult],
    *,
    contraction_rel_tol: float = 0.15,
    shift_tol: float = 0.12,
) -> float:
    """Fraction of stationary runs whose Omega_inv contracts at the given tolerance."""
    stat = _stationary(results)
    if not stat:
        return 0.0
    n = 0
    for r in stat:
        ts = classify_trait_space_change(
            r.omega_before, r.omega_after,
            contraction_rel_tol=contraction_rel_tol, shift_tol=shift_tol,
        )
        n += int(ts.contracted)
    return n / len(stat)


def acceptance_fraction_at(
    results: list[InterventionResult],
    *,
    epsilon: float = DEFAULT_EPSILON,
    contraction_rel_tol: float = 0.15,
    shift_tol: float = 0.12,
) -> float:
    """Fraction accepted: d(P_sim,P_obs) <= epsilon AND Omega_inv contracted."""
    stat = _stationary(results)
    if not stat:
        return 0.0
    n = 0
    for r in stat:
        ts = classify_trait_space_change(
            r.omega_before, r.omega_after,
            contraction_rel_tol=contraction_rel_tol, shift_tol=shift_tol,
        )
        if accepted_by_epsilon(r.distance, epsilon) and ts.contracted:
            n += 1
    return n / len(stat)


# ---------------------------------------------------------------------------
# Channel decomposition (the central causal-isolation control)
# ---------------------------------------------------------------------------

def channel_variants(intervention: Intervention, *, compensation: float = 0.08) -> dict[str, Intervention]:
    """Split an intervention into full / interaction-only / secondary-only variants.

    * ``full``             — the intervention as defined (trait-support loss + the
      secondary channel toggle).
    * ``interaction_only`` — only the trait-supporting interaction is lost; any
      secondary channel (predation, dispersal) is held intact.
    * ``secondary_only``   — the interaction is held intact; only the secondary
      channel is toggled (predator removed / dispersal cut).

    Comparing the three isolates whether contraction is driven by losing the
    trait-supporting relationship or by the secondary disturbance.
    """
    after = intervention.after
    motif = intervention.channel_motif
    name = intervention.name

    interaction_only_after = Regime(
        interaction_scale=after.interaction_scale,
        predation_scale=1.0, dispersal_scale=1.0,
        repro_baseline=compensation,
    )
    secondary_only_after = Regime(
        interaction_scale=1.0,
        predation_scale=after.predation_scale,
        dispersal_scale=after.dispersal_scale,
        repro_baseline=0.0,
    )
    return {
        "full": intervention,
        "interaction_only": Intervention(name, Regime(), interaction_only_after, motif),
        "secondary_only": Intervention(name, Regime(), secondary_only_after, motif),
    }


@dataclass(frozen=True)
class ChannelDecomposition:
    intervention: str
    full: float
    interaction_only: float
    secondary_only: float

    @property
    def interaction_is_driver(self) -> bool:
        """Interaction loss contracts substantially more than the secondary channel."""
        return self.interaction_only >= self.secondary_only + 0.25


def decompose_channels(
    intervention: Intervention,
    *,
    ecosystem_sampler: EcosystemSampler | None = None,
    n_draws: int = 16,
    base_seed: int = 100,
    compensation: float = 0.08,
    **experiment_kwargs,
) -> ChannelDecomposition:
    """Contraction fraction under full / interaction-only / secondary-only loss."""
    sampler = ecosystem_sampler or sample_constrained_ecosystem
    variants = channel_variants(intervention, compensation=compensation)
    fracs = {}
    for key, intv in variants.items():
        results = collect_results(intv, sampler, n_draws=n_draws, base_seed=base_seed, **experiment_kwargs)
        fracs[key] = contraction_fraction_at(results)
    return ChannelDecomposition(
        intervention=intervention.name,
        full=fracs["full"],
        interaction_only=fracs["interaction_only"],
        secondary_only=fracs["secondary_only"],
    )


# ---------------------------------------------------------------------------
# Threshold sensitivity (epsilon and contraction tolerance)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ThresholdSensitivity:
    epsilons: tuple[float, ...]
    contraction_tols: tuple[float, ...]
    constrained_grid: tuple[tuple[float, ...], ...]   # [eps][tol] acceptance fraction
    compensated_grid: tuple[tuple[float, ...], ...]
    min_separation: float                             # min(constrained - compensated)

    @property
    def separation_holds(self) -> bool:
        """Constrained is admitted more than the compensated counterexample everywhere."""
        return self.min_separation > 0.0


def threshold_sensitivity(
    intervention_constrained: Intervention,
    intervention_compensated: Intervention,
    *,
    n_draws: int = 16,
    base_seed: int = 100,
    epsilons: tuple[float, ...] = (0.0, 0.2, 0.4),
    contraction_tols: tuple[float, ...] = (0.10, 0.15, 0.25),
    **experiment_kwargs,
) -> ThresholdSensitivity:
    """Show the constrained/compensated separation survives threshold choices.

    A single sweep is collected per ensemble and re-classified across the
    ``epsilon`` x ``contraction_tol`` grid, so no extra simulation is needed.
    """
    constrained = collect_results(
        intervention_constrained, sample_constrained_ecosystem,
        n_draws=n_draws, base_seed=base_seed, **experiment_kwargs,
    )
    compensated = collect_results(
        intervention_compensated, sample_compensated_ecosystem,
        n_draws=n_draws, base_seed=base_seed, **experiment_kwargs,
    )
    cons_grid = []
    comp_grid = []
    min_sep = 1.0
    for eps in epsilons:
        cons_row = []
        comp_row = []
        for tol in contraction_tols:
            c = acceptance_fraction_at(constrained, epsilon=eps, contraction_rel_tol=tol)
            k = acceptance_fraction_at(compensated, epsilon=eps, contraction_rel_tol=tol)
            cons_row.append(c)
            comp_row.append(k)
            min_sep = min(min_sep, c - k)
        cons_grid.append(tuple(cons_row))
        comp_grid.append(tuple(comp_row))
    return ThresholdSensitivity(
        epsilons=tuple(epsilons),
        contraction_tols=tuple(contraction_tols),
        constrained_grid=tuple(cons_grid),
        compensated_grid=tuple(comp_grid),
        min_separation=min_sep,
    )


# ---------------------------------------------------------------------------
# Monte-Carlo characterisation: replicate convergence and seed spread
# ---------------------------------------------------------------------------

def replicate_convergence(
    intervention: Intervention,
    *,
    ecosystem_sampler: EcosystemSampler | None = None,
    replicate_grid: tuple[int, ...] = (1, 2, 4),
    n_draws: int = 14,
    base_seed: int = 100,
    **experiment_kwargs,
) -> dict[int, float]:
    """Contraction fraction as a function of the number of invasion replicates."""
    sampler = ecosystem_sampler or sample_constrained_ecosystem
    experiment_kwargs.pop("invasion_replicates", None)
    out: dict[int, float] = {}
    for reps in replicate_grid:
        results = collect_results(
            intervention, sampler, n_draws=n_draws, base_seed=base_seed,
            invasion_replicates=reps, **experiment_kwargs,
        )
        out[reps] = contraction_fraction_at(results)
    return out


@dataclass(frozen=True)
class SeedSpread:
    fractions: tuple[float, ...]

    @property
    def mean(self) -> float:
        return sum(self.fractions) / len(self.fractions) if self.fractions else 0.0

    @property
    def lo(self) -> float:
        return min(self.fractions) if self.fractions else 0.0

    @property
    def hi(self) -> float:
        return max(self.fractions) if self.fractions else 0.0


def seed_spread(
    intervention: Intervention,
    *,
    ecosystem_sampler: EcosystemSampler | None = None,
    base_seeds: tuple[int, ...] = (11, 23, 42, 67, 100),
    n_draws: int = 14,
    **experiment_kwargs,
) -> SeedSpread:
    """Contraction fraction across several independent base seeds (min/mean/max)."""
    sampler = ecosystem_sampler or sample_constrained_ecosystem
    fracs = []
    for bs in base_seeds:
        results = collect_results(intervention, sampler, n_draws=n_draws, base_seed=bs, **experiment_kwargs)
        fracs.append(contraction_fraction_at(results))
    return SeedSpread(fractions=tuple(fracs))


# ---------------------------------------------------------------------------
# One-call report
# ---------------------------------------------------------------------------

def run_peer_review_panel(**experiment_kwargs) -> dict:
    """Run the full diagnostic panel and return a JSON-serialisable summary."""
    incomplete = make_interventions(compensation=0.08)
    sufficient = make_interventions(compensation=0.55)
    panel: dict = {"channel_decomposition": {}, "threshold_separation": {}, "seed_spread": {}}
    for name in incomplete:
        dec = decompose_channels(incomplete[name], n_draws=14, base_seed=100, **experiment_kwargs)
        panel["channel_decomposition"][name] = {
            "full": dec.full, "interaction_only": dec.interaction_only,
            "secondary_only": dec.secondary_only, "interaction_is_driver": dec.interaction_is_driver,
        }
        ts = threshold_sensitivity(
            incomplete[name], sufficient[name], n_draws=12, base_seed=100, **experiment_kwargs,
        )
        panel["threshold_separation"][name] = {
            "min_separation": ts.min_separation, "separation_holds": ts.separation_holds,
        }
        ss = seed_spread(incomplete[name], base_seeds=(11, 42, 100), n_draws=12, **experiment_kwargs)
        panel["seed_spread"][name] = {"mean": ss.mean, "lo": ss.lo, "hi": ss.hi}
    return panel
