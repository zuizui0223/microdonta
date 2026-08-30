"""Fail CI when the methods-only MEE submission boundary drifts."""
from __future__ import annotations

import json
from math import isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT_PATH = ROOT / "paper" / "mee_manuscript_draft.md"
MAINLINE_PATH = ROOT / "docs" / "mainline.md"
STRATEGY_PATH = ROOT / "paper" / "TWO_PAPER_STRATEGY.md"
THEORY_PATH = ROOT / "docs" / "rach_theory.md"
FOUNDATIONS_PATH = ROOT / "docs" / "rach_mathematical_foundations.md"
G2_PROTOCOL_PATH = ROOT / "paper" / "g2_frozen_benchmark_protocol.json"
G2_RESULTS_PATH = ROOT / "paper" / "results" / "g2_frozen_v2_summary.json"


def iter_paths(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_paths(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_paths(item)


def require_markers(label: str, text: str, markers: list[str]) -> None:
    absent = [marker for marker in markers if marker not in text]
    if absent:
        raise SystemExit(f"{label} markers are missing:\n- " + "\n- ".join(absent))


def forbid_markers(label: str, text: str, markers: list[str]) -> None:
    present = [marker for marker in markers if marker in text]
    if present:
        raise SystemExit(f"excluded material entered {label}:\n- " + "\n- ".join(present))


def budget_row(summary: dict, policy: str, budget: int) -> dict:
    matches = [
        row
        for row in summary["policy_budget_aggregate"]
        if row["policy"] == policy and row["budget"] == budget
    ]
    if len(matches) != 1:
        raise SystemExit(f"expected one G2 row for {policy=} {budget=}")
    return matches[0]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    companion = manifest.get("companion_boundary_program", {})
    path_inventory = {
        "governance": manifest.get("governance", []),
        "main_text": manifest["main_text"],
        "supplementary": manifest["supplementary"],
        "companion_boundary_program": {
            "manuscript": companion.get("manuscript", []),
            "theory": companion.get("theory", []),
            "supporting_examples": companion.get("supporting_examples", []),
        },
        "archive": manifest["archive"],
    }
    missing = sorted(
        path
        for path in set(iter_paths(path_inventory))
        if not (ROOT / path).exists()
    )
    if missing:
        raise SystemExit(
            "submission manifest contains missing paths:\n- " + "\n- ".join(missing)
        )

    expected_spine = [
        "RACH admissible mechanism set and causal degeneracy",
        "validated NOV equals normalized mechanism-observation mutual information",
        "RACH-SEQ recomputes and selects maximum current NOV",
        "truth-peek-free G2 matched-policy selection validation",
        "reproducible software and reviewer evidence bundle",
    ]
    if manifest.get("claim_spine") != expected_spine:
        raise SystemExit("MEE claim spine is not the frozen methods-only sequence")
    if companion.get("submission_blocker_for_mee") is not False:
        raise SystemExit("boundary-paper completion may not block the MEE methods paper")

    method_paths = set(manifest["main_text"].get("method", []))
    if "causal_model/nov_evsi.py" not in method_paths:
        raise SystemExit("validated NOV implementation is missing from MEE method inventory")
    forbidden_primary_paths = {
        "causal_model/channel_identifiability_theory.py",
        "causal_model/proxy_calibration_theory.py",
        "causal_model/bounded_proxy_drift.py",
        "causal_model/colonization_recruitment_factorization.py",
        "causal_model/campanula_real_data.py",
    }
    leaked = sorted(forbidden_primary_paths & method_paths)
    if leaked:
        raise SystemExit(
            "boundary/projection code entered primary MEE method inventory:\n- "
            + "\n- ".join(leaked)
        )

    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    require_markers(
        "methods manuscript",
        manuscript,
        [
            "Channel-identifiability theorems, bounded proxy-drift intervals",
            "Restricted Admissible Causal Hypotheses (RACH)",
            "NOV(Q)=I(S;Q|A_ε)/K",
            "RACH-SEQ selects the candidate with maximum current NOV",
            "Frozen G2 truth-peek-free selection benchmark",
            "1.169 mechanism-independent nuisance measurements",
            "0.014 for RACH-SEQ",
            "83.5-fold difference",
            "98.8% reduction",
            "Hidden-truth false exclusion was zero",
            "No new empirical data are reported",
        ],
    )
    forbid_markers(
        "active MEE manuscript",
        manuscript,
        [
            "### 2.1 Exact channel-identifiability boundary",
            "N1: net-only observations cannot identify the changed channel",
            "N2: net performance plus one channel is sufficient",
            "N3–N4: proxy calibration is the operational boundary",
            "Exact ecological projection and ABM boundary",
            "Prospective worked design: Izu Islands *Campanula*",
            "99.2% of confounding edges",
            "98.5% of systems fully converging",
            "maximum expected confounding-edge cuts",
        ],
    )

    mainline = MAINLINE_PATH.read_text(encoding="utf-8")
    require_markers(
        "normative mainline",
        mainline,
        [
            "microdonta has one primary MEE scientific product",
            "validated NOV = I(S;Q | A_epsilon)/K",
            "RACH-SEQ maximum-current-NOV selection",
            "truth-peek-free selection challenge",
            "1.169/0.014 = 83.5-fold",
            "Separate boundary-paper programme",
            "Boundary-theory code may remain importable",
        ],
    )

    strategy = STRATEGY_PATH.read_text(encoding="utf-8")
    require_markers(
        "two-paper strategy",
        strategy,
        [
            "Paper A — channel-identifiability boundary",
            "bounded calibration-drift identification interval",
            "Paper B — RACH observation-selection method",
            "83.5-fold",
            "No result is counted in both papers as a primary contribution",
        ],
    )

    theory = THEORY_PATH.read_text(encoding="utf-8")
    require_markers(
        "RACH theory",
        theory,
        [
            "I(S;Q | A_epsilon) / K",
            "heuristic_next_observation_value",
            "next_observation_evsi",
            "There is no favourable-result acceptance threshold",
        ],
    )
    foundations = FOUNDATIONS_PATH.read_text(encoding="utf-8")
    require_markers(
        "RACH foundations",
        foundations,
        [
            "Validated NOV is normalised mechanism–observation information",
            "I(S ; Q | A_ε) / K",
            "0 ≤ NOV(Q) ≤ H(S | A_ε)/K",
        ],
    )

    protocol = json.loads(G2_PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != "rach-g2-truth-peek-free-v2":
        raise SystemExit("current G2 protocol is not frozen selection-validation v2")
    if protocol.get("supersedes") != "rach-g2-truth-peek-free-v1":
        raise SystemExit("G2 v1 supersession provenance is missing")
    distractors = protocol.get("generator", {}).get("distractor_candidates", {})
    if distractors.get("count") != 2:
        raise SystemExit("G2 v2 must retain exactly two nuisance candidates")
    selection = protocol.get("selection_validation", {})
    if selection.get("policies") != ["rach_seq", "random_order"]:
        raise SystemExit("G2 must compare RACH-SEQ with random order")
    if not selection.get("same_systems_truths_candidates_and_budgets_across_policies"):
        raise SystemExit("G2 policies must receive matched systems and candidates")
    if not selection.get("policy_comparison_is_descriptive_not_acceptance_gate"):
        raise SystemExit("G2 contrast must remain descriptive")

    reporting = protocol.get("reporting", {})
    if reporting.get("performance_acceptance_thresholds") != "none_report_all_frozen_outcomes":
        raise SystemExit("G2 protocol may not encode a favourable threshold")

    summary = json.loads(G2_RESULTS_PATH.read_text(encoding="utf-8"))
    rach2 = budget_row(summary, "rach_seq", 2)
    random2 = budget_row(summary, "random_order", 2)
    rach4 = budget_row(summary, "rach_seq", 4)
    random4 = budget_row(summary, "random_order", 4)

    checks = [
        (rach2["mean_frac_resolved_mean"], 1.0, "RACH budget-2 edge resolution"),
        (rach2["frac_converged_mean"], 0.99, "RACH budget-2 convergence"),
        (random2["mean_frac_resolved_mean"], 0.6045, "random budget-2 edge resolution"),
        (random2["frac_converged_mean"], 0.435, "random budget-2 convergence"),
        (rach4["mean_distractors_selected_mean"], 0.014, "RACH budget-4 nuisance"),
        (random4["mean_distractors_selected_mean"], 1.169, "random budget-4 nuisance"),
        (rach4["mean_steps_mean"], 1.518, "RACH budget-4 observations"),
        (random4["mean_steps_mean"], 2.673, "random budget-4 observations"),
    ]
    for actual, expected, label in checks:
        if not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
            raise SystemExit(f"frozen {label} changed: {actual} != {expected}")

    fold = random4["mean_distractors_selected_mean"] / rach4[
        "mean_distractors_selected_mean"
    ]
    reduction = 1.0 - rach4["mean_distractors_selected_mean"] / random4[
        "mean_distractors_selected_mean"
    ]
    if not isclose(fold, 83.5, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"budget-4 nuisance fold contrast changed: {fold}")
    if not isclose(reduction, 0.9880239520958084, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"budget-4 nuisance reduction changed: {reduction}")

    if any(
        row["false_exclusion_rate_mean"] != 0.0
        for row in summary["policy_budget_aggregate"]
    ):
        raise SystemExit("hidden-truth false exclusion is no longer zero in all G2 cells")

    print("submission bundle OK")
    print(f"target: {manifest['primary_target']}")
    print("spine: " + " -> ".join(manifest["claim_spine"]))
    print(f"g2 protocol: {protocol['protocol_id']}")
    print(f"budget-4 nuisance selection ratio: {fold:.1f}-fold")
    print(f"budget-4 nuisance reduction: {100 * reduction:.1f}%")
    print("boundary paper: separate and non-blocking")


if __name__ == "__main__":
    main()
