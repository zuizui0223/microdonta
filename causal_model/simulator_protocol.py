"""Generic simulator protocol for RACH inference.

RACH (Rejection ABC for Causal Hypotheses) requires a simulator
f(θ, s) that maps latent parameters θ and switch state s to
simulated observations y_sim:

    A_ε = {(θ,s) ∈ Θ×{0,1}^K : d(f(θ,s), y_obs) ≤ ε}

This module defines the minimal interface (protocol) that any
simulator must satisfy to be used as f(θ,s) in RACH inference.
Concrete implementations live in the system-specific examples/ directory.

Generality
----------
RACH is not tied to any particular biological system.  To apply it to
a new system (e.g. coral reef fish, forest trees, microbial evolution),
implement ``SimulatorProtocol`` with your own forward model:

    1. Define your environment class (analogous to Environment).
    2. Define your parameter class (analogous to ModelParameters).
    3. Define your switch state (analogous to PathwaySwitches).
    4. Implement a callable that satisfies ``SimulatorProtocol``.
    5. Plug it into ``switch_inference.run_switch_posterior_inference_abm``
       or the equivalent RACH loop.

The framework (causal_model/) provides:
    - ABC distance functions (abc_distance.py)
    - Switch posterior computation (switch_inference.py)
    - Parameter sampling and constraint checking (parameter_sampling.py,
      parameter_constraints.py)
    - Pattern evaluation (via examples/; can be re-used as a template)

What makes a simulator valid for RACH
--------------------------------------
A simulator f IS valid if:
    * It generates simulated data y_sim from (θ, s) via mechanistic rules
      (e.g. individual-level selection, drift, reproduction)
    * Switch effects are EMERGENT consequences of those rules, not
      hand-coded functional relationships
    * The same simulator f is used consistently throughout the inference

A simulator f is NOT valid if:
    * It uses hand-coded formulas of the form
      ``y_sim[guide] += w * bombus * benefit``
      because these encode researcher assumptions, making the posterior
      P(S|A_ε) reflect those assumptions rather than the data
    * Different backends are used for screening vs inference (they define
      different A_ε and thus different posteriors)

The stochastic ABM in ``attraction_trait_model/simulation.py`` is the
valid RACH f(θ,s) for the Campanula/Izu Islands system.  The proxy in
``causal_model/simulation.py`` is an EXAMPLE of how to write a fast
approximation for debugging — it is NOT a valid RACH simulator.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SimulatorProtocol(Protocol):
    """Minimal interface for a RACH-valid f(θ, s) simulator.

    Any callable that matches this signature can be used as the simulator
    in RACH inference.  The return type is intentionally flexible (Any) to
    allow system-specific output dataclasses.

    Parameters
    ----------
    env:
        Population environment (isolation, pollinator frequencies, etc.).
        Must encode the observable environmental conditions that drive
        the system — not the switch hypotheses.
    params:
        Latent benefit/cost parameters θ sampled from the prior π(θ).
        Must be defined independently of switch state s.
    switches:
        Binary switch state s ∈ {0,1}^K encoding which biological
        pathways are active.  Must be sampled from a prior that is
        independent of θ (typically Bernoulli(0.5) for each switch).

    Returns
    -------
    Any
        System-specific simulated output.  Must expose the same
        attribute names as the pattern evaluator expects (e.g. the
        keys listed in observed_patterns.csv ``variable`` column).
    """

    def __call__(self, env: Any, params: Any, switches: Any) -> Any:
        ...


class SimulatedOutputBase:
    """Base class for simulated outputs to be used with RACH pattern evaluation.

    Subclass this and add system-specific trait fields.  The ``population``
    field is required by the pattern evaluator.

    Example (Campanula)::

        @dataclass(frozen=True)
        class CampanulaOutput(SimulatedOutputBase):
            nectar_guide: float
            selfing_rate: float
            herkogamy: float
            flower_size: float
            Fis: float
            primary_pollinator_frequency: float
            outcrossing_opportunity: float
            neutral_diversity: float
    """

    population: str  # population identifier (e.g. "iso_0.000")
