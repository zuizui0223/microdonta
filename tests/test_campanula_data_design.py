from __future__ import annotations

import sys
from pathlib import Path
import csv
from types import SimpleNamespace

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))


def test_campanula_observed_targets_are_canonical_gradients():
    from examples.campanula_izu.observed_data import observed_target_patterns

    targets = observed_target_patterns()
    assert [row["pattern"] for row in targets] == ["selfing_distance", "flower_size_distance"]
    assert all(row["type"] == "gradient_slope" for row in targets)


def test_herkogamy_nectar_guide_and_fis_are_not_abc_targets():
    from examples.campanula_izu.observed_data import load_observed_pattern_table

    rows = load_observed_pattern_table()
    forbidden = {"herkogamy", "nectar_guide", "Fis"}
    bad = [row for row in rows if row.get("variable") in forbidden and row.get("role") == "observed_target"]
    assert not bad


def test_independent_observations_do_not_promote_blank_values_to_targets():
    path = _repo / "examples" / "campanula_izu" / "data" / "independent_observations.csv"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert {row["population"] for row in rows} >= {
        "Honshu",
        "Oshima",
        "Toshima",
        "Niijima",
        "Kozushima",
        "Miyake",
        "Hachijo",
    }
    assert not [
        row for row in rows
        if row["role"] == "observed_target" and not row["observed_value"].strip()
    ]


def test_future_observations_are_loaded_and_excluded_from_abc():
    from examples.campanula_izu.observed_data import load_future_observations

    rows = load_future_observations()
    names = {row["candidate"] for row in rows}
    assert "guide_removal_experiment" in names
    assert "Qst_Fst_comparison" in names
    assert all(row["role"] == "future_observation" for row in rows)
    assert all(row["epistemic_status"] == "pending_field_validation" for row in rows)


def test_numeric_gradient_and_categorical_transition_evaluators():
    from examples.campanula_izu.pattern_evaluator import evaluate_patterns

    outs = [
        SimpleNamespace(population="mainland", selfing_rate=0.10, flower_size=1.00),
        SimpleNamespace(population="Oshima", selfing_rate=0.30, flower_size=0.80),
        SimpleNamespace(population="Kozushima", selfing_rate=0.55, flower_size=0.65),
        SimpleNamespace(population="Hachijo", selfing_rate=0.85, flower_size=0.45),
    ]
    env = {
        "mainland": {"distance_from_mainland": 0.0},
        "Oshima": {"distance_from_mainland": 120.0},
        "Kozushima": {"distance_from_mainland": 170.0},
        "Hachijo": {"distance_from_mainland": 290.0},
    }
    rows = [
        {
            "pattern": "selfing_numeric_gradient",
            "type": "numeric_gradient",
            "variable": "selfing_rate",
            "predictor": "distance_from_mainland",
            "expected_direction": "positive",
            "weight": "1.0",
            "role": "observed_target",
        },
        {
            "pattern": "breeding_system_transition",
            "type": "categorical_transition",
            "variable": "breeding_system",
            "populations": "mainland;Oshima;Kozushima;Hachijo",
            "relation": "SI_outcrossing -> SC_mixed -> SC_mixed -> SC_selfing",
            "weight": "1.0",
            "role": "observed_target",
        },
    ]
    res = evaluate_patterns(outs, rows, env)
    assert res.n_total == 2
    assert res.n_matched == 2
