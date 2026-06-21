"""Neutral processes as first-class alternative generators in RACH.

A neutral process (genetic drift, mutation-selection balance, demographic
sampling noise) generates trait variation *independently of the environmental
gradient* x_obs.  It is a distinguished null — not a residual, not a catch-all
— and must compete on equal footing with directional mechanisms for inclusion
in the admissible region.

This module provides:

  NeutralProcess
      A dataclass describing a neutral alternative: its switch name, the
      biological source (drift / mutation / migration / sampling), and a
      description of what it generates (e.g. random between-population
      differentiation uncorrelated with x).

  NeutralCRCProfile
      CRC and CSM diagnostics specifically for neutral processes: a neutral
      switch with low CRC is easily ablated (directional mechanisms carry the
      pattern), while a neutral switch with high CRC would indicate that
      neutral variation is somehow required for acceptance (unusual and worth
      investigating).

  p_neutral_from_crc(profile)
      Convenience function: P(at least one neutral process active | A_ε),
      back-calculated from the CRC profile.  Complements the direct
      P(neutral | A_ε) from neutral_adaptive.py.

Design rationale (why CRC, not just CA)
----------------------------------------
CA_j = P(s_j = 1 | A_ε) for a neutral switch j near the prior (0.5) looks
uninformative: CA ≈ 0.5 just means neutral is "permitted" but not required.
CRC(neutral_j) tells a sharper story:

  CRC ≈ 0  neutral is redundant — ablating it leaves A_ε intact.
           Directional mechanisms alone explain the pattern; neutral adds
           nothing, and the study design should focus on distinguishing them.

  CRC ≫ 0  neutral is load-bearing — ablating it shrinks A_ε.
           The observed pattern cannot be reproduced by the directional
           mechanisms alone (perhaps the pattern is too noisy for selection
           to explain, or there is a specific signature that only drift
           generates).  Neutral becomes a serious rival explanation.

Relation to neutral_adaptive.py
---------------------------------
``neutral_adaptive.py`` is a full Tier-A worked example where P(neutral|A_ε)
is the headline result and the replicate-transect observation resolves it.
This module provides generic utilities so any RACH application can register
neutral processes and compute their CRC profile without depending on that
example.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from causal_model.causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
)
from causal_model.causal_substitution import causal_substitution_matrix, CSMEntry
from causal_model.counterfactual_ablation import ablate_switch
from causal_model.external_constraints import Constraint


# ---------------------------------------------------------------------------
# Neutral process descriptors
# ---------------------------------------------------------------------------

NEUTRAL_SOURCE_DRIFT = "drift"
NEUTRAL_SOURCE_MUTATION = "mutation"
NEUTRAL_SOURCE_MIGRATION = "migration"
NEUTRAL_SOURCE_SAMPLING = "sampling_noise"
NEUTRAL_SOURCE_STOCHASTIC = "stochastic_environment"

NEUTRAL_SOURCES = frozenset({
    NEUTRAL_SOURCE_DRIFT,
    NEUTRAL_SOURCE_MUTATION,
    NEUTRAL_SOURCE_MIGRATION,
    NEUTRAL_SOURCE_SAMPLING,
    NEUTRAL_SOURCE_STOCHASTIC,
})


@dataclass
class NeutralProcess:
    """A neutral alternative generator registered in a RACH analysis.

    Parameters
    ----------
    switch_name:
        The name of the corresponding BiologicalSwitch (must appear as a key
        in accepted-row dicts).
    source:
        The biological mechanism producing neutral variation (one of the
        NEUTRAL_SOURCE_* constants, or a custom string).
    description:
        Human-readable description of what the neutral process generates.
    prior_on_prob:
        Prior probability that the neutral process is active (default 0.5;
        matches the Tier-A convention).
    """
    switch_name: str
    source: str = NEUTRAL_SOURCE_DRIFT
    description: str = ""
    prior_on_prob: float = 0.5

    def is_recognized_source(self) -> bool:
        return self.source in NEUTRAL_SOURCES


# ---------------------------------------------------------------------------
# CRC profile for neutral processes
# ---------------------------------------------------------------------------

@dataclass
class NeutralCRCProfile:
    """CRC and substitution diagnostics for all registered neutral processes."""
    processes: list[NeutralProcess]
    crc_results: list[CRCResult]          # one per neutral process
    substitution_entries: list[CSMEntry]  # CSM rows where ablated ∈ neutral names
    p_any_neutral: float                  # P(≥1 neutral switch ON | A_ε)

    def describe(self) -> str:
        lines = [f"Neutral CRC profile  (P(any neutral | A_ε) = {self.p_any_neutral:.3f})"]
        for r in self.crc_results:
            lines.append("  " + r.describe())
        if self.substitution_entries:
            lines.append("  Top substitution entries (neutral ablated):")
            for e in self.substitution_entries[:6]:
                lines.append("    " + e.describe())
        return "\n".join(lines)


def neutral_crc_profile(
    neutral_processes: Iterable[NeutralProcess],
    accepted_rows: list[dict],
    switches,
    constraints: list[Constraint] | None = None,
) -> NeutralCRCProfile:
    """Compute CRC diagnostics for all registered neutral processes.

    Parameters
    ----------
    neutral_processes:
        The registered neutral alternatives.
    accepted_rows:
        Current admissible region A_ε.
    switches:
        All causal switches in the analysis.
    constraints:
        Optional external constraints for CRC penalty computation.

    Returns
    -------
    NeutralCRCProfile
    """
    procs = list(neutral_processes)
    neutral_names = {p.switch_name for p in procs}

    crc_results = [
        causal_replaceability_cost_full(p.switch_name, accepted_rows, constraints)
        for p in procs
    ]

    all_csm = causal_substitution_matrix(accepted_rows, switches)
    neutral_csm = [e for e in all_csm if e.ablated in neutral_names]

    # P(at least one neutral active | A_ε)
    n = len(accepted_rows)
    if n == 0:
        p_any = float("nan")
    else:
        n_any = sum(1 for r in accepted_rows
                    if any(r.get(name) for name in neutral_names))
        p_any = n_any / n

    return NeutralCRCProfile(
        processes=procs,
        crc_results=crc_results,
        substitution_entries=neutral_csm,
        p_any_neutral=round(p_any, 4),
    )


def p_neutral_from_crc(profile: NeutralCRCProfile) -> float:
    """P(at least one neutral process active | A_ε) from the profile."""
    return profile.p_any_neutral
