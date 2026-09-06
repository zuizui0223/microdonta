"""Controlled witness for pre-data versus post-data candidate ranking.

This module is deliberately a small conceptual diagnostic, not a new benchmark
and not a comparison against any named prior-art method.  It shows one fact that
matters for MROD's post-current-data formulation:

    a candidate ranking computed before current evidence is observed need not be
    preserved after conditioning on that evidence.

The construction uses two binary mechanism coordinates, A and B, with four
uniform prior states.  Current evidence later fixes A=False while leaving B
unresolved.

Two candidate observations are available:

* ``observe_A`` reads A exactly.  Before current evidence it carries 1 bit about
  the joint mechanism vector and is the higher-value candidate.  After A=False
  is already known, it is constant and carries 0 bits.
* ``observe_B_when_A0`` is positive only for state (A=False, B=True).  Before
  current evidence its entropy is h2(1/4) ~= 0.811278 bit, below ``observe_A``.
  After conditioning on A=False it reads B exactly and carries 1 bit.

Thus the candidate ranking reverses.  The point is not that pre-data design is
inferior: it is that a post-data next-observation problem must condition on the
current evidence rather than reuse an earlier ranking unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model import CandidateObservation, CandidateOutcome, observation_information_value


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class ReprioritizationWitness:
    prior_information_bits: dict[str, float]
    current_information_bits: dict[str, float]
    prior_values: dict[str, float]
    current_values: dict[str, float]
    prior_best: str
    current_best: str
    prior_n: int
    current_n: int


def _band_outcome(name: str, variable: str, value: float) -> CandidateOutcome:
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


def candidate_observations() -> list[CandidateObservation]:
    """Return the two candidates used by the ranking-reversal witness."""
    return [
        CandidateObservation(
            name="observe_A",
            description="Directly observe mechanism coordinate A.",
            target_switches=["A"],
            rationale="Pre-data resolver that becomes redundant once current evidence fixes A.",
            outcomes=[
                _band_outcome("A_on", "q1", 0.75),
                _band_outcome("A_off", "q1", 0.25),
            ],
        ),
        CandidateObservation(
            name="observe_B_when_A0",
            description="Observe a response that reads B only on the A=False branch.",
            target_switches=["B"],
            rationale="Lower pre-data information but fully resolves the remaining B ambiguity after A=False.",
            outcomes=[
                _band_outcome("conditional_B_on", "q2", 0.75),
                _band_outcome("conditional_B_off", "q2", 0.25),
            ],
        ),
    ]


def prior_rows(repeats_per_state: int = 20) -> list[dict]:
    """Uniform four-state prior-predictive row set for (A,B)."""
    if repeats_per_state < 1:
        raise ValueError("repeats_per_state must be positive")
    rows: list[dict] = []
    for a in (False, True):
        for b in (False, True):
            q1 = 0.75 if a else 0.25
            q2 = 0.75 if ((not a) and b) else 0.25
            rows.extend(
                {
                    "A": a,
                    "B": b,
                    "p_q1": q1,
                    "p_q2": q2,
                }
                for _ in range(repeats_per_state)
            )
    return rows


def current_rows(rows: list[dict]) -> list[dict]:
    """Condition the witness on current evidence A=False."""
    return [row for row in rows if not bool(row["A"])]


def _score(rows: list[dict]) -> tuple[dict[str, float], dict[str, float]]:
    switches = [_Switch("A"), _Switch("B")]
    results = observation_information_value(rows, switches, candidate_observations())
    bits = {
        result.candidate: float(result.mutual_information_bits or 0.0)
        for result in results
    }
    values = {
        result.candidate: float(result.information_value or 0.0)
        for result in results
    }
    if set(bits) != {"observe_A", "observe_B_when_A0"}:
        raise RuntimeError("unexpected candidate set in reprioritization witness")
    return bits, values


def evaluate_reprioritization(repeats_per_state: int = 20) -> ReprioritizationWitness:
    """Evaluate candidate information before and after current evidence."""
    before = prior_rows(repeats_per_state)
    after = current_rows(before)
    prior_bits, prior_values = _score(before)
    current_bits, current_values = _score(after)
    prior_best = max(prior_values, key=prior_values.get)
    current_best = max(current_values, key=current_values.get)
    return ReprioritizationWitness(
        prior_information_bits=prior_bits,
        current_information_bits=current_bits,
        prior_values=prior_values,
        current_values=current_values,
        prior_best=prior_best,
        current_best=current_best,
        prior_n=len(before),
        current_n=len(after),
    )


if __name__ == "__main__":
    result = evaluate_reprioritization()
    print("pre-data information bits:", result.prior_information_bits)
    print("post-data information bits:", result.current_information_bits)
    print("pre-data best:", result.prior_best)
    print("post-data best:", result.current_best)
