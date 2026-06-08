"""Run CAPOM scenario ranking against Inoue-series observed patterns.

The Inoue-series literature patterns are treated as observed CAPOM patterns,
not as direct ABM inputs. H1-H5 generate simulated island patterns from
scenario rules, and those outputs are then compared with the known qualitative
patterns for Bombus contribution, flower size, selfing ability, and pollinator
fauna.
"""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


POPULATIONS = ["Mainland", "Oshima", "Kozu", "Hachijo"]
ISOLATION_INDEX = {
    "Mainland": 0.00,
    "Oshima": 0.35,
    "Kozu": 0.68,
    "Hachijo": 0.90,
}


OBSERVED_INOUE_PATTERNS = {
    "bombus_frequency_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
    "flower_size_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
    "selfing_ability_order": ["Hachijo", "Kozu", "Oshima", "Mainland"],
    "pollinator_fauna": {
        "Mainland": "bombus_dominant",
        "Oshima": "mixed_bombus_small_bees",
        "Kozu": "small_pollinator_dominant",
        "Hachijo": "small_pollinator_dominant",
    },
}


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    description: str
    process_flags: tuple[str, ...]


SCENARIOS = [
    ScenarioSpec(
        name="H1_pollinator_loss_only",
        description="Only pollinator environment and Bombus contribution decline with isolation.",
        process_flags=("pollinator_loss",),
    ),
    ScenarioSpec(
        name="H2_pollinator_loss_reproductive_assurance",
        description="Pollinator loss increases reproductive assurance through autonomous selfing.",
        process_flags=("pollinator_loss", "selfing"),
    ),
    ScenarioSpec(
        name="H3_pollinator_loss_inbreeding",
        description="Pollinator loss and selfing interact with inbreeding depression.",
        process_flags=("pollinator_loss", "selfing", "inbreeding"),
    ),
    ScenarioSpec(
        name="H4_pollinator_loss_drift",
        description="Pollinator loss is combined with isolation-driven drift and reduced migration.",
        process_flags=("pollinator_loss", "drift"),
    ),
    ScenarioSpec(
        name="H5_compound_CAPOM",
        description="Pollinator loss, selfing, inbreeding, drift, and selfing-syndrome constraints act together.",
        process_flags=("pollinator_loss", "selfing", "inbreeding", "drift", "selfing_syndrome"),
    ),
]


def load_streamlit_abm() -> dict[str, Any]:
    """Load ABM functions from streamlit_app.py without launching Streamlit."""

    class DummyStreamlit(types.ModuleType):
        def __getattr__(self, name: str):
            def noop(*args: Any, **kwargs: Any) -> Any:
                return args[0] if args else None

            return noop

    dummy = DummyStreamlit("streamlit")
    dummy.sidebar = dummy
    dummy.column_config = types.SimpleNamespace(
        TextColumn=lambda *args, **kwargs: None,
        NumberColumn=lambda *args, **kwargs: None,
    )
    sys.modules["streamlit"] = dummy

    source = (REPO_ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    namespace: dict[str, Any] = {}
    exec(source[: source.index("st.title(")], namespace)
    return namespace


def scenario_parameters(base_params: dict[str, float], population: str, scenario: ScenarioSpec) -> dict[str, float]:
    """Generate ABM parameters from scenario rules, not from observed Inoue patterns."""

    isolation = ISOLATION_INDEX[population]
    params = dict(base_params)

    params["pollinator_environment"] = 0.78
    params["bombus_frequency"] = 0.78
    params["flower_size"] = 0.82
    params["herkogamy"] = 0.78
    params["pollen_ovule_ratio"] = 0.78
    params["selfing_ability"] = 0.22
    params["inbreeding_load"] = 0.12
    params["migration_rate"] = 0.10
    params["genetic_drift_strength"] = 0.025
    params["other_pollinator_efficiency"] = 0.30

    if "pollinator_loss" in scenario.process_flags:
        params["pollinator_environment"] = max(0.25, 0.78 - 0.42 * isolation)
        params["bombus_frequency"] = max(0.0, 0.78 - 1.15 * isolation)

    if "selfing" in scenario.process_flags:
        params["selfing_ability"] = min(0.85, 0.22 + 0.55 * isolation)
        params["herkogamy"] = max(0.25, 0.78 - 0.45 * isolation)

    if "inbreeding" in scenario.process_flags:
        params["inbreeding_load"] = min(0.38, 0.15 + 0.16 * isolation)

    if "drift" in scenario.process_flags:
        params["migration_rate"] = max(0.005, 0.10 * (1.0 - isolation))
        params["genetic_drift_strength"] = min(0.09, 0.025 + 0.055 * isolation)

    if "selfing_syndrome" in scenario.process_flags:
        params["flower_size"] = max(0.40, 0.82 - 0.42 * isolation)
        params["pollen_ovule_ratio"] = max(0.32, 0.78 - 0.48 * isolation)
        params["other_pollinator_efficiency"] = min(0.48, 0.30 + 0.14 * isolation)

    return params


def order_descending(rows: list[dict[str, Any]], key: str) -> list[str]:
    return [row["population"] for row in sorted(rows, key=lambda row: row[key], reverse=True)]


def order_ascending(rows: list[dict[str, Any]], key: str) -> list[str]:
    return [row["population"] for row in sorted(rows, key=lambda row: row[key])]


def classify_pollinator_fauna(row: dict[str, Any]) -> str:
    bombus = float(row["bombus_frequency"])
    if bombus >= 0.55:
        return "bombus_dominant"
    if bombus >= 0.15:
        return "mixed_bombus_small_bees"
    return "small_pollinator_dominant"


def monotonic_distance(rows: list[dict[str, Any]], ordered_populations: list[str], key: str, direction: str) -> float:
    """Distance for strict island-gradient patterns.

    A value of 0 means every adjacent pair follows the observed gradient.
    Ties count as mismatches because the Inoue-series patterns are directional.
    """

    values = {row["population"]: float(row[key]) for row in rows}
    mismatches = 0
    comparisons = len(ordered_populations) - 1
    for left, right in zip(ordered_populations, ordered_populations[1:]):
        if direction == "decreasing":
            mismatches += not (values[left] > values[right])
        elif direction == "increasing":
            mismatches += not (values[left] < values[right])
        else:
            raise ValueError(f"Unknown direction: {direction}")
    return mismatches / comparisons


def fauna_distance(observed: dict[str, str], simulated: dict[str, str]) -> float:
    mismatches = sum(observed[population] != simulated[population] for population in observed)
    return mismatches / len(observed)


def bombus_frequency_distance(rows: list[dict[str, Any]]) -> float:
    """Distance for Inoue-series Bombus pattern: Mainland > Oshima > Kozu ~= Hachijo."""

    values = {row["population"]: float(row["bombus_frequency"]) for row in rows}
    mismatches = 0
    mismatches += not (values["Mainland"] > values["Oshima"])
    mismatches += not (values["Oshima"] > values["Kozu"])
    mismatches += not (abs(values["Kozu"] - values["Hachijo"]) <= 0.05)
    return mismatches / 3


def summarize_scenario(
    scenario: ScenarioSpec,
    abm: dict[str, Any],
    generations: int,
    population_size: int,
    seed: int,
) -> tuple[dict[str, Any], pd.DataFrame]:
    default_data = abm["DEFAULT_FIELD_DATA"]
    field_row_to_params = abm["field_row_to_params"]
    simulate_abm = abm["simulate_abm"]

    base_row = default_data[default_data["population"] == "Mainland"].iloc[0]
    base_params = field_row_to_params(base_row)
    rows: list[dict[str, Any]] = []

    for index, population in enumerate(POPULATIONS):
        params = scenario_parameters(base_params, population, scenario)
        history, _agents = simulate_abm(
            params,
            generations=generations,
            population_size=population_size,
            seed=seed + index,
        )
        final = history.iloc[-1]
        rows.append(
            {
                "scenario": scenario.name,
                "population": population,
                "bombus_frequency": params["bombus_frequency"],
                "flower_size": params["flower_size"],
                "selfing_ability": params["selfing_ability"],
                "pollinator_fauna": classify_pollinator_fauna(params),
                "final_mean_nectar_guide": float(final["mean_nectar_guide"]),
                "final_selfing_rate": float(final["selfing_rate"]),
                "final_outcrossing_rate": float(final["outcrossing_rate"]),
                "mean_fitness": float(final["mean_fitness"]),
            }
        )

    simulated_patterns = {
        "bombus_frequency_order": order_descending(rows, "bombus_frequency"),
        "flower_size_order": order_descending(rows, "flower_size"),
        "selfing_ability_order": order_descending(rows, "selfing_ability"),
        "pollinator_fauna": {row["population"]: row["pollinator_fauna"] for row in rows},
    }

    distances = {
        "bombus_frequency_order": bombus_frequency_distance(rows),
        "flower_size_order": monotonic_distance(
            rows,
            OBSERVED_INOUE_PATTERNS["flower_size_order"],
            key="flower_size",
            direction="decreasing",
        ),
        "selfing_ability_order": monotonic_distance(
            rows,
            list(reversed(OBSERVED_INOUE_PATTERNS["selfing_ability_order"])),
            key="selfing_ability",
            direction="increasing",
        ),
        "pollinator_fauna": fauna_distance(
            OBSERVED_INOUE_PATTERNS["pollinator_fauna"],
            simulated_patterns["pollinator_fauna"],
        ),
    }
    score = {
        "scenario": scenario.name,
        "description": scenario.description,
        "total_distance": sum(distances.values()),
        **distances,
        "simulated_bombus_frequency_order": " > ".join(simulated_patterns["bombus_frequency_order"]),
        "simulated_flower_size_order": " > ".join(simulated_patterns["flower_size_order"]),
        "simulated_selfing_ability_order": " > ".join(simulated_patterns["selfing_ability_order"]),
    }
    return score, pd.DataFrame(rows)


def main() -> None:
    abm = load_streamlit_abm()
    score_rows: list[dict[str, Any]] = []
    output_rows: list[pd.DataFrame] = []

    for scenario in SCENARIOS:
        score, outputs = summarize_scenario(
            scenario,
            abm=abm,
            generations=60,
            population_size=120,
            seed=20260608,
        )
        score_rows.append(score)
        output_rows.append(outputs)

    scores = pd.DataFrame(score_rows).sort_values("total_distance")
    outputs = pd.concat(output_rows, ignore_index=True)

    out_dir = Path(__file__).resolve().parent / "outputs"
    out_dir.mkdir(exist_ok=True)
    scores.to_csv(out_dir / "inoue_pattern_scenario_ranking.csv", index=False)
    outputs.to_csv(out_dir / "inoue_pattern_simulation_outputs.csv", index=False)

    print("Scenario ranking against Inoue-series observed patterns")
    print(scores[["scenario", "total_distance", "bombus_frequency_order", "flower_size_order", "selfing_ability_order", "pollinator_fauna"]].to_string(index=False))
    print(f"\nWrote: {out_dir / 'inoue_pattern_scenario_ranking.csv'}")
    print(f"Wrote: {out_dir / 'inoue_pattern_simulation_outputs.csv'}")


if __name__ == "__main__":
    main()
