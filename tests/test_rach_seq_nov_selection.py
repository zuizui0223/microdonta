"""Direct tests that RACH-SEQ and single-shot NOV share one objective."""

from causal_model.causal_admissibility import CandidateObservation, CandidateOutcome
from causal_model.mechanism_equivalence import mechanism_equivalence_structure
from causal_model.nov_evsi import next_observation_evsi
from causal_model.rach_seq import (
    rach_seq,
    sequential_candidate_value,
    validated_nov_value,
)


class _SW:
    def __init__(self, name: str):
        self.name = name


def _rows():
    """A/B disjunction with a nuisance marker balanced inside every mechanism state."""
    rows = []
    for a, b in ((1, 0), (0, 1), (1, 1)):
        for marker in (0.0, 1.0):
            for _ in range(20):
                rows.append({
                    "A": bool(a),
                    "B": bool(b),
                    "pop_trait": 0.75 if a else 0.25,
                    "decoy_marker": marker,
                })
    return rows


def _resolver():
    return CandidateObservation(
        name="resolve_A",
        description="measure trait that reports A",
        target_switches=["A"],
        rationale="high iff A is active",
        outcomes=[
            CandidateOutcome(
                name="A_active",
                description="A active",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "trait",
                    "population": "pop",
                    "observed_value": "0.75",
                    "scale": "0.05",
                }],
            ),
            CandidateOutcome(
                name="A_inactive",
                description="A inactive",
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


def _decoy():
    return CandidateObservation(
        name="decoy",
        description="mechanism-independent marker",
        target_switches=[],
        rationale="negative-control candidate",
        outcomes=[
            CandidateOutcome(
                name="marker_0",
                description="marker zero",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "marker",
                    "population": "decoy",
                    "observed_value": "0.0",
                    "scale": "0.1",
                }],
            ),
            CandidateOutcome(
                name="marker_1",
                description="marker one",
                prior_probability=0.5,
                extra_pattern_rows=[{
                    "type": "absolute_summary",
                    "variable": "marker",
                    "population": "decoy",
                    "observed_value": "1.0",
                    "scale": "0.1",
                }],
            ),
        ],
    )


def test_verified_rach_seq_ranking_is_the_same_nov_used_by_single_shot_api():
    rows = _rows()
    switches = [_SW("A"), _SW("B")]
    resolver = _resolver()
    decoy = _decoy()

    resolver_nov = validated_nov_value(resolver, rows, switches)
    decoy_nov = validated_nov_value(decoy, rows, switches)
    assert resolver_nov is not None and resolver_nov > 0.0
    assert decoy_nov == 0.0

    single_shot = {
        result.candidate: result
        for result in next_observation_evsi(rows, switches, [resolver, decoy])
    }
    assert single_shot["resolve_A"].evsi == round(resolver_nov, 4)
    assert single_shot["decoy"].evsi == 0.0

    seq = rach_seq(
        rows,
        switches,
        # Put the decoy first so success cannot come from candidate list order.
        [decoy, resolver],
        budget=1,
        outcome_overrides={"resolve_A": "A_active"},
    )
    assert seq.observations_taken == ["resolve_A"]
    step = seq.steps[1]
    ranking = dict(step.candidate_ranking)
    assert ranking["resolve_A"] == resolver_nov
    assert ranking["decoy"] == 0.0
    assert step.candidate_score_sources["resolve_A"] == "validated_nov"
    assert step.candidate_score_sources["decoy"] == "validated_nov"


def test_unverified_candidate_is_explicit_normalized_edge_cut_fallback():
    rows = _rows()
    switches = [_SW("A"), _SW("B")]
    structure = mechanism_equivalence_structure(rows, switches)
    assert structure.edges

    legacy = CandidateObservation(
        name="legacy_target_A",
        description="legacy candidate without outcome map",
        target_switches=["A"],
        rationale="compatibility fallback only",
        outcomes=[],
    )
    value, source = sequential_candidate_value(
        legacy,
        rows,
        switches,
        structure,
    )
    assert source == "normalized_edge_cut_fallback"
    assert 0.0 <= value <= 1.0
    assert validated_nov_value(legacy, rows, switches) is None
