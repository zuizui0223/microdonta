"""Fail CI when the methods-only scientific submission boundary drifts."""
from __future__ import annotations

import json
from math import isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT_PATH = ROOT / "paper" / "manuscript.md"
MAINLINE_PATH = ROOT / "docs" / "mainline.md"
SCOPE_PATH = ROOT / "paper" / "REPOSITORY_SCOPE.md"
THEORY_PATH = ROOT / "docs" / "mechanism_resolution_theory.md"
FOUNDATIONS_PATH = ROOT / "docs" / "observation_information_foundations.md"
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


def require(label: str, text: str, markers: tuple[str, ...]) -> None:
    missing = [m for m in markers if m not in text]
    if missing:
        raise SystemExit(f"{label} markers are missing:\n- " + "\n- ".join(missing))


def budget_row(summary: dict, policy: str, budget: int) -> dict:
    matches = [row for row in summary["policy_budget_aggregate"] if row["policy"] == policy and row["budget"] == budget]
    if len(matches) != 1:
        raise SystemExit(f"expected one G2 row for {policy=} {budget=}")
    return matches[0]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("primary_product") != "Mechanism-Resolving Observation Design":
        raise SystemExit("primary product name drifted")
    expected_spine = [
        "admissible mechanism region and residual mechanism ambiguity",
        "observation information value equals normalized mechanism-observation mutual information",
        "sequential observation design recomputes and selects maximum current information value",
        "truth-peek-free G2 matched-policy selection validation",
        "reproducible software and reviewer evidence bundle",
    ]
    if manifest.get("claim_spine") != expected_spine:
        raise SystemExit("methods-paper claim spine drifted")

    inventory = {
        "governance": manifest.get("governance", []),
        "main_text": manifest.get("main_text", {}),
        "supplementary": manifest.get("supplementary", {}),
        "archive": manifest.get("archive", []),
    }
    missing_paths = sorted(path for path in set(iter_paths(inventory)) if not (ROOT / path).exists())
    if missing_paths:
        raise SystemExit("submission manifest contains missing paths:\n- " + "\n- ".join(missing_paths))

    companion = manifest.get("external_companion", {})
    if companion.get("repository") != "zuizui0223/boundary":
        raise SystemExit("Paper A owner is not the boundary repository")
    if companion.get("submission_blocker_for_mee") is not False:
        raise SystemExit("Paper A may not block the methods submission")
    if companion.get("local_active_copy_allowed") is not False:
        raise SystemExit("local active Paper A copies must remain forbidden")

    forbidden_local = (
        "paper/boundary_manuscript_submission.md",
        "paper/ecology_letters_perspective_proposal.md",
        "paper/build_boundary_reviewer_bundle.py",
        "causal_model/multichannel_identifiability.py",
        "causal_model/calibration_transport_family.py",
        "causal_model/bounded_proxy_drift.py",
        "causal_model/channel_identifiability_theory.py",
        "causal_model/proxy_calibration_theory.py",
    )
    leaked = [p for p in forbidden_local if (ROOT / p).exists()]
    if leaked:
        raise SystemExit("active Paper A material remains local:\n- " + "\n- ".join(leaked))

    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    require("methods manuscript", manuscript, (
        "Mechanism-Resolving Observation Design",
        "V(Q)=I(S;Q|A_epsilon)/K",
        "information-guided design",
        "1.169 mechanism-independent nuisance measurements",
        "0.014 under information-guided design",
        "83.5-fold difference",
        "Hidden-truth false exclusion was zero",
        "No new empirical data are reported",
    ))

    require("mainline", MAINLINE_PATH.read_text(encoding="utf-8"), (
        "Mechanism-Resolving Observation Design",
        "observation information value V(Q)=I(S;Q | A_epsilon)/K",
        "information-guided selection",
        "1.169/0.014 = 83.5-fold",
        "zuizui0223/boundary",
    ))
    require("repository scope", SCOPE_PATH.read_text(encoding="utf-8"), (
        "Mechanism-Resolving Observation Design",
        "local active copy",
        "No double counting",
    ))
    require("theory", THEORY_PATH.read_text(encoding="utf-8"), (
        "admissible mechanism region",
        "V(Q)",
        "sequential observation design",
        "Retired project acronyms",
    ))
    require("foundations", FOUNDATIONS_PATH.read_text(encoding="utf-8"), (
        "V(Q)",
        "I(S;Q | A)/K",
        "conditional independence",
        "sequential recomputation",
    ))

    protocol = json.loads(G2_PROTOCOL_PATH.read_text(encoding="utf-8"))
    # Historical strings are immutable provenance, not the active method name.
    if protocol.get("protocol_id") != "rach-g2-truth-peek-free-v2":
        raise SystemExit("frozen G2 protocol identifier changed")
    if protocol.get("supersedes") != "rach-g2-truth-peek-free-v1":
        raise SystemExit("G2 v1 supersession provenance changed")
    if protocol.get("generator", {}).get("distractor_candidates", {}).get("count") != 2:
        raise SystemExit("G2 must retain exactly two nuisance candidates")
    selection = protocol.get("selection_validation", {})
    if selection.get("policies") != ["rach_seq", "random_order"]:
        raise SystemExit("historical G2 policy keys changed")
    if not selection.get("same_systems_truths_candidates_and_budgets_across_policies"):
        raise SystemExit("G2 policies must remain matched")
    if not selection.get("policy_comparison_is_descriptive_not_acceptance_gate"):
        raise SystemExit("G2 comparison must remain descriptive")
    if protocol.get("reporting", {}).get("performance_acceptance_thresholds") != "none_report_all_frozen_outcomes":
        raise SystemExit("G2 protocol may not encode a favourable threshold")

    summary = json.loads(G2_RESULTS_PATH.read_text(encoding="utf-8"))
    guided2 = budget_row(summary, "rach_seq", 2)
    random2 = budget_row(summary, "random_order", 2)
    guided4 = budget_row(summary, "rach_seq", 4)
    random4 = budget_row(summary, "random_order", 4)
    checks = [
        (guided2["mean_frac_resolved_mean"], 1.0, "guided budget-2 edge resolution"),
        (guided2["frac_converged_mean"], 0.99, "guided budget-2 convergence"),
        (random2["mean_frac_resolved_mean"], 0.6045, "random budget-2 edge resolution"),
        (random2["frac_converged_mean"], 0.435, "random budget-2 convergence"),
        (guided4["mean_distractors_selected_mean"], 0.014, "guided budget-4 nuisance"),
        (random4["mean_distractors_selected_mean"], 1.169, "random budget-4 nuisance"),
        (guided4["mean_steps_mean"], 1.518, "guided budget-4 observations"),
        (random4["mean_steps_mean"], 2.673, "random budget-4 observations"),
    ]
    for actual, expected, label in checks:
        if not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12):
            raise SystemExit(f"frozen {label} changed: {actual} != {expected}")
    fold = random4["mean_distractors_selected_mean"] / guided4["mean_distractors_selected_mean"]
    reduction = 1.0 - guided4["mean_distractors_selected_mean"] / random4["mean_distractors_selected_mean"]
    if not isclose(fold, 83.5, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"budget-4 nuisance fold contrast changed: {fold}")
    if not isclose(reduction, 0.9880239520958084, rel_tol=0.0, abs_tol=1e-12):
        raise SystemExit(f"budget-4 nuisance reduction changed: {reduction}")
    if any(row["false_exclusion_rate_mean"] != 0.0 for row in summary["policy_budget_aggregate"]):
        raise SystemExit("hidden-truth false exclusion is no longer zero in all G2 cells")

    print("submission bundle OK")
    print(f"target: {manifest['primary_target']}")
    print(f"product: {manifest['primary_product']}")
    print("spine: " + " -> ".join(manifest["claim_spine"]))
    print(f"historical G2 protocol: {protocol['protocol_id']}")
    print(f"budget-4 nuisance selection ratio: {fold:.1f}-fold")
    print(f"budget-4 nuisance reduction: {100 * reduction:.1f}%")
    print("Paper A owner: zuizui0223/boundary")


if __name__ == "__main__":
    main()
