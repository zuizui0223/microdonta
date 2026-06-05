"""TenSnap ABM for nectar guide evolution in Campanula punctata var.

Run:
    python shimahotarubukuro_tensnap_abm.py

Then connect a TenSnap renderer/client to ws://localhost:8765.
"""

from __future__ import annotations

import asyncio
import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
for vendor_dir in (SCRIPT_DIR / "work" / "vendor", SCRIPT_DIR.parent / "work" / "vendor"):
    if vendor_dir.exists():
        sys.path.insert(0, str(vendor_dir))
        break

from tensnap import SimulationScenario
from tensnap.bindings import (
    BindParametersConfig,
    action,
    agent,
    agent_layer,
    chart,
    env,
    grid_layer,
)
from tensnap.models import create_parameter


OUTPUT_DIR = SCRIPT_DIR if SCRIPT_DIR.name == "outputs" else SCRIPT_DIR / "outputs"
CSV_PATH = OUTPUT_DIR / "shimahotarubukuro_results.csv"


PRESETS = {
    "Mainland": {
        "pollinator_environment": 0.78,
        "bombus_present": 1.0,
        "bombus_guide_dependence": 0.75,
        "other_pollinator_guide_use": 0.12,
        "selfing_ability": 0.22,
        "inbreeding_load": 0.32,
        "guide_cost": 0.08,
        "seed_set_selfing": 0.46,
        "seed_set_outcrossing": 0.92,
        "germination_selfed": 0.54,
        "germination_outcrossed": 0.86,
        "migration_rate": 0.10,
    },
    "Oshima": {
        "pollinator_environment": 0.58,
        "bombus_present": 1.0,
        "bombus_guide_dependence": 0.65,
        "other_pollinator_guide_use": 0.16,
        "selfing_ability": 0.36,
        "inbreeding_load": 0.25,
        "guide_cost": 0.07,
        "seed_set_selfing": 0.55,
        "seed_set_outcrossing": 0.84,
        "germination_selfed": 0.57,
        "germination_outcrossed": 0.82,
        "migration_rate": 0.05,
    },
    "Kozu": {
        "pollinator_environment": 0.42,
        "bombus_present": 0.0,
        "bombus_guide_dependence": 0.0,
        "other_pollinator_guide_use": 0.18,
        "selfing_ability": 0.52,
        "inbreeding_load": 0.18,
        "guide_cost": 0.05,
        "seed_set_selfing": 0.64,
        "seed_set_outcrossing": 0.76,
        "germination_selfed": 0.60,
        "germination_outcrossed": 0.78,
        "migration_rate": 0.025,
    },
    "Hachijo": {
        "pollinator_environment": 0.36,
        "bombus_present": 0.0,
        "bombus_guide_dependence": 0.0,
        "other_pollinator_guide_use": 0.18,
        "selfing_ability": 0.68,
        "inbreeding_load": 0.12,
        "guide_cost": 0.04,
        "seed_set_selfing": 0.72,
        "seed_set_outcrossing": 0.68,
        "germination_selfed": 0.62,
        "germination_outcrossed": 0.74,
        "migration_rate": 0.01,
    },
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def lerp_color(value: float) -> str:
    """Map nectar-guide strength to a legible yellow-to-violet scale."""
    value = clamp(value)
    start = (244, 199, 54)
    end = (101, 76, 163)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * value) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


@agent(
    x="position[0]",
    y="position[1]",
    color="color",
    size="size",
    data="data",
)
@dataclass
class Plant:
    id: int
    position: tuple[float, float]
    nectar_guide: float
    neutral_diversity: float
    fitness: float = 1.0
    seed_output: float = 1.0
    germination: float = 1.0
    reproduction_mode: str = "outcrossing"

    @property
    def color(self) -> str:
        return lerp_color(self.nectar_guide)

    @property
    def size(self) -> float:
        return 0.55 + 0.7 * clamp(self.fitness)

    @property
    def data(self) -> dict[str, float | str]:
        return {
            "nectar_guide": round(self.nectar_guide, 4),
            "fitness": round(self.fitness, 4),
            "seed_output": round(self.seed_output, 4),
            "germination": round(self.germination, 4),
            "neutral_diversity": round(self.neutral_diversity, 4),
            "reproduction_mode": self.reproduction_mode,
        }


@grid_layer(width="width", height="height", stroke_color="#d7dce2")
@agent_layer("plants", item_iterable_projector="plants")
@env(id="shimahotarubukuro")
class NectarGuideModel:
    width = 32
    height = 22

    def __init__(self, population_size: int = 160, seed: int = 7) -> None:
        self.population_size = population_size
        self.seed = seed
        self.rng = random.Random(seed)
        self.generation = 0

        self.pollinator_environment = PRESETS["Mainland"]["pollinator_environment"]
        self.bombus_present = PRESETS["Mainland"]["bombus_present"]
        self.bombus_guide_dependence = PRESETS["Mainland"]["bombus_guide_dependence"]
        self.other_pollinator_guide_use = PRESETS["Mainland"]["other_pollinator_guide_use"]
        self.selfing_ability = PRESETS["Mainland"]["selfing_ability"]
        self.inbreeding_load = PRESETS["Mainland"]["inbreeding_load"]
        self.guide_cost = PRESETS["Mainland"]["guide_cost"]
        self.seed_set_selfing = PRESETS["Mainland"]["seed_set_selfing"]
        self.seed_set_outcrossing = PRESETS["Mainland"]["seed_set_outcrossing"]
        self.germination_selfed = PRESETS["Mainland"]["germination_selfed"]
        self.germination_outcrossed = PRESETS["Mainland"]["germination_outcrossed"]
        self.migration_rate = PRESETS["Mainland"]["migration_rate"]

        self.base_outcross = 0.10
        self.pollinator_environment_outcross_effect = 0.42
        self.mutation_sd = 0.055
        self.genetic_drift_strength = 0.035

        self.plants: list[Plant] = []
        self.history: list[dict[str, float | int]] = []
        self.reset()

    def reset(self) -> None:
        self.rng = random.Random(self.seed)
        self.generation = 0
        self.plants = [
            Plant(
                id=i,
                position=self._random_position(),
                nectar_guide=clamp(self.rng.betavariate(2.0, 2.0)),
                neutral_diversity=clamp(self.rng.betavariate(6.0, 2.0)),
            )
            for i in range(self.population_size)
        ]
        self._evaluate_generation()
        self._record_history()

    def step(self) -> None:
        self._evaluate_generation()
        parents = self._sample_parents()
        next_plants: list[Plant] = []
        for i, parent in enumerate(parents):
            mutated_guide = clamp(
                parent.nectar_guide + self.rng.gauss(0.0, self.mutation_sd)
            )
            diversity = self._offspring_diversity(parent)
            next_plants.append(
                Plant(
                    id=i,
                    position=self._jittered_position(parent.position),
                    nectar_guide=mutated_guide,
                    neutral_diversity=diversity,
                    fitness=parent.fitness,
                    seed_output=parent.seed_output,
                    germination=parent.germination,
                    reproduction_mode=parent.reproduction_mode,
                )
            )
        self.plants = next_plants
        self.generation += 1
        self._evaluate_generation()
        self._record_history()

    def _random_position(self) -> tuple[float, float]:
        return (
            self.rng.uniform(0.5, self.width - 0.5),
            self.rng.uniform(0.5, self.height - 0.5),
        )

    def _jittered_position(self, position: tuple[float, float]) -> tuple[float, float]:
        x, y = position
        return (
            clamp(x + self.rng.gauss(0, 1.2), 0.5, self.width - 0.5),
            clamp(y + self.rng.gauss(0, 1.2), 0.5, self.height - 0.5),
        )

    def _outcross_probability(self, plant: Plant) -> float:
        guide_alignment = (
            self.bombus_present * self.bombus_guide_dependence
            + (1.0 - self.bombus_present) * self.other_pollinator_guide_use
        )
        return clamp(
            self.base_outcross
            + self.pollinator_environment
            * (self.pollinator_environment_outcross_effect + guide_alignment * plant.nectar_guide)
        )

    def _evaluate_generation(self) -> None:
        for plant in self.plants:
            outcrossing = self.rng.random() < self._outcross_probability(plant)
            selfing = (not outcrossing) and (self.rng.random() < self.selfing_ability)
            plant.reproduction_mode = (
                "outcrossing" if outcrossing else "selfing" if selfing else "failed"
            )

            if outcrossing:
                plant.seed_output = self.seed_set_outcrossing
                plant.germination = self.germination_outcrossed
                inbreeding_penalty = 0.0
            elif selfing:
                plant.seed_output = self.seed_set_selfing
                plant.germination = max(
                    0.0,
                    min(
                        self.germination_selfed,
                        self.germination_outcrossed - self.inbreeding_load,
                    ),
                )
                inbreeding_penalty = 0.0
            else:
                plant.seed_output = 0.02
                plant.germination = 0.02
                inbreeding_penalty = 0.0

            guide_penalty = self.guide_cost * plant.nectar_guide
            plant.fitness = max(
                0.001,
                plant.seed_output * plant.germination * (1.0 - inbreeding_penalty)
                - guide_penalty,
            )

    def _offspring_diversity(self, parent: Plant) -> float:
        if parent.reproduction_mode == "outcrossing":
            diversity = parent.neutral_diversity + 0.045
        elif parent.reproduction_mode == "selfing":
            diversity = parent.neutral_diversity * (1.0 - 0.5 * self.inbreeding_load)
        else:
            diversity = parent.neutral_diversity * 0.96
        migration_rescue = self.migration_rate * (0.82 - diversity)
        drift = self.rng.gauss(0.0, self.genetic_drift_strength)
        return clamp(diversity + migration_rescue + drift)

    def _sample_parents(self) -> list[Plant]:
        total_fitness = sum(plant.fitness for plant in self.plants)
        if total_fitness <= 0:
            return [self.rng.choice(self.plants) for _ in range(self.population_size)]

        weights = [plant.fitness / total_fitness for plant in self.plants]
        return self.rng.choices(self.plants, weights=weights, k=self.population_size)

    def _mean(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else math.nan

    def _record_history(self) -> None:
        self.history.append(
            {
                "generation": self.generation,
                "mean_nectar_guide": self._mean_nectar_guide_value(),
                "selfing_rate": self._selfing_rate_value(),
                "outcrossing_rate": self._outcrossing_rate_value(),
                "failed_rate": self._failed_rate_value(),
                "mean_fitness": self._mean_fitness_value(),
                "seed_output": self._mean_seed_output_value(),
                "germination": self._mean_germination_value(),
                "mean_neutral_diversity": self._mean_neutral_diversity_value(),
                "Fis": self._fis_value(),
                "Fst": self._fst_value(),
                "pollinator_environment": self.pollinator_environment,
                "bombus_present": self.bombus_present,
                "bombus_guide_dependence": self.bombus_guide_dependence,
                "other_pollinator_guide_use": self.other_pollinator_guide_use,
                "selfing_ability": self.selfing_ability,
                "inbreeding_load": self.inbreeding_load,
                "guide_cost": self.guide_cost,
                "seed_set_selfing": self.seed_set_selfing,
                "seed_set_outcrossing": self.seed_set_outcrossing,
                "germination_selfed": self.germination_selfed,
                "germination_outcrossed": self.germination_outcrossed,
                "migration_rate": self.migration_rate,
            }
        )

    def _apply_preset(self, name: str) -> None:
        for key, value in PRESETS[name].items():
            setattr(self, key, value)
        self._evaluate_generation()
        self._record_history()

    @action(label="Mainland")
    def preset_mainland(self) -> None:
        self._apply_preset("Mainland")

    @action(label="Oshima")
    def preset_oshima(self) -> None:
        self._apply_preset("Oshima")

    @action(label="Kozu")
    def preset_kozu(self) -> None:
        self._apply_preset("Kozu")

    @action(label="Hachijo")
    def preset_hachijo(self) -> None:
        self._apply_preset("Hachijo")

    @action(label="Export CSV")
    def export_csv(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "generation",
            "mean_nectar_guide",
            "selfing_rate",
            "outcrossing_rate",
            "failed_rate",
            "mean_fitness",
            "seed_output",
            "germination",
            "mean_neutral_diversity",
            "Fis",
            "Fst",
            "pollinator_environment",
            "bombus_present",
            "bombus_guide_dependence",
            "other_pollinator_guide_use",
            "selfing_ability",
            "inbreeding_load",
            "guide_cost",
            "seed_set_selfing",
            "seed_set_outcrossing",
            "germination_selfed",
            "germination_outcrossed",
            "migration_rate",
        ]
        with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.history)

    @chart(
        "nectar_guide_evolution",
        "Mean Nectar Guide",
        data_list=[
            {"id": "mean_nectar_guide", "label": "mean_nectar_guide", "color": "#654ca3"},
            {"id": "guide_threshold_0_5", "label": "threshold 0.5", "color": "#343a40"},
        ],
    )
    def mean_nectar_guide(self) -> dict[str, float]:
        return {
            "mean_nectar_guide": self._mean_nectar_guide_value(),
            "guide_threshold_0_5": 0.5,
        }

    @chart(
        "reproduction_rates",
        "Reproduction Rates",
        data_list=[
            {"id": "selfing_rate", "label": "selfing_rate", "color": "#d95f02"},
            {"id": "outcrossing_rate", "label": "outcrossing_rate", "color": "#1b9e77"},
            {"id": "failed_rate", "label": "failed_rate", "color": "#666666"},
        ],
    )
    def reproduction_rates(self) -> dict[str, float]:
        return {
            "selfing_rate": self._selfing_rate_value(),
            "outcrossing_rate": self._outcrossing_rate_value(),
            "failed_rate": self._failed_rate_value(),
        }

    @chart("mean_fitness", "Mean Fitness", "#386cb0")
    def mean_fitness(self) -> float:
        return self._mean_fitness_value()

    @chart(
        "fitness_components",
        "Fitness Components",
        data_list=[
            {"id": "seed_output", "label": "seed_output", "color": "#7570b3"},
            {"id": "germination", "label": "germination", "color": "#66a61e"},
        ],
    )
    def fitness_components(self) -> dict[str, float]:
        return {
            "seed_output": self._mean_seed_output_value(),
            "germination": self._mean_germination_value(),
        }

    @chart(
        "genetic_indices",
        "Genetic Indices",
        data_list=[
            {
                "id": "mean_neutral_diversity",
                "label": "mean_neutral_diversity",
                "color": "#1f78b4",
            },
            {"id": "Fis", "label": "Fis", "color": "#e7298a"},
            {"id": "Fst", "label": "Fst", "color": "#a6761d"},
        ],
    )
    def genetic_indices(self) -> dict[str, float]:
        return {
            "mean_neutral_diversity": self._mean_neutral_diversity_value(),
            "Fis": self._fis_value(),
            "Fst": self._fst_value(),
        }

    def _mean_nectar_guide_value(self) -> float:
        return self._mean([p.nectar_guide for p in self.plants])

    def _mean_fitness_value(self) -> float:
        return self._mean([p.fitness for p in self.plants])

    def _mean_seed_output_value(self) -> float:
        return self._mean([p.seed_output for p in self.plants])

    def _mean_germination_value(self) -> float:
        return self._mean([p.germination for p in self.plants])

    def _mean_neutral_diversity_value(self) -> float:
        return self._mean([p.neutral_diversity for p in self.plants])

    def _selfing_rate_value(self) -> float:
        return self._mean(
            [1.0 if p.reproduction_mode == "selfing" else 0.0 for p in self.plants]
        )

    def _outcrossing_rate_value(self) -> float:
        return self._mean(
            [1.0 if p.reproduction_mode == "outcrossing" else 0.0 for p in self.plants]
        )

    def _failed_rate_value(self) -> float:
        return self._mean(
            [1.0 if p.reproduction_mode == "failed" else 0.0 for p in self.plants]
        )

    def _fis_value(self) -> float:
        return clamp(self._selfing_rate_value() * (1.0 - 0.5 * self.migration_rate))

    def _fst_value(self) -> float:
        isolation = 1.0 - self.migration_rate
        pollinator_loss = 1.0 - self._outcrossing_rate_value()
        return clamp(isolation * pollinator_loss * (1.0 - self._mean_neutral_diversity_value()))


async def main() -> None:
    model = NectarGuideModel()
    scenario = SimulationScenario(port=8765)
    scenario.add_environment(model)
    scenario.add_parameters(
        model,
        BindParametersConfig(
            include=[
                "pollinator_environment",
                "bombus_present",
                "bombus_guide_dependence",
                "other_pollinator_guide_use",
                "selfing_ability",
                "inbreeding_load",
                "guide_cost",
                "seed_set_selfing",
                "seed_set_outcrossing",
                "germination_selfed",
                "germination_outcrossed",
                "migration_rate",
            ],
            custom_bindings={
                "pollinator_environment": create_parameter(
                    id="pollinator_environment",
                    type="number",
                    label="pollinator_environment",
                    value=model.pollinator_environment,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "bombus_present": create_parameter(
                    id="bombus_present",
                    type="number",
                    label="bombus_present",
                    value=model.bombus_present,
                    min=0,
                    max=1,
                    step=1.0,
                ),
                "bombus_guide_dependence": create_parameter(
                    id="bombus_guide_dependence",
                    type="number",
                    label="bombus_guide_dependence",
                    value=model.bombus_guide_dependence,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "other_pollinator_guide_use": create_parameter(
                    id="other_pollinator_guide_use",
                    type="number",
                    label="other_pollinator_guide_use",
                    value=model.other_pollinator_guide_use,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "selfing_ability": create_parameter(
                    id="selfing_ability",
                    type="number",
                    label="selfing_ability",
                    value=model.selfing_ability,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "inbreeding_load": create_parameter(
                    id="inbreeding_load",
                    type="number",
                    label="inbreeding_load",
                    value=model.inbreeding_load,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "guide_cost": create_parameter(
                    id="guide_cost",
                    type="number",
                    label="guide_cost",
                    value=model.guide_cost,
                    min=0,
                    max=0.5,
                    step=0.005,
                ),
                "seed_set_selfing": create_parameter(
                    id="seed_set_selfing",
                    type="number",
                    label="seed_set_selfing",
                    value=model.seed_set_selfing,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "seed_set_outcrossing": create_parameter(
                    id="seed_set_outcrossing",
                    type="number",
                    label="seed_set_outcrossing",
                    value=model.seed_set_outcrossing,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "germination_selfed": create_parameter(
                    id="germination_selfed",
                    type="number",
                    label="germination_selfed",
                    value=model.germination_selfed,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "germination_outcrossed": create_parameter(
                    id="germination_outcrossed",
                    type="number",
                    label="germination_outcrossed",
                    value=model.germination_outcrossed,
                    min=0,
                    max=1,
                    step=0.01,
                ),
                "migration_rate": create_parameter(
                    id="migration_rate",
                    type="number",
                    label="migration_rate",
                    value=model.migration_rate,
                    min=0,
                    max=0.25,
                    step=0.005,
                ),
            },
        ),
    )
    scenario.add_charts(model)
    scenario.add_actions(model)
    await scenario.register_model_handler(model_step=model.step, model_reset=model.reset)
    print("TenSnap ABM server: ws://localhost:8765")
    print(f"CSV export action writes: {CSV_PATH}")
    await scenario.run()


if __name__ == "__main__":
    asyncio.run(main())
