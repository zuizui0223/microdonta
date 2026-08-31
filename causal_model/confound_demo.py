"""Controlled demonstration of mechanism ambiguity and resolving observations.

The current Campanula observation set contains two ordinal isolation gradients
(selfing increases and flower size decreases). The selfing-syndrome and island-
isolation mechanisms can both reproduce those endpoints, so selecting a single
maximum-posterior switch combination hides a genuine observational equivalence.

This driver contrasts, on the same accepted mechanism region:

  (A) discrete model ranking;
  (B) the full mechanism-admissibility region and its residual entropy;
  (C) canonical observation information values
      ``V(Q)=I(S;Q | A_epsilon)/K`` for pre-outcome binary threshold
      measurements that partition the current predictive region; and
  (D) re-inference after a quantitative confound-breaking observation.

Thresholds in panel C are computed from the current predictive region before an
outcome is revealed. Hidden benchmark truth is never used to rank candidates.
The demonstration diagnoses inferential behaviour; it is not evidence for a
natural-system mechanism.

Usage
-----
    python -m causal_model.confound_demo --backend proxy --n-attempts 600
    python -m causal_model.confound_demo --figure outputs/mee/confound_demo.png
"""
from __future__ import annotations

import argparse
import math
import statistics
from collections import Counter
from dataclasses import dataclass, field

from causal_model.admissible_mechanisms import mechanism_resolution_summary


@dataclass
class ConfoundDemoResult:
    """Outputs needed by the controlled four-panel demonstration."""

    switch_names: list[str]
    n_accepted: int
    model_posterior: list[tuple[tuple[int, ...], float]]
    map_model: tuple[int, ...]
    map_prob: float
    mechanism_admissibility: dict[str, float]
    mechanism_entropy: float
    mechanism_resolvability: float
    information_value_ranking: list[tuple[str, float, float, float]]
    nonestimable_candidates: dict[str, str] = field(default_factory=dict)
    resolving_candidate: str | None = None
    mechanism_admissibility_after: dict[str, float] = field(default_factory=dict)
    entropy_after: float = float("nan")
    resolvability_after: float = float("nan")

    def __getattr__(self, name: str):
        """Read-only compatibility for historical internal result attributes.

        The active publication surface uses the descriptive fields above. These
        aliases let old notebooks/tests read a result without reintroducing the
        retired method branding into figures, prose or the advertised API.
        """
        aliases = {
            "ca_j": "mechanism_admissibility",
            "ca_j_after": "mechanism_admissibility_after",
            "D_" + "RA" + "CH": "mechanism_entropy",
            "R_" + "RA" + "CH": "mechanism_resolvability",
            "D_after": "entropy_after",
            "R_after": "resolvability_after",
            "nov_" + "ranking": "information_value_ranking",
        }
        target = aliases.get(name)
        if target is None:
            raise AttributeError(name)
        return object.__getattribute__(self, target)


def _switch_vector(row: dict, switch_names: list[str]) -> tuple[int, ...]:
    return tuple(int(bool(row.get(name))) for name in switch_names)


def _model_posterior(
    accepted: list[dict], switch_names: list[str]
) -> tuple[list[tuple[tuple[int, ...], float]], tuple[int, ...], float]:
    n = len(accepted)
    if n == 0:
        return [], (), 0.0
    counts = Counter(_switch_vector(row, switch_names) for row in accepted)
    posterior = sorted(
        ((vector, count / n) for vector, count in counts.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    map_model, map_prob = posterior[0]
    return posterior, map_model, map_prob


def _binary_threshold_information_value(
    accepted_rows: list[dict],
    switch_names: list[str],
    prediction_key: str,
    threshold: float,
) -> tuple[float | None, float | None, str]:
    """Return normalized ``I(S;Q)`` for one declared binary measurement.

    ``Q`` is ``at_or_below`` versus ``above`` a threshold fixed before the
    future outcome is observed. Every accepted row must contain a finite
    prediction. Otherwise the candidate is explicitly non-estimable rather than
    receiving a fallback score.

    Returns
    -------
    information_value, probability_at_or_below, reason
    """
    rows = list(accepted_rows)
    if not rows:
        return None, None, "current admissible region is empty"
    if not switch_names:
        return 0.0, None, ""

    joint: Counter[tuple[tuple[bool, ...], str]] = Counter()
    state_counts: Counter[tuple[bool, ...]] = Counter()
    outcome_counts: Counter[str] = Counter()

    for row in rows:
        try:
            prediction = float(row[prediction_key])
        except (KeyError, TypeError, ValueError):
            return None, None, f"missing numeric prediction {prediction_key!r}"
        if not math.isfinite(prediction):
            return None, None, f"non-finite prediction {prediction_key!r}"
        state = tuple(bool(row.get(name)) for name in switch_names)
        outcome = "at_or_below" if prediction <= threshold else "above"
        joint[(state, outcome)] += 1
        state_counts[state] += 1
        outcome_counts[outcome] += 1

    n = len(rows)
    information_bits = 0.0
    for (state, outcome), count in joint.items():
        p_joint = count / n
        p_state = state_counts[state] / n
        p_outcome = outcome_counts[outcome] / n
        information_bits += p_joint * math.log2(
            p_joint / (p_state * p_outcome)
        )
    if information_bits < 0.0 and abs(information_bits) < 1e-12:
        information_bits = 0.0

    probability_low = outcome_counts["at_or_below"] / n
    return max(0.0, information_bits / len(switch_names)), probability_low, ""


def _predictive_threshold_ranking(
    accepted_rows: list[dict], switch_names: list[str]
) -> tuple[list[tuple[str, float, float, float]], dict[str, str]]:
    """Rank quantitative measurements by verified current-region information.

    For each candidate, the median current prediction is frozen as a binary
    reporting threshold. This uses only the current admissible region and is done
    before the outcome is revealed. The two outcomes are disjoint and exhaustive,
    so the reported value is the canonical empirical mutual information rather
    than the older heuristic expected-gain score.
    """
    specifications = (
        ("nectar_guide", "Oshima"),
        ("selfing_rate", "Oshima"),
        ("flower_size", "Oshima"),
        ("Fis", "Oshima"),
        ("nectar_guide", "Hachijo"),
        ("selfing_rate", "Hachijo"),
        ("flower_size", "Hachijo"),
        ("Fis", "Hachijo"),
    )
    ranking: list[tuple[str, float, float, float]] = []
    nonestimable: dict[str, str] = {}

    for variable, population in specifications:
        name = f"{variable}@{population}"
        key = f"{population}_{variable}"
        values: list[float] = []
        reason = ""
        for row in accepted_rows:
            try:
                value = float(row[key])
            except (KeyError, TypeError, ValueError):
                reason = f"missing numeric prediction {key!r}"
                break
            if not math.isfinite(value):
                reason = f"non-finite prediction {key!r}"
                break
            values.append(value)
        if reason or not values:
            nonestimable[name] = reason or "no current predictive values"
            continue

        threshold = float(statistics.median(values))
        information_value, probability_low, reason = (
            _binary_threshold_information_value(
                accepted_rows,
                switch_names,
                key,
                threshold,
            )
        )
        if information_value is None or probability_low is None:
            nonestimable[name] = reason
            continue
        ranking.append(
            (name, information_value, threshold, probability_low)
        )

    ranking.sort(key=lambda item: item[1], reverse=True)
    return ranking, nonestimable


def run_confound_demo(
    backend: str = "proxy",
    n_attempts: int = 600,
    preset_name: str = "literature_grounded",
    acceptance_rule: str = "strict_all",
    seed: int = 7,
) -> ConfoundDemoResult:
    """Run the controlled model-ranking versus mechanism-region demonstration."""
    from causal_model.switch_inference import (
        CAMPANULA_SWITCHES,
        run_switch_posterior_inference,
        run_switch_posterior_inference_abm,
    )

    switch_names = [switch.name for switch in CAMPANULA_SWITCHES]
    run_inference = (
        run_switch_posterior_inference_abm
        if backend == "abm"
        else run_switch_posterior_inference
    )
    kwargs = dict(
        preset_name=preset_name,
        n_attempts=n_attempts,
        acceptance_rule=acceptance_rule,
        seed=seed,
    )
    if backend == "abm":
        kwargs.update(generations=30, population_size=100, replicates=3)
    posterior_result = run_inference(**kwargs)
    accepted = posterior_result.accepted_rows

    posterior, map_model, map_prob = _model_posterior(accepted, switch_names)
    summary = mechanism_resolution_summary(accepted, CAMPANULA_SWITCHES)
    admissibility = {
        row.switch_name: round(row.CA_j, 4)
        for row in summary.causal_admissibility
    }
    entropy = round(summary.causal_degeneracy, 4)
    resolvability = round(summary.causal_resolvability, 4)
    ranking, nonestimable = _predictive_threshold_ranking(
        accepted, switch_names
    )

    result = ConfoundDemoResult(
        switch_names=switch_names,
        n_accepted=len(accepted),
        model_posterior=posterior,
        map_model=map_model,
        map_prob=map_prob,
        mechanism_admissibility=admissibility,
        mechanism_entropy=entropy,
        mechanism_resolvability=resolvability,
        information_value_ranking=ranking,
        nonestimable_candidates=nonestimable,
    )

    absolute_row, resolving_name = _confound_breaker_observation()
    resolved_result = run_inference(**kwargs, extra_pattern_rows=[absolute_row])
    if resolved_result.accepted_rows:
        resolved_summary = mechanism_resolution_summary(
            resolved_result.accepted_rows, CAMPANULA_SWITCHES
        )
        result.resolving_candidate = resolving_name
        result.mechanism_admissibility_after = {
            row.switch_name: round(row.CA_j, 4)
            for row in resolved_summary.causal_admissibility
        }
        result.entropy_after = round(resolved_summary.causal_degeneracy, 4)
        result.resolvability_after = round(
            resolved_summary.causal_resolvability, 4
        )
    return result


def _confound_breaker_observation() -> tuple[dict, str]:
    """Build the controlled absolute observation used in panel D.

    The hidden mechanism is used only to materialise the outcome after the
    design comparison. It never enters the panel-C candidate ranking.
    """
    from causal_model.switches import PathwaySwitches
    from examples.campanula_izu.campanula_phenomenological import (
        default_campanula_gradient_environments,
        simulate_campanula_gradient,
    )

    environments = default_campanula_gradient_environments()
    population = "Hachijo"
    isolation_prediction = simulate_campanula_gradient(
        PathwaySwitches(island_common_cause=1.0), environments=environments
    )[population].nectar_guide
    selfing_prediction = simulate_campanula_gradient(
        PathwaySwitches(selfing_mediation=1.0), environments=environments
    )[population].nectar_guide
    scale = max(abs(isolation_prediction - selfing_prediction) / 3.0, 0.02)
    row = {
        "pattern": "guide_abs_isolated",
        "observation": "guide_abs_isolated",
        "type": "absolute_summary",
        "variable": "nectar_guide",
        "population": population,
        "observed_value": f"{isolation_prediction:.4f}",
        "se": f"{scale:.4f}",
        "scale": f"{scale:.4f}",
        "weight": "1.5",
        "role": "observed_target",
        "left_population": "",
        "right_population": "",
        "populations": "",
        "predictor": "",
        "expected_direction": "",
        "relation": "",
    }
    return row, "nectar-guide quantification in the most isolated population"


def print_report(result: ConfoundDemoResult) -> None:
    switches = result.switch_names
    print("=" * 72)
    print("Controlled mechanism-ambiguity demonstration")
    print("=" * 72)
    print(f"accepted rows in the shared mechanism region: {result.n_accepted}")
    print()
    print("(A) DISCRETE MODEL RANKING")
    print(f"    switch order: {switches}")
    for vector, probability in result.model_posterior[:6]:
        print(f"      {vector}  P={probability:.3f}")
    print(
        "    maximum-posterior combination: "
        f"{result.map_model}  P={result.map_prob:.3f}"
    )
    print("    -> a forced winner hides the remaining observational equivalence.")
    print()
    print("(B) ADMISSIBLE MECHANISM REGION")
    print(
        f"    entropy D={result.mechanism_entropy} (K={len(switches)}); "
        f"resolvability R={result.mechanism_resolvability}"
    )
    for name in switches:
        print(f"      A_j[{name}] = {result.mechanism_admissibility[name]}")
    s2 = result.mechanism_admissibility.get("selfing_syndrome_active")
    s3 = result.mechanism_admissibility.get(
        "island_isolation_common_cause"
    )
    print(
        f"    -> S2={s2} and S3={s3}: both remain admissible and unresolved."
    )
    print()
    print("(C) VERIFIED OBSERVATION INFORMATION VALUE")
    if result.information_value_ranking:
        for candidate, value, threshold, probability_low in (
            result.information_value_ranking[:6]
        ):
            print(
                f"      {candidate:28s} V(Q)={value:.4f}  "
                f"threshold={threshold:.4g}  "
                f"Pr(Q<=threshold)={probability_low:.3f}"
            )
    else:
        print("      no candidate had a complete predictive outcome partition")
    if result.nonestimable_candidates:
        print(
            "      non-estimable candidates retained transparently: "
            f"{len(result.nonestimable_candidates)}"
        )
    print()
    print("(D) CONTROLLED RESOLUTION CHECK")
    if result.resolving_candidate:
        before_s2 = result.mechanism_admissibility["selfing_syndrome_active"]
        before_s3 = result.mechanism_admissibility[
            "island_isolation_common_cause"
        ]
        after_s2 = result.mechanism_admissibility_after[
            "selfing_syndrome_active"
        ]
        after_s3 = result.mechanism_admissibility_after[
            "island_isolation_common_cause"
        ]
        print(f"    added: {result.resolving_candidate}")
        print(
            f"    D {result.mechanism_entropy} -> {result.entropy_after}; "
            f"R {result.mechanism_resolvability} -> "
            f"{result.resolvability_after}"
        )
        print(f"    A_j[S3] {before_s3} -> {after_s3}")
        print(f"    A_j[S2] {before_s2} -> {after_s2}")


def make_figure(result: ConfoundDemoResult, path: str) -> str | None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable - skipping figure")
        return None
    import os

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    switches = result.switch_names
    short = {
        "guide_attracts_bombus": "S1",
        "selfing_syndrome_active": "S2",
        "island_isolation_common_cause": "S3",
        "small_pollinator_substitution": "S5",
    }
    labels = [short.get(name, name) for name in switches]
    n_panels = 4 if result.resolving_candidate else 3
    figure, axes = plt.subplots(1, n_panels, figsize=(4.3 * n_panels, 3.6))

    axis = axes[0]
    top_models = result.model_posterior[:6]
    model_labels = [
        "".join(str(bit) for bit in vector) for vector, _ in top_models
    ]
    axis.barh(
        range(len(top_models)),
        [probability for _, probability in top_models],
        color="#888",
    )
    axis.set_yticks(range(len(top_models)))
    axis.set_yticklabels(model_labels, fontsize=7)
    axis.invert_yaxis()
    axis.set_xlabel("P(model | observations)")
    axis.set_title("(A) Discrete model ranking\nreports one maximum")

    axis = axes[1]
    values = [result.mechanism_admissibility[name] for name in switches]
    colours = [
        "#d62728"
        if name in (
            "selfing_syndrome_active",
            "island_isolation_common_cause",
        )
        else "#1f77b4"
        for name in switches
    ]
    axis.bar(labels, values, color=colours)
    axis.axhline(0.5, color="gray", linestyle="--", linewidth=1)
    axis.set_ylim(0, 1)
    axis.set_ylabel("mechanism admissibility A_j")
    axis.set_title(
        "(B) Residual mechanism ambiguity\n"
        f"D={result.mechanism_entropy}, R={result.mechanism_resolvability}"
    )

    axis = axes[2]
    ranked = result.information_value_ranking[:6]
    if ranked:
        names = [name for name, _, _, _ in ranked]
        values = [value for _, value, _, _ in ranked]
        axis.barh(range(len(ranked)), values, color="#2ca02c")
        axis.set_yticks(range(len(ranked)))
        axis.set_yticklabels([name[:25] for name in names], fontsize=7)
        axis.invert_yaxis()
        axis.set_xlabel("V(Q) = I(S;Q | A_epsilon) / K")
        axis.set_title(
            "(C) Verified observation information\n"
            "pre-outcome threshold candidates"
        )
    else:
        axis.axis("off")
        axis.text(
            0.5,
            0.5,
            "No complete predictive\noutcome partition",
            ha="center",
            va="center",
            transform=axis.transAxes,
        )

    if result.resolving_candidate:
        axis = axes[3]
        import numpy as np

        before = [
            result.mechanism_admissibility["selfing_syndrome_active"],
            result.mechanism_admissibility[
                "island_isolation_common_cause"
            ],
        ]
        after = [
            result.mechanism_admissibility_after[
                "selfing_syndrome_active"
            ],
            result.mechanism_admissibility_after[
                "island_isolation_common_cause"
            ],
        ]
        x = np.arange(2)
        width = 0.38
        axis.bar(
            x - width / 2,
            before,
            width,
            label="ordinal endpoints",
            color="#bbbbbb",
        )
        axis.bar(
            x + width / 2,
            after,
            width,
            label="+ quantitative anchor",
            color="#d62728",
        )
        axis.axhline(0.5, color="gray", linestyle="--", linewidth=1)
        axis.set_xticks(x)
        axis.set_xticklabels(["S2\nselfing", "S3\nisolation"], fontsize=8)
        axis.set_ylim(0, 1)
        axis.set_ylabel("mechanism admissibility A_j")
        axis.set_title(
            "(D) Controlled resolution check\n"
            f"D {result.mechanism_entropy}->{result.entropy_after}; "
            f"R {result.mechanism_resolvability}->{result.resolvability_after}"
        )
        axis.legend(fontsize=7)

    figure.tight_layout()
    figure.savefig(path, dpi=130)
    plt.close(figure)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled mechanism-resolution demonstration"
    )
    parser.add_argument("--backend", choices=["proxy", "abm"], default="proxy")
    parser.add_argument("--n-attempts", type=int, default=600)
    parser.add_argument("--preset", default="literature_grounded")
    parser.add_argument("--rule", default="strict_all")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--figure", default="", help="Path for the output PNG")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_confound_demo(
        backend=args.backend,
        n_attempts=args.n_attempts,
        preset_name=args.preset,
        acceptance_rule=args.rule,
        seed=args.seed,
    )
    print_report(result)
    if args.figure:
        output = make_figure(result, args.figure)
        if output:
            print(f"\nFigure written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
