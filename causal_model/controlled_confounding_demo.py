"""Controlled confounding demonstration for Mechanism-Resolving Observation Design.

The demonstration uses one accepted parameter-mechanism region for four linked
steps:

1. a conventional ranking reports a single low-mass modal switch combination;
2. the retained admissible region exposes residual mechanism ambiguity;
3. quantitative candidate measurements are scored by the canonical observation
   information value ``V(Q)=I(S;Q|A_epsilon)/K`` using a verified six-bin
   partition of the current region;
4. a predeclared quantitative nectar-guide measurement is added and the coupled
   mechanisms are re-evaluated.

The example diagnoses inferential behaviour in a controlled model. It is not a
claim about the true mechanism in a natural population.
"""
from __future__ import annotations

import argparse
import math
import random
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ControlledConfoundingResult:
    """Results used by manuscript Figure 1 and its behavioural regression test."""

    switch_names: list[str]
    n_accepted: int
    model_posterior: list[tuple[tuple[int, ...], float]]
    modal_model: tuple[int, ...]
    modal_probability: float
    mechanism_admissibility: dict[str, float]
    mechanism_entropy: float
    mechanism_resolvability: float
    information_value_ranking: list[tuple[str, float, str]]
    resolving_measurement: str | None = None
    mechanism_admissibility_after: dict[str, float] = field(default_factory=dict)
    entropy_after: float = float("nan")
    resolvability_after: float = float("nan")


def _switch_vector(row: dict, switch_names: list[str]) -> tuple[int, ...]:
    return tuple(int(bool(row.get(name))) for name in switch_names)


def _model_posterior(
    accepted_rows: list[dict],
    switch_names: list[str],
) -> tuple[list[tuple[tuple[int, ...], float]], tuple[int, ...], float]:
    n = len(accepted_rows)
    if n == 0:
        return [], (), 0.0
    counts = Counter(_switch_vector(row, switch_names) for row in accepted_rows)
    posterior = sorted(
        ((vector, count / n) for vector, count in counts.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    modal_model, modal_probability = posterior[0]
    return posterior, modal_model, modal_probability


def _candidate_information_values(
    accepted_rows: list[dict],
    switches,
    *,
    seed: int,
) -> list[tuple[str, float, str]]:
    """Score quantitative measurements with a verified current-region partition.

    Each continuous candidate is divided into six equal-width predictive bins.
    Those bins are mutually exclusive and exhaustive over the stored admissible
    region, so expected resolvability gain is exactly
    ``I(S;Q|A_epsilon)/K``. A fixed-seed synthetic nuisance measurement is added
    independently of mechanism state to show that variation alone need not carry
    resolving information.
    """
    from causal_model.admissible_mechanisms import mechanism_resolvability
    from causal_model.information_value_calibration_core import evsi_resolvability

    current_resolvability = mechanism_resolvability(accepted_rows, switches)
    specifications = [
        (
            "nectar guide at Hachijo",
            "Hachijo",
            "nectar_guide",
            "direct quantitative confound-breaker",
        ),
        (
            "flower size at Hachijo",
            "Hachijo",
            "flower_size",
            "quantitative endpoint measurement",
        ),
        (
            "selfing rate at Hachijo",
            "Hachijo",
            "selfing_rate",
            "quantitative mating-system measurement",
        ),
        (
            "Fis at Hachijo",
            "Hachijo",
            "Fis",
            "quantitative population-genetic measurement",
        ),
    ]

    ranking: list[tuple[str, float, str]] = []
    for label, population, variable, role in specifications:
        value = evsi_resolvability(
            accepted_rows,
            switches,
            population,
            variable,
            current_resolvability,
            n_bins=6,
        )
        if value is not None:
            ranking.append((label, float(value), role))

    nuisance_rows = [dict(row) for row in accepted_rows]
    rng = random.Random(seed + 918_273)
    for row in nuisance_rows:
        row["synthetic_nuisance_measurement"] = rng.random()
    nuisance_value = evsi_resolvability(
        nuisance_rows,
        switches,
        "synthetic",
        "nuisance_measurement",
        current_resolvability,
        n_bins=6,
    )
    if nuisance_value is not None:
        ranking.append(
            (
                "mechanism-independent nuisance",
                float(nuisance_value),
                "synthetic negative-control measurement",
            )
        )

    ranking.sort(key=lambda item: item[1], reverse=True)
    return ranking


def run_controlled_confounding_demo(
    backend: str = "proxy",
    n_attempts: int = 600,
    preset_name: str = "literature_grounded",
    acceptance_rule: str = "strict_all",
    seed: int = 7,
) -> ControlledConfoundingResult:
    """Run the controlled model-ranking, ambiguity and measurement-design example."""
    from causal_model.switch_inference import (
        CAMPANULA_SWITCHES,
        run_switch_posterior_inference,
        run_switch_posterior_inference_abm,
    )
    from causal_model.admissible_mechanisms import mechanism_resolution_summary

    switch_names = [switch.name for switch in CAMPANULA_SWITCHES]
    inference = (
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

    first = inference(**kwargs)
    accepted_rows = first.accepted_rows
    posterior, modal_model, modal_probability = _model_posterior(
        accepted_rows, switch_names
    )

    summary = mechanism_resolution_summary(accepted_rows, CAMPANULA_SWITCHES)
    admissibility = {
        item.switch_name: round(item.CA_j, 4)
        for item in summary.causal_admissibility
    }
    entropy = round(summary.causal_degeneracy, 4)
    resolvability = round(summary.causal_resolvability, 4)
    information_ranking = _candidate_information_values(
        accepted_rows, CAMPANULA_SWITCHES, seed=seed
    )

    result = ControlledConfoundingResult(
        switch_names=switch_names,
        n_accepted=len(accepted_rows),
        model_posterior=posterior,
        modal_model=modal_model,
        modal_probability=modal_probability,
        mechanism_admissibility=admissibility,
        mechanism_entropy=entropy,
        mechanism_resolvability=resolvability,
        information_value_ranking=information_ranking,
    )

    measurement_row, measurement_name = _confound_breaker_observation()
    second = inference(**kwargs, extra_pattern_rows=[measurement_row])
    if second.accepted_rows:
        after = mechanism_resolution_summary(
            second.accepted_rows, CAMPANULA_SWITCHES
        )
        result.resolving_measurement = measurement_name
        result.mechanism_admissibility_after = {
            item.switch_name: round(item.CA_j, 4)
            for item in after.causal_admissibility
        }
        result.entropy_after = round(after.causal_degeneracy, 4)
        result.resolvability_after = round(after.causal_resolvability, 4)

    return result


def _confound_breaker_observation() -> tuple[dict, str]:
    """Predeclare a quantitative nectar-guide measurement at Hachijo.

    The controlled hidden state used only for materialising the demonstration's
    realised outcome has the island common-cause mechanism active. Candidate
    ranking is completed before this value is used.
    """
    from causal_model.switches import PathwaySwitches
    from examples.campanula_izu.campanula_phenomenological import (
        default_campanula_gradient_environments,
        simulate_campanula_gradient,
    )

    environments = default_campanula_gradient_environments()
    population = "Hachijo"
    common_cause_value = simulate_campanula_gradient(
        PathwaySwitches(island_common_cause=1.0),
        environments=environments,
    )[population].nectar_guide
    selfing_pathway_value = simulate_campanula_gradient(
        PathwaySwitches(selfing_mediation=1.0),
        environments=environments,
    )[population].nectar_guide
    scale = max(abs(common_cause_value - selfing_pathway_value) / 3.0, 0.02)
    row = {
        "pattern": "guide_abs_isolated",
        "observation": "guide_abs_isolated",
        "type": "absolute_summary",
        "variable": "nectar_guide",
        "population": population,
        "observed_value": f"{common_cause_value:.4f}",
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
    return row, "quantitative nectar-guide measurement at Hachijo"


def print_report(result: ControlledConfoundingResult) -> None:
    """Print the four-panel story without retired project terminology."""
    print("=" * 76)
    print("Controlled confounding demonstration")
    print("=" * 76)
    print(f"accepted parameter-mechanism draws: {result.n_accepted}")
    print()
    print("(A) MODEL RANKING")
    print(f"    switch order: {result.switch_names}")
    for vector, probability in result.model_posterior[:6]:
        print(f"      {vector}  P={probability:.3f}")
    print(
        "    modal combination: "
        f"{result.modal_model}  P={result.modal_probability:.3f}"
    )
    print("    -> ranking reports one label although substantial ambiguity remains.")
    print()
    print("(B) ADMISSIBLE MECHANISM REGION")
    print(
        f"    entropy D={result.mechanism_entropy} bits; "
        f"resolvability R={result.mechanism_resolvability}"
    )
    for name in result.switch_names:
        print(
            f"      P({name}=on | A_epsilon) = "
            f"{result.mechanism_admissibility[name]}"
        )
    s2 = result.mechanism_admissibility.get("selfing_syndrome_active")
    s3 = result.mechanism_admissibility.get("island_isolation_common_cause")
    print(f"    -> S2={s2} and S3={s3}: observationally coupled.")
    print()
    print("(C) OBSERVATION INFORMATION VALUE")
    for label, value, role in result.information_value_ranking:
        print(f"      {label:34s} V(Q)={value:.4f}  [{role}]")
    print()
    print("(D) CONDITION ON THE REALISED QUANTITATIVE MEASUREMENT")
    if result.resolving_measurement:
        s2_after = result.mechanism_admissibility_after[
            "selfing_syndrome_active"
        ]
        s3_after = result.mechanism_admissibility_after[
            "island_isolation_common_cause"
        ]
        print(f"    added: {result.resolving_measurement}")
        print(
            f"    D {result.mechanism_entropy} -> {result.entropy_after}; "
            f"R {result.mechanism_resolvability} -> "
            f"{result.resolvability_after}"
        )
        print(f"    S3 {s3} -> {s3_after}; S2 {s2} -> {s2_after}")
        print("    -> the coupled mechanisms separate after the measurement.")


def make_figure(result: ControlledConfoundingResult, path: str) -> str | None:
    """Write manuscript Figure 1 with the canonical information-value axis."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib unavailable - skipping figure")
        return None

    import os
    import numpy as np

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    labels = {
        "guide_attracts_bombus": "S1",
        "selfing_syndrome_active": "S2",
        "island_isolation_common_cause": "S3",
        "small_pollinator_substitution": "S5",
    }
    short_labels = [labels.get(name, name) for name in result.switch_names]
    figure, axes = plt.subplots(1, 4, figsize=(17.2, 3.8))

    ax = axes[0]
    top_models = result.model_posterior[:6]
    model_labels = ["".join(str(bit) for bit in vector) for vector, _ in top_models]
    ax.barh(range(len(top_models)), [p for _, p in top_models], color="#888888")
    ax.set_yticks(range(len(top_models)))
    ax.set_yticklabels(model_labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("P(model | data)")
    ax.set_title("(A) Model ranking\nreports one modal combination")

    ax = axes[1]
    values = [result.mechanism_admissibility[name] for name in result.switch_names]
    colours = [
        "#d62728"
        if name in {"selfing_syndrome_active", "island_isolation_common_cause"}
        else "#1f77b4"
        for name in result.switch_names
    ]
    ax.bar(short_labels, values, color=colours)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1)
    ax.set_ylabel("P(mechanism active | A_epsilon)")
    ax.set_title(
        "(B) Residual mechanism ambiguity\n"
        f"D={result.mechanism_entropy}, R={result.mechanism_resolvability}"
    )

    ax = axes[2]
    candidates = result.information_value_ranking[:5]
    candidate_labels = [label for label, _, _ in candidates]
    candidate_values = [value for _, value, _ in candidates]
    candidate_colours = [
        "#bdbdbd" if "nuisance" in label else "#2ca02c"
        for label in candidate_labels
    ]
    ax.barh(range(len(candidates)), candidate_values, color=candidate_colours)
    ax.set_yticks(range(len(candidates)))
    ax.set_yticklabels([label[:31] for label in candidate_labels], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("V(Q) = I(S; Q | A_epsilon) / K")
    ax.set_title("(C) What to measure next\ncurrent information value")

    ax = axes[3]
    before = [
        result.mechanism_admissibility["selfing_syndrome_active"],
        result.mechanism_admissibility["island_isolation_common_cause"],
    ]
    after = [
        result.mechanism_admissibility_after.get(
            "selfing_syndrome_active", float("nan")
        ),
        result.mechanism_admissibility_after.get(
            "island_isolation_common_cause", float("nan")
        ),
    ]
    x_positions = np.arange(2)
    width = 0.38
    ax.bar(
        x_positions - width / 2,
        before,
        width,
        label="ordinal targets",
        color="#bbbbbb",
    )
    ax.bar(
        x_positions + width / 2,
        after,
        width,
        label="+ quantitative guide",
        color="#d62728",
    )
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(["S2\nselfing pathway", "S3\ncommon cause"], fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("P(mechanism active | A_epsilon)")
    ax.set_title(
        "(D) Condition and re-evaluate\n"
        f"D {result.mechanism_entropy}->{result.entropy_after}, "
        f"R {result.mechanism_resolvability}->{result.resolvability_after}"
    )
    ax.legend(fontsize=7)

    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled mechanism-confounding and observation-design example"
    )
    parser.add_argument("--backend", choices=["proxy", "abm"], default="proxy")
    parser.add_argument("--n-attempts", type=int, default=600)
    parser.add_argument("--preset", default="literature_grounded")
    parser.add_argument("--rule", default="strict_all")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--figure", default="", help="PNG output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    result = run_controlled_confounding_demo(
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


__all__ = [
    "ControlledConfoundingResult",
    "make_figure",
    "print_report",
    "run_controlled_confounding_demo",
]


if __name__ == "__main__":
    raise SystemExit(main())
