"""Controlled witness separating current resolvability from evidence gain.

MROD reports

    D(A) = H(S | A)
    R(A) = 1 - H(S | A) / K

for the current admissible mechanism distribution.  R(A) is an absolute state
summary relative to the maximum K-bit entropy.  It is not, by itself, the amount
of information supplied by the current observations: a concentrated pre-data
prior or pre-data constraint grammar can already make R(A) positive.

For a candidate next observation Q, by contrast,

    V(Q) = I(S; Q | A) / K

is an incremental expected information quantity relative to the current state.

The witness has two parts.

1. A single binary mechanism has a pre-observation distribution P(S=1)=0.9.
   No observed target has yet been applied, but R=1-H2(0.9)=0.5310.  A candidate
   that reads S exactly has 0.468996 bit of mutual information, while a candidate
   independent of S has zero information.  Thus positive current R need not be
   observational evidence gain, whereas candidate V remains incremental.

2. A two-switch audit shows that candidate ranking can depend on the declared
   prior/current mechanism distribution.  With A balanced and B concentrated at
   0.9, observing A is more informative; swapping those concentrations makes
   observing B more informative.  This is expected conditional design behaviour,
   not a prior-invariance claim.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model import (
    CandidateObservation,
    CandidateOutcome,
    mechanism_entropy,
    mechanism_resolvability,
    observation_information_value,
)


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class PriorEvidenceWitness:
    baseline_entropy_bits: float
    baseline_resolvability: float
    signal_information_bits: float
    signal_value: float
    noise_information_bits: float
    noise_value: float
    expected_resolvability_after_signal: float


@dataclass(frozen=True)
class PriorRankingSensitivity:
    first_prior_information_bits: dict[str, float]
    second_prior_information_bits: dict[str, float]
    first_best: str
    second_best: str


def _outcome(name: str, variable: str, value: float) -> CandidateOutcome:
    return CandidateOutcome(
        name=name,
        description=f"{variable} around {value}",
        prior_probability=0.5,
        extra_pattern_rows=[
            {
                "type": "absolute_summary",
                "variable": variable,
                "population": "p",
                "observed_value": str(value),
                "scale": "0.05",
            }
        ],
    )


def _binary_candidate(name: str, variable: str, target: str) -> CandidateObservation:
    return CandidateObservation(
        name=name,
        description=f"Binary observation of {target}.",
        target_switches=[target],
        rationale="Controlled information-theoretic witness.",
        outcomes=[
            _outcome(f"{name}_high", variable, 0.75),
            _outcome(f"{name}_low", variable, 0.25),
        ],
    )


def skewed_baseline_rows() -> list[dict]:
    """Return P(S=True)=0.9 with an independent balanced nuisance observation."""
    rows: list[dict] = []
    for state, count in ((True, 90), (False, 10)):
        # Split the nuisance outcome exactly 50/50 inside each mechanism state.
        half = count // 2
        for i in range(count):
            rows.append(
                {
                    "S": state,
                    "p_q_signal": 0.75 if state else 0.25,
                    "p_q_noise": 0.75 if i < half else 0.25,
                }
            )
    return rows


def evaluate_prior_evidence_separation() -> PriorEvidenceWitness:
    """Evaluate absolute current R and incremental candidate information."""
    rows = skewed_baseline_rows()
    switches = [_Switch("S")]
    candidates = [
        _binary_candidate("observe_S", "q_signal", "S"),
        _binary_candidate("observe_noise", "q_noise", "S"),
    ]
    result = {
        item.candidate: item
        for item in observation_information_value(rows, switches, candidates)
    }
    signal = result["observe_S"]
    noise = result["observe_noise"]
    if signal.expected_resolvability is None:
        raise RuntimeError("signal candidate unexpectedly non-estimable")
    return PriorEvidenceWitness(
        baseline_entropy_bits=mechanism_entropy(rows, switches),
        baseline_resolvability=mechanism_resolvability(rows, switches),
        signal_information_bits=float(signal.mutual_information_bits or 0.0),
        signal_value=float(signal.information_value or 0.0),
        noise_information_bits=float(noise.mutual_information_bits or 0.0),
        noise_value=float(noise.information_value or 0.0),
        expected_resolvability_after_signal=float(signal.expected_resolvability),
    )


def _two_switch_rows(*, p_a: float, p_b: float, scale: int = 100) -> list[dict]:
    """Construct an exact empirical product distribution for two decimal priors."""
    n_a_on = int(round(p_a * scale))
    n_b_on = int(round(p_b * scale))
    if not (0 <= n_a_on <= scale and 0 <= n_b_on <= scale):
        raise ValueError("prior probabilities must lie in [0,1]")

    rows: list[dict] = []
    # Cross product of equally weighted A and B index lists gives an exact
    # product empirical distribution with scale**2 rows.
    for ia in range(scale):
        a = ia < n_a_on
        for ib in range(scale):
            b = ib < n_b_on
            rows.append(
                {
                    "A": a,
                    "B": b,
                    "p_qA": 0.75 if a else 0.25,
                    "p_qB": 0.75 if b else 0.25,
                }
            )
    return rows


def _direct_ranking(rows: list[dict]) -> tuple[dict[str, float], str]:
    switches = [_Switch("A"), _Switch("B")]
    candidates = [
        _binary_candidate("observe_A", "qA", "A"),
        _binary_candidate("observe_B", "qB", "B"),
    ]
    result = observation_information_value(rows, switches, candidates)
    bits = {
        item.candidate: float(item.mutual_information_bits or 0.0)
        for item in result
    }
    best = max(result, key=lambda item: item.information_value or 0.0).candidate
    return bits, best


def evaluate_prior_ranking_sensitivity() -> PriorRankingSensitivity:
    """Swap prior concentrations and show the information ranking swaps too."""
    first_bits, first_best = _direct_ranking(
        _two_switch_rows(p_a=0.5, p_b=0.9)
    )
    second_bits, second_best = _direct_ranking(
        _two_switch_rows(p_a=0.9, p_b=0.5)
    )
    return PriorRankingSensitivity(
        first_prior_information_bits=first_bits,
        second_prior_information_bits=second_bits,
        first_best=first_best,
        second_best=second_best,
    )


if __name__ == "__main__":
    state = evaluate_prior_evidence_separation()
    sensitivity = evaluate_prior_ranking_sensitivity()
    print("baseline entropy bits:", state.baseline_entropy_bits)
    print("baseline resolvability:", state.baseline_resolvability)
    print("signal MI/value:", state.signal_information_bits, state.signal_value)
    print("noise MI/value:", state.noise_information_bits, state.noise_value)
    print("expected R after signal:", state.expected_resolvability_after_signal)
    print("prior ranking 1:", sensitivity.first_prior_information_bits, sensitivity.first_best)
    print("prior ranking 2:", sensitivity.second_prior_information_bits, sensitivity.second_best)
