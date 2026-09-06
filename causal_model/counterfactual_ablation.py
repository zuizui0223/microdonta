"""Historical switch-off filtering helper for an admissible mechanism region.

Important scope note
--------------------
The module name is retained for compatibility with older internal code, but the
operation implemented here is **not**, by itself, identification of a causal
counterfactual in the potential-outcomes, intervention or do-calculus sense.
It simply restricts an already computed admissible region ``A_epsilon`` to rows
in which one declared mechanism switch is inactive:

    A_epsilon_off(j) = A_epsilon ∩ {s_j = 0}.

The resulting sub-region answers a set-membership / replaceability question
inside the declared simulator and prior family: were acceptable rows with that
switch already OFF present in the original region?  Calling this a
"counterfactual world" would overstate what filtering alone establishes.

Why filtering, not re-simulation
--------------------------------
Filtering ``A_epsilon`` to ``s_j=0`` rows is computationally valid for this
restricted sub-region calculation when the forward model was evaluated over
all switch combinations during the original run (as Tier-A modules do: each
draw samples ``s`` independently from the prior).  The sub-region is then a
Monte-Carlo sample of the original accepted draws satisfying ``s_j=0``.

If the original run conditioned on ``s_j`` always being ON, filtering is
inapplicable because the required support is absent.  Even when support is
present, this operation should not be relabelled as an identified intervention
effect unless a separate causal model and its identification assumptions justify
that interpretation.
"""
from __future__ import annotations


def ablate_switch(accepted_rows: list[dict], switch_name: str) -> list[dict]:
    """Restrict ``A_epsilon`` to rows where *switch_name* is OFF.

    Parameters
    ----------
    accepted_rows:
        The full admissible region. Each row must have ``switch_name`` as a
        key; falsy values (False, 0, None, "") are treated as OFF.
    switch_name:
        The declared mechanism switch to set-membership filter.

    Returns
    -------
    list[dict]
        Sub-region where ``s_{switch_name} = 0``. May be empty.

    Notes
    -----
    This is a compatibility-preserving historical API name. The returned
    sub-region is not automatically a causal intervention distribution.
    """
    return [r for r in accepted_rows if not r.get(switch_name)]


def ablation_fraction(accepted_rows: list[dict], switch_name: str) -> float:
    """Fraction of ``A_epsilon`` with *switch_name* already OFF.

    Equal to ``P(s_j = 0 | A_epsilon) = 1 - CA_j`` under the empirical accepted
    row distribution used by the implementation.

    Returns 0.0 for an empty region (NaN-safe: the fraction is formally
    undefined there, and 0.0 is the historical sentinel used by callers).
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
    """Apply the switch-OFF sub-region filter to each declared switch."""
    return {name: ablate_switch(accepted_rows, name) for name in switch_names}
