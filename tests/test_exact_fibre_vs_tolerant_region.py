"""An exact structural zero must not be applied to a thickened region."""
from __future__ import annotations

import pytest

from causal_model.mechanism_region import CandidateObservation, CandidateOutcome
from causal_model.target_observation_value import target_observation_information_value


def test_refining_imprecise_O_can_help_even_when_Q_is_a_function_of_exact_O():
    worlds = [{"T": 0, "exact_O": 0.0, "probe_O": 0.0},
              {"T": 1, "exact_O": 1.0, "probe_O": 1.0}]
    observed, tolerance = 0.5, 0.5
    accepted = [w for w in worlds if abs(w["exact_O"] - observed) <= tolerance]
    # Q equals the latent exact O. It is not a recoding of the coarse record 0.5.
    candidate = CandidateObservation(
        name="read_exact_O", description="Refine the imprecisely known O",
        target_switches=[], rationale="Controlled exact/tolerant conditioning audit",
        outcomes=[CandidateOutcome(
            name=str(value), description=str(value), prior_probability=0.5,
            extra_pattern_rows=[{"type": "absolute_summary", "population": "probe",
                                 "variable": "O", "observed_value": str(value),
                                 "scale": "0.01"}],
        ) for value in (0, 1)],
    )
    coarse = target_observation_information_value(
        accepted, [candidate], target_columns=["T"])[0]
    assert coarse.estimable and coarse.partition_verified
    assert coarse.mutual_information_bits == pytest.approx(1.0)
    for exact in (0.0, 1.0):
        fibre = [w for w in accepted if w["exact_O"] == exact]
        conditioned = target_observation_information_value(
            fibre, [candidate], target_columns=["T"])[0]
        assert conditioned.estimable
        assert conditioned.mutual_information_bits == 0.0
