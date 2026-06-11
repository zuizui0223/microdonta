from __future__ import annotations

import csv
from pathlib import Path


def test_absolute_observations_load_and_keep_pending_out_of_targets():
    from examples.campanula_izu.observed_data import (
        future_absolute_observations,
        load_absolute_observations,
        observed_absolute_targets,
    )

    rows = load_absolute_observations()
    assert rows
    assert {"observed_value", "se", "scale", "weight"}.issubset(rows[0])
    assert observed_absolute_targets() == []

    future = future_absolute_observations()
    names = {row["observation"] for row in future}
    assert {"guide_area_abs", "herkogamy_abs", "Fis_abs", "bagging_seed_set_abs"} <= names
    assert all(row["role"] != "observed_target" or row["observed_value"] is None for row in future)


def test_observed_absolute_targets_require_value_and_non_pending_status(tmp_path: Path):
    from examples.campanula_izu.observed_data import observed_absolute_targets

    p = tmp_path / "abs.csv"
    rows = [
        {
            "observation": "measured_flower",
            "variable": "flower_size",
            "population": "Oshima",
            "observed_value": "0.8",
            "se": "0.1",
            "scale": "",
            "weight": "0.8",
            "source": "field",
            "role": "observed_target",
            "epistemic_status": "field_derived",
            "notes": "measured",
        },
        {
            "observation": "pending_guide",
            "variable": "nectar_guide",
            "population": "Oshima",
            "observed_value": "0.2",
            "se": "0.1",
            "scale": "",
            "weight": "1.0",
            "source": "field",
            "role": "observed_target",
            "epistemic_status": "pending_field_validation",
            "notes": "pending",
        },
    ]
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    targets = observed_absolute_targets(p)
    assert [row["observation"] for row in targets] == ["measured_flower"]
    assert targets[0]["observed_value"] == 0.8
    assert targets[0]["se"] == 0.1
