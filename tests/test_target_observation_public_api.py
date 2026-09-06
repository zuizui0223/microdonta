import causal_model as method


class _SW:
    def __init__(self, name: str):
        self.name = name


def _candidate():
    return method.CandidateObservation(
        name="measure_trait",
        description="measure high/low trait",
        target_switches=["A"],
        rationale="candidate partitions current rows by trait",
        outcomes=[
            method.CandidateOutcome(
                name="high",
                description="high",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            method.CandidateOutcome(
                name="low",
                description="low",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.25",
                    "scale": "0.05",
                }],
            ),
        ],
    )


def test_public_api_exposes_target_value_without_replacing_mechanism_value():
    rows = []
    for mechanism in (False, True):
        rows.extend(
            {"A": mechanism, "pop_trait": 0.25, "target_sign": "low"}
            for _ in range(20)
        )
        rows.extend(
            {"A": mechanism, "pop_trait": 0.75, "target_sign": "high"}
            for _ in range(20)
        )

    candidate = _candidate()
    mechanism_bits = method.candidate_mutual_information_bits(
        rows, [_SW("A")], candidate
    )
    target_bits = method.candidate_target_mutual_information_bits(
        rows, candidate, ["target_sign"]
    )
    target_value = method.target_observation_information_value(
        rows, [candidate], target_columns=["target_sign"]
    )[0]

    assert mechanism_bits == 0.0
    assert target_bits == 1.0
    assert target_value.normalized_target_value == 1.0
    assert method.observation_information_value(
        rows, [_SW("A")], [candidate]
    )[0].information_value == 0.0


def test_public_api_exports_explicit_target_entropy():
    rows = [{"target": "low"}, {"target": "high"}] * 10
    assert method.target_entropy_bits(rows, ["target"]) == 1.0
    assert "target_observation_information_value" in method.__all__
    assert "observation_information_value" in method.__all__
