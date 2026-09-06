"""Existing target-information API versus an independent finite-map oracle.

The pinned fixture is mirrored in Boundary. There is no cross-repository import,
network dependency, changed publication estimand, or ecological truth claim.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.observation_information import candidate_mutual_information_bits
from causal_model.sequential_observation import filter_by_outcome
from causal_model.target_observation_value import target_entropy_bits, target_observation_information_value

FIXTURE = Path(__file__).parent / "fixtures" / "target_factorization_v1.json"
FIXTURE_SHA256 = "d12478f3354170130a8ed11e0c019a0099f5dc942d4365195770619ae3f14841"


def _cases():
    return json.loads(FIXTURE.read_text())["cases"]


def _rows(case):
    rows = [dict(zip(case["columns"], values)) for values in case["rows"]]
    return [dict(r, **{f"probe_{q}": r[q] for q in case["candidates"]}) for r in rows]


def _candidate(rows, name):
    values = sorted({r[name] for r in rows})
    return CandidateObservation(
        name=name, description="Controlled deterministic measurement",
        target_switches=[], rationale="Finite-map bridge audit, not empirical evidence",
        outcomes=[CandidateOutcome(
            name=f"state_{v}", description=str(v), prior_probability=1 / len(values),
            extra_pattern_rows=[{"type": "absolute_summary", "population": "probe",
                                 "variable": name, "observed_value": str(v), "scale": "0.01"}],
        ) for v in values],
    )


def _factors(rows, keys):
    return all(tuple(a[k] for k in keys) != tuple(b[k] for k in keys) or a["T"] == b["T"]
               for a in rows for b in rows)


def _conditional_entropy(rows, keys):
    groups = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    return sum(len(sub) / len(rows) * target_entropy_bits(sub, ["T"])
               for sub in groups.values())


def test_fixture_is_identical_to_boundary_contract_version():
    assert sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256
    assert json.loads(FIXTURE.read_text())["contract_id"] == "boundary-mrod-target-factorization-v1"


def test_full_support_factorization_iff_zero_entropy_and_complete_repair():
    for case in _cases():
        rows = _rows(case)
        expected = case["expected"]
        current_h = _conditional_entropy(rows, ["O"])
        assert current_h == pytest.approx(expected["target_conditional_entropy_bits"])
        assert _factors(rows, ["O"]) == expected["factors"]
        assert (current_h < 1e-12) == expected["factors"]
        for name in case["candidates"]:
            candidate = _candidate(rows, name)
            information = 0.0
            expected_remaining = 0.0
            # Condition on O first: each subset is the current A_y, not new data.
            for observed in {r["O"] for r in rows}:
                sub = [r for r in rows if r["O"] == observed]
                result = target_observation_information_value(
                    sub, [candidate], target_columns=["T"])[0]
                assert result.estimable and result.partition_verified
                information += len(sub) / len(rows) * result.mutual_information_bits
                for outcome in candidate.outcomes:
                    after = filter_by_outcome(sub, outcome.extra_pattern_rows)
                    if after:
                        expected_remaining += len(after) / len(rows) * target_entropy_bits(after, ["T"])
            assert information == pytest.approx(expected["candidate_information_bits"][name])
            assert current_h - information == pytest.approx(expected_remaining)
            repaired = _factors(rows, ["O", name])
            assert repaired == expected["repairs"][name]
            assert (expected_remaining < 1e-12) == repaired


def test_already_resolved_question_still_allows_two_bits_of_mechanism_learning():
    case = next(c for c in _cases() if c["name"] == "question_resolved_detail_unresolved")
    rows = _rows(case)
    deep = _candidate(rows, "deep")
    switches = [SimpleNamespace(name=name) for name in ("T", "U1", "U2")]
    assert target_entropy_bits(rows, ["T"]) == 0.0
    assert candidate_mutual_information_bits(rows, switches, deep) == pytest.approx(2.0)
    target = target_observation_information_value(rows, [deep], target_columns=["T"])[0]
    assert target.target_already_identified
    assert target.mutual_information_bits == 0.0


def test_positive_information_can_leave_target_unresolved():
    case = next(c for c in _cases() if c["name"] == "positive_information_is_not_complete_repair")
    rows = _rows(case)
    result = target_observation_information_value(rows, [_candidate(rows, "partial")], target_columns=["T"])[0]
    assert result.mutual_information_bits > 0.0
    assert _conditional_entropy(rows, ["O", "partial"]) == pytest.approx(2 / 3)
    assert not _factors(rows, ["O", "partial"])


def test_zero_weight_or_omitted_world_can_fake_entropy_resolution():
    case = next(c for c in _cases() if c["name"] == "zero_mass_is_not_structural_exclusion")
    rows = _rows(case)
    masses = Counter()
    for row, weight in zip(rows, case["diagnostic_weights"]):
        masses[row["T"]] += weight
    weighted_h = -sum(p * math.log2(p) for p in masses.values() if p > 0.0)
    assert weighted_h == case["expected"]["weighted_target_entropy_bits"] == 0.0
    assert not _factors(rows, ["O"])
    assert target_entropy_bits(rows, ["T"]) == 1.0
    assert target_entropy_bits(rows[:1], ["T"]) == 0.0
    # Neither zero weight nor finite-pool omission proves structural exclusion.


def test_zero_registered_candidate_value_does_not_identify_target():
    case = next(c for c in _cases() if c["name"] == "unresolved_question")
    rows = _rows(case)
    zero_candidates = [_candidate(rows, name) for name in ("deep", "repeat")]
    values = target_observation_information_value(rows, zero_candidates, target_columns=["T"])
    assert all(v.estimable and v.mutual_information_bits == 0.0 for v in values)
    assert target_entropy_bits(rows, ["T"]) == 1.0
    assert not _factors(rows, ["O"])
