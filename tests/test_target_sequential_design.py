from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.observation_information import candidate_mutual_information_bits
from causal_model.target_observation_value import candidate_target_mutual_information_bits
from causal_model.target_sequential_design import target_sequential_observation_design


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate(name: str, variable: str, target_switches: list[str]):
    return CandidateObservation(
        name=name,
        description=f"measure {variable}",
        target_switches=target_switches,
        rationale="two-level verified partition",
        outcomes=[
            CandidateOutcome(
                name="high",
                description="high",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": variable,
                    "population": "pop",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            CandidateOutcome(
                name="low",
                description="low",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": variable,
                    "population": "pop",
                    "observed_value": "0.25",
                    "scale": "0.05",
                }],
            ),
        ],
    )


def _rows():
    rows = []
    for a in (False, True):
        for target in ("low", "high"):
            for _ in range(20):
                rows.append({
                    "A": a,
                    "pop_mech": 0.75 if a else 0.25,
                    "pop_trait": 0.75 if target == "high" else 0.25,
                    "target_sign": target,
                })
    return rows


def test_mechanism_and_target_objectives_reverse_first_choice():
    rows = _rows()
    mechanism_candidate = _candidate("measure_mechanism", "mech", ["A"])
    target_candidate = _candidate("measure_target", "trait", [])

    mechanism_values = {
        candidate.name: candidate_mutual_information_bits(rows, [_SW("A")], candidate)
        for candidate in (mechanism_candidate, target_candidate)
    }
    target_values = {
        candidate.name: candidate_target_mutual_information_bits(
            rows, candidate, ["target_sign"]
        )
        for candidate in (mechanism_candidate, target_candidate)
    }

    assert mechanism_values == {
        "measure_mechanism": 1.0,
        "measure_target": 0.0,
    }
    assert target_values == {
        "measure_mechanism": 0.0,
        "measure_target": 1.0,
    }

    # Only the selected target candidate receives a realised-outcome entry. This
    # also guards the rule that outcomes of unselected candidates are not read.
    result = target_sequential_observation_design(
        rows,
        [mechanism_candidate, target_candidate],
        target_columns=["target_sign"],
        realised_outcomes={"measure_target": "high"},
        budget=1,
    )
    assert result.steps[0].candidate == "measure_target"
    assert result.steps[0].realised_outcome == "high"
    assert result.initial_target_entropy_bits == 1.0
    assert result.final_target_entropy_bits == 0.0
    assert result.target_identified
    assert result.stop_reason == "target_identified_at_budget"


def test_target_policy_stops_without_spending_budget_when_target_is_already_identified():
    rows = [{"pop_trait": 0.75, "target": "same"} for _ in range(20)]
    candidate = _candidate("measure_target", "trait", [])
    result = target_sequential_observation_design(
        rows,
        [candidate],
        target_columns=["target"],
        realised_outcomes={},
        budget=3,
    )
    assert result.target_identified
    assert result.stop_reason == "target_identified"
    assert result.steps == ()
