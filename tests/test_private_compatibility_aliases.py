from __future__ import annotations

import importlib

import causal_model


ALIASES = {
    "causal_admissibility": "mechanism_region",
    "causal_replaceability": "mechanism_replaceability_core",
    "rach_seq": "sequential_observation",
    "nov_evsi": "observation_information",
    "nov_calibration": "information_value_calibration_core",
    "rach_set": "joint_observation_set",
    "replaceability_nov": "replaceability_observation_value",
}


def test_historical_import_aliases_resolve_to_canonical_backends() -> None:
    for alias, canonical in ALIASES.items():
        alias_module = importlib.import_module(f"causal_model.{alias}")
        canonical_module = importlib.import_module(f"causal_model.{canonical}")
        assert alias_module is canonical_module


def test_historical_aliases_are_not_advertised_public_api() -> None:
    public = set(causal_model.__all__)
    assert not public.intersection(ALIASES)
