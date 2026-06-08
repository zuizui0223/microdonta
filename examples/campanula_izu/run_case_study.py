"""Minimal CAPOM scenario-ranking example for the Campanula case study.

This script intentionally avoids depending on Streamlit. It demonstrates the
package-level pattern-matching API with ordinal targets and placeholder
scenario outputs. The next step is to connect these scenarios to the extracted
ABM core.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from constraint_abm.matching import compare_patterns, rank_scenarios
from constraint_abm.patterns import ordinal_pattern


OBSERVED_PATTERNS = [
    ordinal_pattern("nectar_guide_order", ["Mainland", "Oshima", "Kozu", "Hachijo"], weight=2.0),
    ordinal_pattern("selfing_order", ["Hachijo", "Kozu", "Oshima", "Mainland"]),
    ordinal_pattern("flower_size_order", ["Mainland", "Oshima", "Kozu", "Hachijo"]),
]


SIMULATED_SCENARIO_PATTERNS = {
    "H1_pollinator_loss_only": {
        "nectar_guide_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
        "selfing_order": ["Oshima", "Mainland", "Kozu", "Hachijo"],
        "flower_size_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
    },
    "H2_pollinator_loss_reproductive_assurance": {
        "nectar_guide_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
        "selfing_order": ["Hachijo", "Kozu", "Oshima", "Mainland"],
        "flower_size_order": ["Mainland", "Oshima", "Kozu", "Hachijo"],
    },
    "N1_drift_only": {
        "nectar_guide_order": ["Oshima", "Mainland", "Hachijo", "Kozu"],
        "selfing_order": ["Kozu", "Hachijo", "Oshima", "Mainland"],
        "flower_size_order": ["Mainland", "Kozu", "Oshima", "Hachijo"],
    },
}


def main() -> None:
    results = [
        compare_patterns(scenario, OBSERVED_PATTERNS, simulated)
        for scenario, simulated in SIMULATED_SCENARIO_PATTERNS.items()
    ]
    for result in rank_scenarios(results):
        print(f"{result.scenario}: distance={result.total_distance:.3f}")


if __name__ == "__main__":
    main()
