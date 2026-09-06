"""Controlled witness for tolerance-sensitive next-observation ranking.

MROD conditions candidate information on the current admissible mechanism region
A_epsilon.  Changing the acceptance tolerance can therefore change not only the
size of the retained region, but its mechanism composition and the ranking of
candidate follow-up observations.

This witness uses a single fixed pool of states with row-level discrepancy
scores.  The strict region (epsilon=0.10) is a subset of the loose region
(epsilon=0.20).  Candidate ``observe_A`` reads mechanism A exactly and
``observe_B`` reads B exactly.

Under the strict region A is balanced while B is concentrated, so observe_A has
more mechanism information.  The additional rows admitted at the looser
tolerance make A more concentrated but B nearly balanced, reversing the
candidate ranking.  The construction demonstrates existence only; it does not
claim that every tolerance change causes a ranking reversal.
"""
from __future__ import annotations

from dataclasses import dataclass

from causal_model import CandidateObservation, CandidateOutcome, observation_information_value


STRICT_EPSILON = 0.10
LOOSE_EPSILON = 0.20


@dataclass(frozen=True)
class _Switch:
    name: str


@dataclass(frozen=True)
class ToleranceSensitivityWitness:
    strict_n: int
    loose_n: int
    strict_information_bits: dict[str, float]
    loose_information_bits: dict[str, float]
    strict_values: dict[str, float]
    loose_values: dict[str, float]
    strict_best: str
    loose_best: str
    common_best: tuple[str, ...]


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


def candidate_observations() -> list[CandidateObservation]:
    return [
        CandidateObservation(
            name="observe_A",
            description="Directly observe mechanism coordinate A.",
            target_switches=["A"],
            rationale="Information equals the current entropy of A in this deterministic witness.",
            outcomes=[
                _outcome("A_on", "qA", 0.75),
                _outcome("A_off", "qA", 0.25),
            ],
        ),
        CandidateObservation(
            name="observe_B",
            description="Directly observe mechanism coordinate B.",
            target_switches=["B"],
            rationale="Information equals the current entropy of B in this deterministic witness.",
            outcomes=[
                _outcome("B_on", "qB", 0.75),
                _outcome("B_off", "qB", 0.25),
            ],
        ),
    ]


def _make_row(a: bool, b: bool, discrepancy: float) -> dict:
    return {
        "A": a,
        "B": b,
        "discrepancy": discrepancy,
        "p_qA": 0.75 if a else 0.25,
        "p_qB": 0.75 if b else 0.25,
    }


def evaluated_rows(repeats: int = 1) -> list[dict]:
    """Return one fixed evaluated pool with strict-core and loose-only rows."""
    if repeats < 1:
        raise ValueError("repeats must be positive")

    rows: list[dict] = []
    # Strict core: A is balanced (5/10 ON) while B is concentrated (2/10 ON).
    core_counts = {
        (False, False): 4,
        (True, False): 4,
        (False, True): 1,
        (True, True): 1,
    }
    for (a, b), count in core_counts.items():
        for _ in range(count * repeats):
            rows.append(_make_row(a, b, STRICT_EPSILON))

    # Loose-only rows: adding A=0,B=1 makes A concentrated and B nearly balanced.
    for _ in range(8 * repeats):
        rows.append(_make_row(False, True, LOOSE_EPSILON))
    return rows


def accepted_rows(rows: list[dict], epsilon: float) -> list[dict]:
    """Filter one evaluated pool by a scalar acceptance tolerance."""
    return [row for row in rows if float(row["discrepancy"]) <= epsilon]


def _score(rows: list[dict]) -> tuple[dict[str, float], dict[str, float], str]:
    switches = [_Switch("A"), _Switch("B")]
    results = observation_information_value(rows, switches, candidate_observations())
    bits = {item.candidate: float(item.mutual_information_bits or 0.0) for item in results}
    values = {item.candidate: float(item.information_value or 0.0) for item in results}
    best = max(values, key=values.get)
    return bits, values, best


def _argmax_set(values: dict[str, float], tol: float = 1e-12) -> set[str]:
    maximum = max(values.values())
    return {name for name, value in values.items() if abs(value - maximum) <= tol}


def evaluate_tolerance_sensitivity(repeats: int = 1) -> ToleranceSensitivityWitness:
    """Evaluate candidate information under nested strict and loose regions."""
    pool = evaluated_rows(repeats)
    strict = accepted_rows(pool, STRICT_EPSILON)
    loose = accepted_rows(pool, LOOSE_EPSILON)
    if not set(map(id, strict)).issubset(set(map(id, loose))):
        raise RuntimeError("strict accepted region must be nested inside loose region")

    strict_bits, strict_values, strict_best = _score(strict)
    loose_bits, loose_values, loose_best = _score(loose)
    common = tuple(sorted(_argmax_set(strict_values) & _argmax_set(loose_values)))

    return ToleranceSensitivityWitness(
        strict_n=len(strict),
        loose_n=len(loose),
        strict_information_bits=strict_bits,
        loose_information_bits=loose_bits,
        strict_values=strict_values,
        loose_values=loose_values,
        strict_best=strict_best,
        loose_best=loose_best,
        common_best=common,
    )


if __name__ == "__main__":
    result = evaluate_tolerance_sensitivity()
    print("strict n / loose n:", result.strict_n, result.loose_n)
    print("strict MI:", result.strict_information_bits)
    print("loose MI:", result.loose_information_bits)
    print("strict best / loose best:", result.strict_best, result.loose_best)
    print("common best:", result.common_best)
