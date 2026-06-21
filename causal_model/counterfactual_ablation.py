"""Counterfactual ablation of a single causal mechanism from A_ε.

The core operation of the Causal Replaceability framework: force switch j
OFF (s_j = 0) and retain only those accepted draws that *already have* s_j
inactive.  This produces a sub-region of A_ε representing the counterfactual
world where mechanism j does not operate.

Why filtering, not re-simulation
---------------------------------
Filtering A_ε to s_j=0 rows is valid when the forward model is evaluated
over all switch combinations during the original ABC run (as Tier-A
modules do: each draw samples s independently from the prior). The sub-region
A_ε ∩ {s_j=0} is then an exact Monte-Carlo sample of the ablated posterior.

If the original ABC ran with s_j *always on* (a conditional run), filtering
would be inapplicable. Tier-A modules guard against this: every switch is
sampled from its prior (p = 0.5) on every draw, so every sub-combination
appears with positive prior probability.

The ablation is exact under the deterministic proxy simulator (same proof as
the RACH-SEQ filter step — see nov_calibration.py).
"""
from __future__ import annotations


def ablate_switch(accepted_rows: list[dict], switch_name: str) -> list[dict]:
    """Filter A_ε to rows where *switch_name* is OFF (counterfactual ablation).

    Parameters
    ----------
    accepted_rows:
        The full admissible region.  Each row must have ``switch_name`` as a
        key; falsy values (False, 0, None, "") are treated as OFF.
    switch_name:
        The mechanism to counterfactually remove.

    Returns
    -------
    list[dict]
        Sub-region where ``s_{switch_name} = 0``.  May be empty (→ CRC = ∞).
    """
    return [r for r in accepted_rows if not r.get(switch_name)]


def ablation_fraction(accepted_rows: list[dict], switch_name: str) -> float:
    """Fraction of A_ε surviving the ablation of *switch_name*.

    Equal to ``P(s_j = 0 | A_ε) = 1 − CA_j``.

    Returns 0.0 for an empty region (NaN-safe: returns 0.0 not NaN because
    an empty region has no draws to ablate, so the fraction is undefined; 0.0
    signals "completely irreplaceable" in the caller).
    Returns 1.0 if *switch_name* is absent from all rows (always OFF).
    """
    n = len(accepted_rows)
    if n == 0:
        return 0.0
    n_ablated = sum(1 for r in accepted_rows if not r.get(switch_name))
    return n_ablated / n


def ablate_all_switches(
    accepted_rows: list[dict],
    switch_names: list[str],
) -> dict[str, list[dict]]:
    """Ablate each switch individually and return the sub-regions.

    Returns
    -------
    dict
        ``{switch_name: ablated_rows}`` for each name in *switch_names*.
    """
    return {name: ablate_switch(accepted_rows, name) for name in switch_names}
