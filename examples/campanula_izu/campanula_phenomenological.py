"""Campanula Izu: phenomenological model for causal structure comparison.

Wraps the generic causal_model.phenomenological_model functions with
campanula-specific default environments. Kept in examples/campanula_izu/
to leave causal_model/ general-purpose.

The term "phenomenological" reflects that this model directly encodes
theoretical causal relationships between environmental variables and
trait values — it is a theory-encoding model, not a mechanistic simulation
acting as a proxy for the ABM.

Entry points
------------
simulate_campanula_causal_structure(structure, ...)
    Original function. Accepts a pre-defined CausalStructure (M1–M5).
    Switches default to the structure's canonical pathway configuration.

simulate_campanula_with_switches(switches, ...)
    New function for switch posterior inference.
    Accepts an explicit PathwaySwitches object; no CausalStructure required.
    Used by causal_model.switch_inference.

simulate_campanula_gradient(switches, ...)
    Multi-population gradient simulation.
    Runs all four populations (mainland, Oshima, Kozushima, Hachijo) and
    returns outputs keyed by population name.

environments_from_population_env(env_table)
    Convert an ecological_context.csv dict (from observed_data.load_ecological_context)
    into {population_name: Environment} for gradient simulation.
"""

from __future__ import annotations

import math

from attraction_trait_model import Environment, ModelParameters
from causal_model.phenomenological_model import (
    PhenomenologicalOutput,
    predict_traits_phenomenological,
    relations_from_outputs,
)
from causal_model.structures import CausalStructure
from causal_model.switches import PathwaySwitches, switches_for_structure


def default_campanula_environments() -> dict[str, Environment]:
    """Return provisional Oshima / Hachijo environments for causal comparison."""

    return {
        "Oshima": Environment(
            name="Oshima",
            primary_pollinator_frequency=0.35,
            background_pollinator_frequency=0.55,
            community_pollinator_abundance=0.62,
            migration_rate=0.05,
            island_distance=0.35,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
        "Hachijo": Environment(
            name="Hachijo",
            primary_pollinator_frequency=0.00,
            background_pollinator_frequency=0.72,
            community_pollinator_abundance=0.34,
            migration_rate=0.01,
            island_distance=0.90,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
    }


def simulate_campanula_causal_structure(
    structure: CausalStructure,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
    switches: PathwaySwitches | None = None,
) -> tuple[dict[str, str], list[PhenomenologicalOutput]]:
    """Generate Oshima/Hachijo pattern relations for one pre-defined causal structure.

    Parameters
    ----------
    structure:
        One of the M1–M5 CausalStructure objects.  Used to look up default
        pathway switches when ``switches`` is None.
    params:
        Latent ecological parameters.  Defaults to ModelParameters defaults.
    environments:
        Population environments.  Defaults to Oshima / Hachijo defaults.
    switches:
        Explicit pathway switches.  If None, derived from ``structure.name``.
    """

    params = params or ModelParameters()
    environments = environments or default_campanula_environments()
    switches = switches or switches_for_structure(structure.name)
    outputs = [
        predict_traits_phenomenological(structure, env, params, switches=switches)
        for env in environments.values()
    ]
    relations = relations_from_outputs(outputs, left="Oshima", right="Hachijo")
    return relations, outputs


def simulate_campanula_with_switches(
    switches: PathwaySwitches,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
) -> tuple[dict[str, str], list[PhenomenologicalOutput]]:
    """Generate Oshima/Hachijo pattern relations for an explicit switch state.

    This is the entry point for switch posterior inference.  No pre-defined
    CausalStructure is required — the switches fully specify the biological
    pathways that are active in this simulation run.

    Parameters
    ----------
    switches:
        Explicit :class:`PathwaySwitches` object specifying pathway weights.
        Created by :func:`causal_model.switch_inference.pathway_switches_from_state`.
    params:
        Latent ecological parameters.  Defaults to ModelParameters defaults.
    environments:
        Population environments.  Defaults to Oshima / Hachijo defaults.

    Returns
    -------
    tuple
        (relations_dict, outputs_list)
        ``relations_dict`` maps pattern names to ordinal relation strings
        (e.g. ``"Oshima > Hachijo"``).
    """

    params = params or ModelParameters()
    environments = environments or default_campanula_environments()

    # Create a minimal placeholder structure.  Its name is never used because
    # switches are passed explicitly; we only need a valid object type.
    _placeholder = CausalStructure(
        name="switch_inference",
        description="Switch posterior inference — no fixed structure",
        edges=[],
        expected_patterns=[],
        latent_parameters=[],
    )

    outputs = [
        predict_traits_phenomenological(_placeholder, env, params, switches=switches)
        for env in environments.values()
    ]
    relations = relations_from_outputs(outputs, left="Oshima", right="Hachijo")
    return relations, outputs


# ---------------------------------------------------------------------------
# Multi-population gradient simulation (Tasks 5-6)
# ---------------------------------------------------------------------------

def environments_from_population_env(
    env_table: dict[str, dict],
) -> dict[str, Environment]:
    """Convert ecological_context.csv data into Environment objects.

    Parameters
    ----------
    env_table:
        Dict returned by observed_data.load_ecological_context().
        Keys are population names; values are dicts with numeric columns.

    Returns
    -------
    dict
        {population_name: Environment} in CSV row order.
    """
    result: dict[str, Environment] = {}
    for pop_name, row in env_table.items():
        result[pop_name] = Environment(
            name=pop_name,
            primary_pollinator_frequency=float(row.get("primary_pollinator_frequency", 0.0)),
            background_pollinator_frequency=float(row.get("background_pollinator_frequency", 0.5)),
            community_pollinator_abundance=float(row.get("community_pollinator_abundance", 0.5)),
            migration_rate=float(row.get("migration_rate", 0.05)),
            island_distance=float(row.get("isolation", 0.0)),
            # effective_population_size derived from island_distance by Environment.__post_init__
            # (effective_population_size_proxy from CSV is intentionally ignored to avoid
            #  double-counting Ne: Ne is a consequence of isolation, not independent)
        )
    return result


def default_campanula_gradient_environments() -> dict[str, Environment]:
    """Return default mainland / Oshima / Kozushima / Hachijo environments."""
    return {
        "mainland": Environment(
            name="mainland",
            primary_pollinator_frequency=0.80,
            background_pollinator_frequency=0.50,
            community_pollinator_abundance=0.88,
            migration_rate=0.15,
            island_distance=0.00,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
        "Oshima": Environment(
            name="Oshima",
            primary_pollinator_frequency=0.45,
            background_pollinator_frequency=0.50,
            community_pollinator_abundance=0.62,
            migration_rate=0.05,
            island_distance=0.35,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
        "Kozushima": Environment(
            name="Kozushima",
            primary_pollinator_frequency=0.20,
            background_pollinator_frequency=0.55,
            community_pollinator_abundance=0.44,
            migration_rate=0.02,
            island_distance=0.60,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
        "Hachijo": Environment(
            name="Hachijo",
            primary_pollinator_frequency=0.00,
            background_pollinator_frequency=0.60,
            community_pollinator_abundance=0.34,
            migration_rate=0.01,
            island_distance=0.85,
            # effective_population_size derived from island_distance by Environment.__post_init__
        ),
    }


def simulate_campanula_gradient(
    switches: PathwaySwitches,
    params: ModelParameters | None = None,
    environments: dict[str, Environment] | None = None,
) -> dict[str, PhenomenologicalOutput]:
    """Simulate all gradient populations and return outputs by population name.

    Parameters
    ----------
    switches:
        PathwaySwitches specifying which pathways are active.
    params:
        Latent ecological parameters. Defaults to ModelParameters defaults.
    environments:
        {population_name: Environment}. Defaults to four-population gradient.

    Returns
    -------
    dict
        {population_name: PhenomenologicalOutput} in population order.
    """
    params = params or ModelParameters()
    environments = environments or default_campanula_gradient_environments()

    _placeholder = CausalStructure(
        name="gradient_inference",
        description="Multi-population gradient simulation",
        edges=[],
        expected_patterns=[],
        latent_parameters=[],
    )

    return {
        pop_name: predict_traits_phenomenological(
            _placeholder, env, params, switches=switches
        )
        for pop_name, env in environments.items()
    }


# ---------------------------------------------------------------------------
# Continuous isolation gradient — no named populations
# ---------------------------------------------------------------------------

def env_from_isolation(
    isolation: float,
    ne_isolation_slope: float = 0.765,
    migration_decay_rate: float = 3.19,
    pollinator_loss_slope: float = 0.94,
) -> Environment:
    """Derive an Environment purely from isolation distance in [0, 1].

    All other environmental variables are estimated from the four Izu Island
    populations (mainland, Oshima, Kozushima, Hachijo) via linear regression
    on isolation, except migration_rate (exponential decay).

    Fitted from population_env.csv (defaults = Izu Island fitted values):
        Bombus_frequency      = max(0, 0.80 − pollinator_loss_slope * iso)  R²≈0.99
        community_pollinator_abundance = 0.88 − 0.635 * iso                 R²≈0.97
        background_pollinator_frequency = 0.50 + 0.118 * iso                R²≈0.88
        migration_rate        = 0.15 * exp(−migration_decay_rate * iso)      R²≈0.99
        effective_population_size = 1.00 − ne_isolation_slope * iso          R²≈0.93

    Epistemic taxonomy of coefficients
    -----------------------------------
    DIRECTION (普遍的原理): all directional signs are fixed (Bombus decreases,
        Ne decreases, migration decreases, background pollinators increase with
        isolation). Only the magnitudes are uncertain.

    SLOPES (推論対象 θ): ne_isolation_slope, migration_decay_rate,
        pollinator_loss_slope are latent parameters sampled from prior
        distributions and inferred via ABC. The defaults are Izu-fitted values
        and serve as prior centres, not known constants.

    Parameters
    ----------
    isolation:
        Normalised isolation distance from mainland in [0, 1].
        0 = mainland, 1 = maximally isolated island.
    ne_isolation_slope:
        θ: slope of Ne decline with isolation. Default 0.765 (Izu fit R²=0.93).
    migration_decay_rate:
        θ: exponential decay rate of migration with isolation.
        Default 3.19 (Izu fit R²=0.99).
    pollinator_loss_slope:
        θ: slope of Bombus frequency decline with isolation.
        Default 0.94 (Izu fit R²=0.99).
    """
    iso = float(max(0.0, min(1.0, isolation)))
    return Environment(
        name=f"iso_{iso:.3f}",
        primary_pollinator_frequency=max(0.0, 0.80 - pollinator_loss_slope * iso),
        background_pollinator_frequency=min(1.0, 0.50 + 0.118 * iso),
        community_pollinator_abundance=max(0.0, 0.88 - 0.635 * iso),
        migration_rate=0.15 * math.exp(-migration_decay_rate * iso),
        island_distance=iso,
        ne_isolation_slope=ne_isolation_slope,
        # effective_population_size derived from island_distance and
        # ne_isolation_slope by Environment.__post_init__
    )


def simulate_campanula_isolation_gradient(
    switches: PathwaySwitches,
    params: ModelParameters | None = None,
    n_points: int = 8,
    isolation_range: tuple[float, float] = (0.0, 1.0),
    ne_isolation_slope: float = 0.765,
    migration_decay_rate: float = 3.19,
    pollinator_loss_slope: float = 0.94,
) -> tuple[dict[str, PhenomenologicalOutput], dict[str, dict]]:
    """Simulate a continuous isolation gradient without named populations.

    Generates ``n_points`` environments parameterised purely by isolation
    distance.  All other environmental variables are derived from isolation
    via empirically-fitted functions (see :func:`env_from_isolation`).

    Parameters
    ----------
    switches:
        PathwaySwitches specifying which pathways are active.
    params:
        Latent ecological parameters (benefit/cost parameters θ).
        Defaults to ModelParameters defaults.
    n_points:
        Number of evenly-spaced isolation points. Default 8.
    isolation_range:
        (min_iso, max_iso) spanning the gradient. Default (0.0, 1.0).
    ne_isolation_slope:
        θ: slope of Ne decline with isolation. Passed to env_from_isolation.
    migration_decay_rate:
        θ: exponential decay rate of migration with isolation.
    pollinator_loss_slope:
        θ: slope of Bombus frequency decline with isolation.

    Returns
    -------
    (outputs_dict, synth_pop_env)
        outputs_dict:
            {pop_name: PhenomenologicalOutput} keyed by ``"iso_X.XXX"``.
        synth_pop_env:
            Synthetic population-environment table in the same format as
            ``load_population_env()`` output.  Used as ``env_table`` argument
            to :func:`pattern_evaluator.evaluate_patterns`.
            Each entry contains ``isolation``, ``distance_from_mainland``
            (= isolation × 290 km, for predictor lookups in POM), and the
            derived environmental variables.
    """
    params = params or ModelParameters()
    lo, hi = isolation_range
    if n_points < 2:
        iso_values = [lo]
    else:
        step = (hi - lo) / (n_points - 1)
        iso_values = [lo + step * i for i in range(n_points)]

    _placeholder = CausalStructure(
        name="isolation_gradient_inference",
        description="Continuous isolation gradient — population-free",
        edges=[],
        expected_patterns=[],
        latent_parameters=[],
    )

    outputs_dict: dict[str, PhenomenologicalOutput] = {}
    synth_pop_env: dict[str, dict] = {}

    for iso in iso_values:
        env = env_from_isolation(
            iso,
            ne_isolation_slope=ne_isolation_slope,
            migration_decay_rate=migration_decay_rate,
            pollinator_loss_slope=pollinator_loss_slope,
        )
        output = predict_traits_phenomenological(_placeholder, env, params, switches=switches)
        outputs_dict[env.name] = output
        synth_pop_env[env.name] = {
            "isolation": iso,
            # distance_from_mainland in km (Izu max ≈ 290 km)
            # used by gradient_slope pattern predictor lookup
            "distance_from_mainland": round(iso * 290.0, 1),
            "Bombus_frequency": env.primary_pollinator_frequency,
            "background_pollinator_frequency": env.background_pollinator_frequency,
            "community_pollinator_abundance": env.community_pollinator_abundance,
            "migration_rate": env.migration_rate,
            "effective_population_size_proxy": env.effective_population_size,
        }

    return outputs_dict, synth_pop_env
