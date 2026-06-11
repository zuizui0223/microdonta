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

    @property
    def acceptance_rate(self) -> float:
        """ABC acceptance rate = n_accepted / n_evaluated (0.0 if nothing evaluated)."""
        return self.n_accepted / self.n_evaluated if self.n_evaluated > 0 else 0.0


# Default robustness thresholds (see docs/streamlit_ensemble_first_flow.md, Step 2).
SENSITIVITY_THRESHOLD = 0.20   # sensitivity_range >= this => prior/epsilon sensitive
CA_ON_THRESHOLD       = 2 / 3  # mean CA_j >= this => switch called ON
CA_OFF_THRESHOLD      = 1 / 3  # mean CA_j <= this => switch called OFF


@dataclass
class SwitchRobustness:
    """Robustness verdict for one switch across the ensemble.

    Two independent axes:

    * ``is_stable``   — CA_j barely moves as the prior preset and ABC ε threshold
      are varied (``sensitivity_range < SENSITIVITY_THRESHOLD``).
    * ``is_resolved`` — the switch has a definite ON/OFF call (CA_j away from 0.5).

    A **robust conclusion** (``is_robust``) requires BOTH: stable *and* resolved.
    A switch that is stable but sits at CA_j ≈ 0.5 is *stably uninformative*, NOT
    a robust conclusion — low sensitivity_range there reflects weak identification
    (the data barely constrain the switch), not a trustworthy answer. Only
    ``is_robust`` switches are reliable inference targets; every other switch
    (unresolved or prior/ε-sensitive) needs additional observations and becomes a
    NOV target — see ``next_observation_value(..., sensitive_switches=...)``.
    """
    switch: str
    mean_ca_j: float          # n_accepted-weighted mean CA_j across configs
    sensitivity_range: float  # max(CA_j) - min(CA_j) across configs
    is_robust: bool           # ROBUST CONCLUSION: stable AND resolved
    call: str                 # "ON" / "OFF" / "indeterminate"
    verdict: str              # human-readable label combining call + stability
    is_stable: bool = True     # sensitivity_range < SENSITIVITY_THRESHOLD
    is_resolved: bool = False  # call is ON or OFF (CA_j away from 0.5)

    @property
    def classification(self) -> str:
        """Issue #31 robustness label.

        Maps the two-axis verdict onto the canonical strings:
        - ``robust_supported``   — robust conclusion, switch ON
        - ``robust_opposed``     — robust conclusion, switch OFF
        - ``threshold_sensitive``— resolved direction but prior/ε-sensitive
        - ``unresolved``         — CA_j ≈ 0.5 (no definite direction)
        """
        if not self.is_resolved:
            return "unresolved"
        if not self.is_stable:
            return "threshold_sensitive"
        return "robust_supported" if self.call == "ON" else "robust_opposed"


def run_ensemble(
    presets: list[str],
    acceptance_rules: list[str],
    switches,
    n_attempts: int = 200,
    seed: int = 42,
    backend: str = "abm",
    distance_mode: str = "match_rate",
    epsilon_mode: str = "fixed",
    adaptive_percentile: float = 5.0,
    min_accept: int = 20,
    structure_prior_lambda: float = 0.0,
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
    progress_callback:
        Optional callable(done: int, total: int, preset: str, rule: str).

    y_obs is the role-filtered ``observed_target`` pattern set loaded internally
    by the inference functions; it is not a parameter here.

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
            threshold=thresh,
            distance_mode=distance_mode,
            epsilon_mode=epsilon_mode,
            adaptive_percentile=adaptive_percentile,
            min_accept=min_accept,
            structure_prior_lambda=structure_prior_lambda,
        )

        accepted = sp.accepted_rows
        evaluated = getattr(sp, "evaluated_rows", None) or accepted

        D = causal_degeneracy(accepted, switches)
        R = causal_resolvability(accepted, switches)

        # CA_j per switch
        sw_names = [sw.name for sw in switches]
        if accepted:
            weights = [max(0.0, float(r.get("structure_prior_weight", 1.0))) for r in accepted]
            denom = sum(weights) or float(len(accepted))
            ca = {
                name: round(
                    sum(w for r, w in zip(accepted, weights) if r.get(name)) / denom,
                    4,
                )
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


# Default stability filters for ensemble best-setting selection (issue #25).
DEFAULT_MIN_ACCEPTED       = 20
DEFAULT_MIN_ACCEPTANCE_RATE = 0.02   # reject configs so strict they may be artefacts


@dataclass
class BestSettingSelection:
    """Result of ensemble best-setting selection, with the selection rationale.

    ``passed_filters`` is True when ``best`` satisfied every stability filter.
    When no configuration passes, ``best`` falls back to the least-bad config by
    ``n_accepted`` and ``passed_filters`` is False — interpret with caution.
    """
    best: EnsembleResult | None
    passed_filters: bool
    rationale: str
    n_eligible: int
    n_total: int
    criteria: dict


def _selection_key(mode: str):
    """Return the sort key used to pick the best config for a given mode."""
    if mode == "max_accepted":
        return lambda r: (r.n_accepted, r.R_RACH)
    # default: maximise R_RACH, tie-break on n_accepted
    return lambda r: (r.R_RACH, r.n_accepted)


def select_best_ensemble_setting(
    results: list[EnsembleResult],
    min_accepted: int = DEFAULT_MIN_ACCEPTED,
    min_acceptance_rate: float = DEFAULT_MIN_ACCEPTANCE_RATE,
    max_acceptance_rate: float | None = None,
    mode: str = "max_R",
) -> BestSettingSelection:
    """Select the best ensemble configuration under explicit stability filters.

    The naive rule "max R_RACH among n_accepted >= 20" can over-favour very
    strict settings whose high resolvability is a small-sample artefact.  This
    adds acceptance-rate guards so a configuration must also accept a
    non-trivial fraction of evaluated draws (and optionally not too many).

    Stability filters
    -----------------
    * ``min_accepted``         — minimum accepted draws (avoid tiny samples).
    * ``min_acceptance_rate``  — minimum n_accepted / n_evaluated (avoid configs
      so strict their resolvability is a stochastic artefact).
    * ``max_acceptance_rate``  — optional upper bound (avoid configs so lax that
      A_ε is barely constrained); ``None`` disables it.

    Selection mode
    --------------
    * ``"max_R"``        — highest R_RACH among configs passing the filters
      (tie-break: larger n_accepted).  Default.
    * ``"max_accepted"`` — largest accepted sample (tie-break: higher R_RACH).

    Fallback
    --------
    If no configuration passes the filters, the least-bad config by n_accepted is
    returned with ``passed_filters=False`` and a cautionary rationale.

    Returns
    -------
    BestSettingSelection
    """
    criteria = {
        "min_accepted": min_accepted,
        "min_acceptance_rate": min_acceptance_rate,
        "max_acceptance_rate": max_acceptance_rate,
        "mode": mode,
    }
    if not results:
        return BestSettingSelection(
            best=None, passed_filters=False,
            rationale="No ensemble configurations were provided.",
            n_eligible=0, n_total=0, criteria=criteria,
        )

    key = _selection_key(mode)

    def _passes(r: EnsembleResult) -> bool:
        if r.n_accepted < min_accepted:
            return False
        if r.acceptance_rate < min_acceptance_rate:
            return False
        if max_acceptance_rate is not None and r.acceptance_rate > max_acceptance_rate:
            return False
        return True

    eligible = [r for r in results if _passes(r)]

    if eligible:
        best = max(eligible, key=key)
        crit_txt = (
            f"highest R_RACH" if mode == "max_R" else "largest accepted sample"
        )
        rationale = (
            f"Selected `{best.preset_name}` + `{best.acceptance_rule}` because it had "
            f"the {crit_txt} among {len(eligible)}/{len(results)} configurations passing "
            f"the stability filters (n_accepted >= {min_accepted}, "
            f"acceptance_rate >= {min_acceptance_rate:g}"
            + (f", <= {max_acceptance_rate:g}" if max_acceptance_rate is not None else "")
            + f"). R_RACH={best.R_RACH:.3f}, n_accepted={best.n_accepted}, "
            f"acceptance_rate={best.acceptance_rate:.3f}."
        )
        return BestSettingSelection(
            best=best, passed_filters=True, rationale=rationale,
            n_eligible=len(eligible), n_total=len(results), criteria=criteria,
        )

    # Fallback: nothing passed the filters.
    best = max(results, key=lambda r: (r.n_accepted, r.R_RACH))
    rationale = (
        f"No configuration passed the stability filters "
        f"(n_accepted >= {min_accepted}, acceptance_rate >= {min_acceptance_rate:g}"
        + (f", <= {max_acceptance_rate:g}" if max_acceptance_rate is not None else "")
        + f"). Showing least-bad fallback `{best.preset_name}` + `{best.acceptance_rule}` "
        f"by n_accepted ({best.n_accepted}); interpret with caution."
    )
    return BestSettingSelection(
        best=best, passed_filters=False, rationale=rationale,
        n_eligible=0, n_total=len(results), criteria=criteria,
    )


def best_config(
    results: list[EnsembleResult],
    min_accepted: int = DEFAULT_MIN_ACCEPTED,
    min_acceptance_rate: float = 0.0,
    max_acceptance_rate: float | None = None,
    mode: str = "max_R",
) -> EnsembleResult | None:
    """Return the best ensemble configuration (the ``EnsembleResult`` only).

    Thin wrapper over :func:`select_best_ensemble_setting`.  The default
    ``min_acceptance_rate=0.0`` preserves the original behaviour (max R_RACH
    among ``n_accepted >= min_accepted``, relaxing to all configs if none
    qualify).  Pass ``min_acceptance_rate``/``max_acceptance_rate`` to enable the
    stability guards described in :func:`select_best_ensemble_setting`.
    """
    return select_best_ensemble_setting(
        results,
        min_accepted=min_accepted,
        min_acceptance_rate=min_acceptance_rate,
        max_acceptance_rate=max_acceptance_rate,
        mode=mode,
    ).best


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
        # Stability: CA_j barely moves across prior/ε configs. Missing sensitivity
        # (single config) cannot demonstrate stability.
        is_stable = (not math.isnan(s_v)) and s_v < sensitivity_threshold

        if math.isnan(ca_v):
            call = "indeterminate"
        elif ca_v >= ca_on_threshold:
            call = "ON"
        elif ca_v <= ca_off_threshold:
            call = "OFF"
        else:
            call = "indeterminate"

        # Resolution: the switch has a definite direction (CA_j away from 0.5).
        is_resolved = call in ("ON", "OFF")

        # A ROBUST CONCLUSION requires BOTH stability and resolution. A switch
        # sitting at CA_j ≈ 0.5 with a small sensitivity_range is *stably
        # uninformative*, NOT a robust conclusion — it must still be flagged for
        # additional observations (it becomes a NOV target).
        is_robust = is_stable and is_resolved

        if is_resolved:
            verdict = f"{call} ({'robust' if is_stable else 'prior/ε sensitive'})"
        else:
            verdict = (
                "unresolved (stable across configs — needs more data)"
                if is_stable else
                "unresolved (prior/ε sensitive — needs more data)"
            )

        out.append(SwitchRobustness(
            switch=name,
            mean_ca_j=round(ca_v, 4) if not math.isnan(ca_v) else float("nan"),
            sensitivity_range=round(s_v, 4) if not math.isnan(s_v) else float("nan"),
            is_robust=is_robust,
            call=call,
            verdict=verdict,
            is_stable=is_stable,
            is_resolved=is_resolved,
        ))

    # Most-sensitive first (NaN sensitivity sorts last).
    out.sort(key=lambda r: (-1.0 if math.isnan(r.sensitivity_range) else r.sensitivity_range),
             reverse=True)
    return out


def sensitive_switches(
    results: list[EnsembleResult],
    sensitivity_threshold: float = SENSITIVITY_THRESHOLD,
) -> list[str]:
    """Return switches that are NOT a robust conclusion — the NOV targets.

    This is every switch that is either prior/ε-sensitive (high
    ``sensitivity_range``) OR unresolved (CA_j ≈ 0.5). Both require additional
    observations, so both are valid next-observation-value targets. Ordered
    most-sensitive first.
    """
    return [
        r.switch for r in classify_switch_robustness(
            results, sensitivity_threshold=sensitivity_threshold)
        if not r.is_robust
    ]
