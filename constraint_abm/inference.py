"""Generative inverse estimation via ABC rejection sampling.

Usage
-----
From the examples/campanula_izu/run_inference.py entry point::

    result = abc_rejection(
        observed_patterns=patterns,
        latent_params=latent_params,
        fixed_params=fixed_params,
        constraints=constraints,
        simulate=simulate_fn,
        n_samples=10_000,
        epsilon=0.10,
    )
    summary = posterior_summary(result)
    result.samples.to_csv("posterior.csv", index=False)
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .constraints import Constraint
from .latent import LatentParameter
from .patterns import ObservablePattern


@dataclass
class InferenceResult:
    """Posterior samples accepted by ABC rejection."""

    samples: pd.DataFrame
    acceptance_rate: float
    n_attempted: int
    epsilon: float
    latent_names: list[str]

    def is_empty(self) -> bool:
        return self.samples.empty

    def __repr__(self) -> str:
        return (
            f"InferenceResult(accepted={len(self.samples)}, "
            f"rate={self.acceptance_rate:.4f}, epsilon={self.epsilon})"
        )


def abc_rejection(
    observed_patterns: list[ObservablePattern],
    latent_params: list[LatentParameter],
    fixed_params: dict[str, float],
    constraints: list[Constraint],
    simulate: Callable[[dict[str, float]], dict[str, float]],
    n_samples: int = 5000,
    epsilon: float = 0.10,
    seed: int = 42,
    verbose: bool = True,
) -> InferenceResult:
    """ABC rejection sampler for generative inverse estimation.

    Draws latent parameter candidates uniformly from their prior ranges,
    rejects those violating biological constraints, runs the simulation,
    computes the weighted mean pattern distance, and accepts candidates
    whose distance falls below *epsilon*.

    The accepted set approximates the posterior distribution
    p(latent | observed patterns).

    Parameters
    ----------
    observed_patterns:
        Field-measurable patterns the simulation must reproduce.
        Each `ObservablePattern` carries a target value, weight, and
        a `distance()` method.
    latent_params:
        Parameters sampled from uniform priors [lower, upper].
        These are the difficult-to-measure trade-offs being estimated.
    fixed_params:
        Population-specific or well-measured parameters held constant.
    constraints:
        Hard biological filters applied before simulation.
        Candidates failing any constraint are immediately rejected.
    simulate:
        ``simulate(full_params) -> dict[str, float]``
        Must return a dict whose keys match pattern names.
    n_samples:
        Total draws attempted from the prior.
    epsilon:
        Acceptance threshold on the normalized weighted mean distance.
        Lower = stricter = fewer but better samples.
    seed:
        RNG seed for reproducibility of the sampling loop.
    verbose:
        Print progress every 10 % of n_samples.

    Returns
    -------
    InferenceResult
        `.samples`  — DataFrame of accepted (latent params + distances)
        `.acceptance_rate` — fraction accepted
        `.n_attempted`     — total draws from prior
    """
    rng = random.Random(seed)
    accepted: list[dict[str, Any]] = []
    weight_sum = sum(p.weight for p in observed_patterns) or 1.0
    log_interval = max(1, n_samples // 10)

    for i in range(n_samples):
        # 1. Sample latent parameters from uniform priors
        candidate = {lp.name: rng.uniform(lp.lower, lp.upper) for lp in latent_params}
        full_params = {**fixed_params, **candidate}

        # 2. Hard biological constraint filter
        if not all(c.predicate(full_params) for c in constraints):
            continue

        # 3. Run generative simulation
        try:
            simulated = simulate(full_params)
        except Exception:
            continue

        # 4. Compute normalized weighted mean distance
        total_dist = 0.0
        pat_dists: dict[str, float] = {}
        for pat in observed_patterns:
            if pat.name not in simulated:
                d = 1.0
            else:
                d = float(pat.distance(simulated[pat.name]))
            pat_dists[pat.name] = d
            total_dist += pat.weight * d
        total_dist /= weight_sum

        # 5. Accept / reject
        if total_dist <= epsilon:
            row: dict[str, Any] = {**candidate, "distance": total_dist}
            row.update({f"d_{k}": v for k, v in pat_dists.items()})
            accepted.append(row)

        if verbose and (i + 1) % log_interval == 0:
            rate = len(accepted) / (i + 1)
            print(f"  [{i + 1:>{len(str(n_samples))}}/{n_samples}]  "
                  f"accepted={len(accepted)}  rate={rate:.4f}")

    latent_names = [lp.name for lp in latent_params]
    pattern_dist_cols = [f"d_{p.name}" for p in observed_patterns]
    all_cols = latent_names + ["distance"] + pattern_dist_cols

    df = (
        pd.DataFrame(accepted)
        if accepted
        else pd.DataFrame(columns=all_cols)
    )
    return InferenceResult(
        samples=df,
        acceptance_rate=len(accepted) / max(1, n_samples),
        n_attempted=n_samples,
        epsilon=epsilon,
        latent_names=latent_names,
    )


def abc_cross_population(
    population_patterns: dict[str, list[ObservablePattern]],
    latent_params: list[LatentParameter],
    population_fixed_params: dict[str, dict[str, float]],
    constraints: list[Constraint],
    make_simulate: Callable[[dict[str, float]], Callable[[dict[str, float]], dict[str, float]]],
    n_samples: int = 5000,
    epsilon: float = 0.10,
    seed: int = 42,
    verbose: bool = True,
) -> InferenceResult:
    """Cross-population ABC: one latent set must explain all populations.

    Tests whether a single mechanistic parameter set simultaneously
    reproduces the observed gradient across all populations (Mainland,
    Oshima, Kozu, Hachijo). This is a stronger constraint than
    per-population inference.

    Parameters
    ----------
    population_patterns:
        ``{population_name: [ObservablePattern, ...]}``
    latent_params:
        Shared latent parameters sampled from priors.
    population_fixed_params:
        ``{population_name: {param: value}}``
        Population-specific fixed parameters (pollinator env, Bombus
        frequency, selfing ability, etc.).
    constraints:
        Hard biological filters on the candidate parameter set.
    make_simulate:
        ``make_simulate(fixed_params) -> simulate_fn``
        Returns a simulate callable bound to those fixed params.
    n_samples, epsilon, seed, verbose:
        Same as ``abc_rejection``.

    Returns
    -------
    InferenceResult
        Same structure as ``abc_rejection``.
        Distance columns are prefixed by population name.
    """
    rng = random.Random(seed)
    accepted: list[dict[str, Any]] = []
    populations = list(population_patterns.keys())
    log_interval = max(1, n_samples // 10)

    for i in range(n_samples):
        candidate = {lp.name: rng.uniform(lp.lower, lp.upper) for lp in latent_params}

        # Constraints are checked on the candidate alone (shared mechanism)
        if not all(c.predicate(candidate) for c in constraints):
            continue

        # Run ABM for every population and accumulate pattern distances
        total_dist = 0.0
        pop_dists: dict[str, float] = {}
        pat_detail: dict[str, float] = {}
        weight_total = 0.0
        failed = False

        for pop_name in populations:
            fixed = population_fixed_params[pop_name]
            full_params = {**fixed, **candidate}
            try:
                sim_fn = make_simulate(fixed)
                simulated = sim_fn({**fixed, **candidate})
            except Exception:
                failed = True
                break

            patterns = population_patterns[pop_name]
            w_sum = sum(p.weight for p in patterns) or 1.0
            pop_dist = 0.0
            for pat in patterns:
                d = float(pat.distance(simulated[pat.name])) if pat.name in simulated else 1.0
                pat_detail[f"{pop_name}.{pat.name}"] = d
                pop_dist += pat.weight * d
            pop_dist /= w_sum
            pop_dists[pop_name] = pop_dist
            total_dist += pop_dist
            weight_total += 1.0

        if failed:
            continue

        total_dist /= max(1.0, weight_total)

        if total_dist <= epsilon:
            row: dict[str, Any] = {**candidate, "distance": total_dist}
            row.update({f"d_{k}": v for k, v in pop_dists.items()})
            row.update({f"d_{k}": v for k, v in pat_detail.items()})
            accepted.append(row)

        if verbose and (i + 1) % log_interval == 0:
            rate = len(accepted) / (i + 1)
            print(f"  [{i + 1:>{len(str(n_samples))}}/{n_samples}]  "
                  f"accepted={len(accepted)}  rate={rate:.4f}")

    latent_names = [lp.name for lp in latent_params]
    df = pd.DataFrame(accepted) if accepted else pd.DataFrame(
        columns=latent_names + ["distance"] + [f"d_{p}" for p in populations]
    )
    return InferenceResult(
        samples=df,
        acceptance_rate=len(accepted) / max(1, n_samples),
        n_attempted=n_samples,
        epsilon=epsilon,
        latent_names=latent_names,
    )


def posterior_summary(result: InferenceResult) -> pd.DataFrame:
    """Return descriptive statistics of the accepted posterior samples.

    Returns a DataFrame indexed by latent parameter name with columns:
    mean, std, q05, q50, q95.
    """
    if result.is_empty():
        return pd.DataFrame(
            columns=["mean", "std", "q05", "q50", "q95"],
            index=result.latent_names,
        )
    df = result.samples[result.latent_names]
    return pd.concat(
        [
            df.mean().rename("mean"),
            df.std().rename("std"),
            df.quantile(0.05).rename("q05"),
            df.quantile(0.50).rename("q50"),
            df.quantile(0.95).rename("q95"),
        ],
        axis=1,
    )


def credible_interval(result: InferenceResult, param: str, level: float = 0.90) -> tuple[float, float]:
    """Return the equal-tailed credible interval for one latent parameter."""
    if result.is_empty() or param not in result.samples.columns:
        return (float("nan"), float("nan"))
    lo = (1.0 - level) / 2.0
    hi = 1.0 - lo
    vals = result.samples[param]
    return float(vals.quantile(lo)), float(vals.quantile(hi))
