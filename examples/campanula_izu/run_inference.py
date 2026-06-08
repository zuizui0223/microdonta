"""Generative inverse estimation for the Campanula Izu Island case study.

Two inference modes
-------------------
1. Per-population ABC
   For each population separately, find latent parameters that reproduce
   that population's observed patterns. Gives per-population posterior ranges.

2. Cross-population ABC  (recommended, stronger constraint)
   Find ONE set of latent parameters that simultaneously reproduces the
   observed gradient across all four populations (Mainland, Oshima, Kozu,
   Hachijo). This tests whether a single mechanism explains the whole gradient.

Run
---
    python examples/campanula_izu/run_inference.py

Outputs (written to examples/campanula_izu/outputs/)
------
    posterior_<population>.csv       — per-population posterior samples
    posterior_summary_<pop>.csv      — quantile summaries per population
    posterior_cross_population.csv   — cross-population posterior samples
    posterior_summary_cross.csv      — cross-population summary
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script without installing the package
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd

from constraint_abm.abm_core import simulate_multi_seed
from constraint_abm.inference import (
    InferenceResult,
    abc_cross_population,
    abc_rejection,
    posterior_summary,
    credible_interval,
)
from observed_patterns import (
    BIOLOGICAL_CONSTRAINTS,
    LATENT_PARAMS,
    POPULATION_FIXED_PARAMS,
    POPULATION_OBSERVED,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Simulation settings
# ---------------------------------------------------------------------------
GENERATIONS = 80
POPULATION_SIZE = 160
SEEDS = [42, 43, 44]          # averaged across 3 seeds per evaluation
N_ABC_SAMPLES = 8_000          # draws from prior; increase for finer posteriors
EPSILON_PER_POP = 0.10         # acceptance threshold for per-population runs
EPSILON_CROSS = 0.12           # slightly relaxed for cross-population (harder constraint)


# ---------------------------------------------------------------------------
# Simulation wrapper
# ---------------------------------------------------------------------------

def make_simulate(fixed_params: dict) -> callable:
    """Return a simulate function bound to the given fixed parameters."""
    def _simulate(full_params: dict) -> dict[str, float]:
        return simulate_multi_seed(
            params=full_params,
            generations=GENERATIONS,
            population_size=POPULATION_SIZE,
            seeds=SEEDS,
        )
    return _simulate


# ---------------------------------------------------------------------------
# Per-population inference
# ---------------------------------------------------------------------------

def run_per_population() -> dict[str, InferenceResult]:
    print("\n=== Per-population ABC inference ===")
    results: dict[str, InferenceResult] = {}

    for pop_name, fixed_params in POPULATION_FIXED_PARAMS.items():
        print(f"\n--- {pop_name} ---")
        observed = POPULATION_OBSERVED[pop_name]
        simulate_fn = make_simulate(fixed_params)

        result = abc_rejection(
            observed_patterns=observed,
            latent_params=LATENT_PARAMS,
            fixed_params=fixed_params,
            constraints=BIOLOGICAL_CONSTRAINTS,
            simulate=simulate_fn,
            n_samples=N_ABC_SAMPLES,
            epsilon=EPSILON_PER_POP,
            seed=42,
            verbose=True,
        )
        results[pop_name] = result

        out_samples = OUTPUT_DIR / f"posterior_{pop_name}.csv"
        out_summary = OUTPUT_DIR / f"posterior_summary_{pop_name}.csv"
        result.samples.to_csv(out_samples, index=False)
        posterior_summary(result).to_csv(out_summary)

        print(f"  Accepted: {len(result.samples)} / {result.n_attempted}  "
              f"(rate={result.acceptance_rate:.4f})")
        if not result.is_empty():
            summary = posterior_summary(result)
            print(summary.to_string())
        else:
            print("  WARNING: no samples accepted — consider increasing epsilon or n_samples.")

    return results


# ---------------------------------------------------------------------------
# Cross-population inference
# ---------------------------------------------------------------------------

def run_cross_population() -> InferenceResult:
    print("\n=== Cross-population ABC inference ===")
    print(
        "Constraint: ONE latent parameter set must simultaneously reproduce\n"
        "the observed gradient across Mainland, Oshima, Kozu, and Hachijo."
    )

    result = abc_cross_population(
        population_patterns=POPULATION_OBSERVED,
        latent_params=LATENT_PARAMS,
        population_fixed_params=POPULATION_FIXED_PARAMS,
        constraints=BIOLOGICAL_CONSTRAINTS,
        make_simulate=make_simulate,
        n_samples=N_ABC_SAMPLES,
        epsilon=EPSILON_CROSS,
        seed=42,
        verbose=True,
    )

    result.samples.to_csv(OUTPUT_DIR / "posterior_cross_population.csv", index=False)
    posterior_summary(result).to_csv(OUTPUT_DIR / "posterior_summary_cross.csv")

    print(f"\nAccepted: {len(result.samples)} / {result.n_attempted}  "
          f"(rate={result.acceptance_rate:.4f})")

    if not result.is_empty():
        summary = posterior_summary(result)
        print("\nPosterior summary (cross-population):")
        print(summary.to_string())

        print("\n90 % credible intervals:")
        for lp in LATENT_PARAMS:
            lo, hi = credible_interval(result, lp.name, level=0.90)
            print(f"  {lp.name:<32}  [{lo:.4f}, {hi:.4f}]")
    else:
        print("WARNING: no samples accepted — consider increasing epsilon or n_samples.")

    return result


# ---------------------------------------------------------------------------
# Comparison report
# ---------------------------------------------------------------------------

def comparison_report(per_pop: dict[str, InferenceResult]) -> None:
    print("\n=== Parameter range comparison across populations ===")
    rows = []
    for pop_name, result in per_pop.items():
        if result.is_empty():
            continue
        for lp in LATENT_PARAMS:
            lo, hi = credible_interval(result, lp.name, level=0.90)
            rows.append({
                "population": pop_name,
                "parameter": lp.name,
                "q05": lo,
                "q50": float(result.samples[lp.name].median()),
                "q95": hi,
            })
    if not rows:
        print("  No accepted samples to compare.")
        return
    df = pd.DataFrame(rows)
    out = OUTPUT_DIR / "comparison_report.csv"
    df.to_csv(out, index=False)
    print(df.pivot(index="parameter", columns="population", values="q50").to_string())
    print(f"\n  Full comparison saved to {out}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Campanula Izu Island — generative inverse estimation")
    print(f"  n_samples={N_ABC_SAMPLES}  "
          f"epsilon_per_pop={EPSILON_PER_POP}  "
          f"epsilon_cross={EPSILON_CROSS}")
    print(f"  generations={GENERATIONS}  pop_size={POPULATION_SIZE}  seeds={SEEDS}")
    print(f"  outputs → {OUTPUT_DIR}\n")

    per_pop_results = run_per_population()
    cross_result = run_cross_population()
    comparison_report(per_pop_results)

    print(f"\nDone. All CSVs written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
