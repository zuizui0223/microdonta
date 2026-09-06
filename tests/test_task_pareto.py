from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.task_pareto import pareto_front_candidates, task_pareto_values


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate(name: str, variable: str) -> CandidateObservation:
    return CandidateObservation(
        name=name,
        description=f"measure {variable}",
        target_switches=["A"],
        rationale="finite task-Pareto witness",
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
    for mechanism in (False, True):
        for target in ("low", "high"):
            for noise in ("low", "high"):
                rows.extend(
                    {
                        "A": mechanism,
                        "target": target,
                        "pop_mech": 0.75 if mechanism else 0.25,
                        "pop_target_signal": 0.75 if target == "high" else 0.25,
                        "pop_noise": 0.75 if noise == "high" else 0.25,
                    }
                    for _ in range(10)
                )
    return rows


def test_mechanism_only_and_target_only_candidates_form_two_point_pareto_front():
    candidates = [
        _candidate("measure_mechanism", "mech"),
        _candidate("measure_target", "target_signal"),
        _candidate("measure_noise", "noise"),
    ]
    results = task_pareto_values(
        _rows(),
        [_SW("A")],
        candidates,
        target_columns=["target"],
    )
    by_name = {row.candidate: row for row in results}

    assert by_name["measure_mechanism"].mechanism_value == 1.0
    assert by_name["measure_mechanism"].target_value == 0.0
    assert by_name["measure_target"].mechanism_value == 0.0
    assert by_name["measure_target"].target_value == 1.0
    assert by_name["measure_noise"].mechanism_value == 0.0
    assert by_name["measure_noise"].target_value == 0.0

    assert set(pareto_front_candidates(results)) == {
        "measure_mechanism",
        "measure_target",
    }
    assert by_name["measure_noise"].dominated_by == (
        "measure_mechanism",
        "measure_target",
    )


def test_nonestimable_dimension_is_not_silently_replaced_by_zero():
    candidate = CandidateObservation(
        name="unmapped",
        description="no outcome map",
        target_switches=["A"],
        rationale="non-estimable witness",
        outcomes=[],
    )
    row = task_pareto_values(
        _rows(),
        [_SW("A")],
        [candidate],
        target_columns=["target"],
    )[0]
    assert not row.jointly_estimable
    assert row.mechanism_value is None
    assert row.target_value is None
    assert not row.pareto_nondominated
