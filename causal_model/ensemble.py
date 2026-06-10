"""Ensemble inference over θ-prior presets and ABC acceptance rules.

Runs the RACH ABC sampler across a grid of (preset_name, acceptance_rule)
combinations to quantify sensitivity of CA_j, D_RACH, and R_RACH to the
choice of prior and ε threshold.

Usage
-----
    from causal_model.ensemble import run_ensemble, best_config, ensemble_ca_j

    results = run_ensemble(
        presets=["literature_grounded", "broad_prior"],
        acceptance_rules=["weighted_lax", "relaxed_0.83"],
        switches=CAMPANULA_SWITCHES,
        n_attempts=200,
        seed=42,
    )
    best = best_config(results, min_accepted=20)
    ca_avg = ensemble_ca_j(results, min_accepted=20)
    sens   = sensitivity_range(results)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnsembleResult:
    """One row in the ensemble comparison table."""
    preset_name: str
    acceptance_rule: str
    threshold: float
    n_accepted: int
    n_evaluated: int
    D_RACH: float
    R_RACH: float
    ca_j: dict[str, float]   # switch_name -> CA_j
    K: int                   # number of switches


# Default robustness thresholds (see docs/streamlit_ensemble_first_flow.md, Step 2).
SENSITIVITY_THRESHOLD = 0.20   # sensitivity_range >= this => prior/epsilon sensitive
CA_ON_THRESHOLD       = 2 / 3  # mean CA_j >= this => switch called ON
CA_OFF_THRESHOLD      = 1 / 3  # mean CA_j <= this => switch called OFF


@dataclass
class SwitchRobustness:
    """Robust/sensitive verdict for one switch across the ensemble.

    A switch is *robust* when its CA_j barely moves as the prior preset and ABC
    ε threshold are varied across the ensemble; it is *sensitive* (prior/epsilon
    dependent) when CA_j swings by at least ``SENSITIVITY_THRESHOLD``.  Only
    robust switches should be treated as reliable inference targets; sensitive
    switches are flagged as needing additional observations (and become the NOV
    targets — see ``next_observation_value(..., sensitive_switches=...)``).
    """
    switch: str
    mean_ca_j: float          # n_accepted-weighted mean CA_j across configs
    sensitivity_range: float  # max(CA_j) - min(CA_j) across configs
    is_robust: bool           # sensitivity_range < SENSITIVITY_THRESHOLD
    call: str                 # "ON" / "OFF" / "indeterminate"
    verdict: str              # human-readable label combining call + robustness


def run_ensemble(
    presets: list[str],
    acceptance_rules: list[str],
    switches,
    n_attempts: int = 200,
    seed: int = 42,
    backend: str = "abm",
    observed_rels=None,
    pattern_weights=None,
    progress_callback=None,   # callable(done, total, preset_name, rule)
) -> list[EnsembleResult]:
    """Run ABC inference over every (preset, acceptance_rule) combination.

    Parameters
    ----------
    presets:
        Names of θ-prior presets (keys of predefined_tradeoff_presets()).
    acceptance_rules:
        ABC acceptance rule names (keys of GRADIENT_THRESH_MAP).
    switches:
        Sequence of BiologicalSwitch definitions.
    n_attempts:
        ABC draws per configuration.
    seed:
        Base random seed; each config uses seed + config_index for reproducibility.
    backend:
        "abm" (default, high-fidelity) or "proxy" (fast).
    observed_rels:
        y_obs pattern rows.  If None, loaded from default Campanula data.
    pattern_weights:
        Pattern weight dict.  If None, loaded from default Campanula data.
    progress_callback:
        Optional callable(done: int, total: int, preset: str, rule: str).

    Returns
    -------
    list[EnsembleResult]
        One entry per (preset, rule) pair, sorted by R_RACH descending.
    """
    from causal_model.switch_inference import (
        run_switch_posterior_inference_abm as _run_abm,
        run_switch_posterior_inference as _run_proxy,
        GRADIENT_THRESH_MAP,
    )
    from causal_model.causal_admissibility import (
        causal_degeneracy,
        causal_resolvability,
    )

    if observed_rels is None or pattern_weights is None:
        from examples.campanula_izu.observed_data import (
            load_observed_patterns,
            load_pattern_weights,
        )
        observed_rels  = load_observed_patterns()
        pattern_weights = load_pattern_weights()

    _run = _run_abm if backend == "abm" else _run_proxy

    configs = [(p, r) for p in presets for r in acceptance_rules]
    total = len(configs)
    results: list[EnsembleResult] = []

    for i, (preset_name, acceptance_rule) in enumerate(configs):
        _seed = seed + i
        thresh = GRADIENT_THRESH_MAP.get(acceptance_rule, 1.0)

        sp = _run(
            preset_name=preset_name,
            n_attempts=n_attempts,
            acceptance_rule=acceptance_rule,
            seed=_seed,
            observed_rels=observed_rels,
            pattern_weights=pattern_weights,
            threshold=thresh,
        )

        accepted = sp.accepted_rows
        evaluated = getattr(sp, "evaluated_rows", None) or accepted

        D = causal_degeneracy(accepted, switches)
        R = causal_resolvability(accepted, switches)

        # CA_j per switch
        sw_names = [sw.name for sw in switches]
        if accepted:
            ca = {
                name: round(sum(1 for r in accepted if r.get(name)) / len(accepted), 4)
                for name in sw_names
            }
        else:
            ca = {name: float("nan") for name in sw_names}

        results.append(EnsembleResult(
            preset_name=preset_name,
            acceptance_rule=acceptance_rule,
            threshold=thresh,
            n_accepted=len(accepted),
            n_evaluated=len(evaluated),
            D_RACH=round(D, 4),
            R_RACH=round(R, 4),
            ca_j=ca,
            K=len(sw_names),
        ))

        if progress_callback is not None:
            progress_callback(i + 1, total, preset_name, acceptance_rule)

    results.sort(key=lambda x: x.R_RACH, reverse=True)
    return results


def best_config(
    results: list[EnsembleResult],
    min_accepted: int = 20,
) -> EnsembleResult | None:
    """Return the config with the highest R_RACH among those with n_accepted >= min_accepted."""
    eligible = [r for r in results if r.n_accepted >= min_accepted]
    if not eligible:
        eligible = results  # relax constraint if nothing qualifies
    return max(eligible, key=lambda x: x.R_RACH) if eligible else None


def ensemble_ca_j(
    results: list[EnsembleResult],
    min_accepted: int = 1,
) -> dict[str, float]:
    """Compute n_accepted-weighted average CA_j across configurations.

    Configs with n_accepted < min_accepted are excluded.
    Returns {switch_name: weighted_mean_CA_j}.
    """
    import math
    eligible = [r for r in results if r.n_accepted >= min_accepted]
    if not eligible:
        return {}

    sw_names = list(eligible[0].ca_j.keys())
    total_w = sum(r.n_accepted for r in eligible)

    return {
        name: round(
            sum(r.n_accepted * r.ca_j[name] for r in eligible
                if not math.isnan(r.ca_j.get(name, float("nan"))))
            / max(total_w, 1),
            4,
        )
        for name in sw_names
    }


def sensitivity_range(
    results: list[EnsembleResult],
) -> dict[str, float]:
    """Return max - min CA_j per switch across all configurations.

    Near-zero range → result is robust to prior/ε choice.
    Large range      → result is prior/ε sensitive; interpret with caution.
    """
    import math
    if not results:
        return {}
    sw_names = list(results[0].ca_j.keys())
    out = {}
    for name in sw_names:
        vals = [r.ca_j[name] for r in results if not math.isnan(r.ca_j.get(name, float("nan")))]
        out[name] = round(max(vals) - min(vals), 4) if len(vals) >= 2 else float("nan")
    return out


def classify_switch_robustness(
    results: list[EnsembleResult],
    sensitivity_threshold: float = SENSITIVITY_THRESHOLD,
    ca_on_threshold: float = CA_ON_THRESHOLD,
    ca_off_threshold: float = CA_OFF_THRESHOLD,
    min_accepted: int = 1,
) -> list[SwitchRobustness]:
    """Classify every switch as robust or sensitive across the ensemble.

    For each switch this combines two ensemble summaries:

    * ``mean_ca_j``         — n_accepted-weighted mean CA_j (``ensemble_ca_j``)
    * ``sensitivity_range`` — max(CA_j) − min(CA_j) (``sensitivity_range``)

    Robustness:
        robust    if sensitivity_range <  sensitivity_threshold
        sensitive if sensitivity_range >= sensitivity_threshold

    Directional call (only meaningful for robust switches):
        ON            if mean_ca_j >= ca_on_threshold
        OFF           if mean_ca_j <= ca_off_threshold
        indeterminate otherwise

    Parameters
    ----------
    results:
        Ensemble results from ``run_ensemble``.
    sensitivity_threshold:
        CA_j swing at/above which a switch is declared prior/ε sensitive.
    ca_on_threshold, ca_off_threshold:
        Mean-CA_j cutoffs for the ON / OFF directional call.
    min_accepted:
        Configs with fewer accepted draws are excluded from the weighted mean.

    Returns
    -------
    list[SwitchRobustness]
        One per switch, ordered most-sensitive first (so the highest-priority
        NOV targets sort to the top).
    """
    import math
    if not results:
        return []

    sw_names = list(results[0].ca_j.keys())
    mean_ca  = ensemble_ca_j(results, min_accepted=min_accepted)
    sens     = sensitivity_range(results)

    out: list[SwitchRobustness] = []
    for name in sw_names:
        ca_v = mean_ca.get(name, float("nan"))
        s_v  = sens.get(name, float("nan"))
        # Missing sensitivity (single config) is treated as not-robust: we cannot
        # demonstrate robustness from one configuration.
        is_robust = (not math.isnan(s_v)) and s_v < sensitivity_threshold

        if math.isnan(ca_v):
            call = "indeterminate"
        elif ca_v >= ca_on_threshold:
            call = "ON"
        elif ca_v <= ca_off_threshold:
            call = "OFF"
        else:
            call = "indeterminate"

        if is_robust:
            verdict = f"{call} (robust)" if call != "indeterminate" else "indeterminate (robust)"
        else:
            verdict = f"{call} (prior/ε sensitive)" if call != "indeterminate" \
                else "indeterminate (prior/ε sensitive)"

        out.append(SwitchRobustness(
            switch=name,
            mean_ca_j=round(ca_v, 4) if not math.isnan(ca_v) else float("nan"),
            sensitivity_range=round(s_v, 4) if not math.isnan(s_v) else float("nan"),
            is_robust=is_robust,
            call=call,
            verdict=verdict,
        ))

    # Most-sensitive first (NaN sensitivity sorts last).
    out.sort(key=lambda r: (-1.0 if math.isnan(r.sensitivity_range) else r.sensitivity_range),
             reverse=True)
    return out


def sensitive_switches(
    results: list[EnsembleResult],
    sensitivity_threshold: float = SENSITIVITY_THRESHOLD,
) -> list[str]:
    """Return the names of switches that are prior/ε sensitive (NOV targets)."""
    return [
        r.switch for r in classify_switch_robustness(
            results, sensitivity_threshold=sensitivity_threshold)
        if not r.is_robust
    ]


# Alias matching the name used in docs/streamlit_ensemble_first_flow.md.
select_best_ensemble_setting = best_config
