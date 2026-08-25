"""Fail CI when the primary submission boundary drifts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT_PATH = ROOT / "paper" / "mee_manuscript_draft.md"
MAINLINE_PATH = ROOT / "docs" / "mainline.md"
THEORY_PATH = ROOT / "docs" / "rach_theory.md"
FOUNDATIONS_PATH = ROOT / "docs" / "rach_mathematical_foundations.md"
G2_PROTOCOL_PATH = ROOT / "paper" / "g2_frozen_benchmark_protocol.json"


def iter_paths(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_paths(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_paths(item)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    missing = sorted(
        path for path in set(iter_paths({
            "governance": manifest.get("governance", []),
            "main_text": manifest["main_text"],
            "supplementary": manifest["supplementary"],
            "archive": manifest["archive"],
        }))
        if not (ROOT / path).exists()
    )
    if missing:
        raise SystemExit("submission manifest contains missing paths:\n- " + "\n- ".join(missing))

    manuscript = MANUSCRIPT_PATH.read_text(encoding="utf-8")
    required = [
        "Frozen G2 v2 results below come only",
        "maximum current validated NOV",
        "0.990 ± 0.0079",
        "paper/results/g2_frozen_v2_summary.json",
        "Exact channel-identifiability boundary",
        "N1: net-only observations cannot identify the changed channel",
        "N2: net performance plus one channel is sufficient",
        "N3–N4: proxy calibration is the operational boundary",
        "RACH: admissible explanations and next-observation design",
        "I(S;Q|A_ε)/K",
        "Generality and observation-budget error control",
        "random_order",
        "Exact ecological projection and ABM boundary",
        "Prospective worked design: Izu Islands *Campanula*",
    ]
    absent = [marker for marker in required if marker not in manuscript]
    if absent:
        raise SystemExit("theorem-first manuscript markers are missing:\n- " + "\n- ".join(absent))

    forbidden_main_claims = [
        "### 3.5 Agreement with established ecological rules",
        "### 4.1 Discovering the path from the pattern",
        "### 4.3 Transfer to a published animal rule",
        "publication-grade worked example now",
        "Tier-A (validated) simulator",
        "99.2% of confounding edges",
        "98.5% of systems fully converging",
        "maximum expected confounding-edge cuts",
        "rank candidates by expected confounding-edge cuts",
    ]
    present = [marker for marker in forbidden_main_claims if marker in manuscript]
    if present:
        raise SystemExit(
            "excluded or pre-fix claims re-entered the primary manuscript:\n- "
            + "\n- ".join(present)
        )

    mainline = MAINLINE_PATH.read_text(encoding="utf-8")
    mainline_required = [
        "microdonta has one scientific product",
        "N1-N4 exact channel-identifiability boundary",
        "next_observation_evsi",
        "I(S;Q | A_epsilon) / K",
        "heuristic_next_observation_value",
        "descriptive, not an acceptance gate",
        "random_order",
        "Pass G2",
        "Pass G5",
        "What is not the mainline",
    ]
    absent_mainline = [marker for marker in mainline_required if marker not in mainline]
    if absent_mainline:
        raise SystemExit(
            "normative RACH mainline markers are missing:\n- " + "\n- ".join(absent_mainline)
        )

    theory = THEORY_PATH.read_text(encoding="utf-8")
    theory_required = [
        "I(S;Q | A_epsilon) / K",
        "heuristic_next_observation_value",
        "next_observation_evsi",
        "There is no favourable-result acceptance threshold",
    ]
    absent_theory = [marker for marker in theory_required if marker not in theory]
    if absent_theory:
        raise SystemExit(
            "RACH theory drifted from the publication mainline:\n- "
            + "\n- ".join(absent_theory)
        )

    foundations = FOUNDATIONS_PATH.read_text(encoding="utf-8")
    foundation_required = [
        "Validated NOV is normalised mechanism–observation information",
        "I(S ; Q | A_ε) / K",
        "0 ≤ NOV(Q) ≤ H(S | A_ε)/K",
    ]
    absent_foundations = [
        marker for marker in foundation_required if marker not in foundations
    ]
    if absent_foundations:
        raise SystemExit(
            "RACH mathematical foundations are missing NOV information identity:\n- "
            + "\n- ".join(absent_foundations)
        )

    method_paths = set(manifest["main_text"].get("method", []))
    if "causal_model/nov_evsi.py" not in method_paths:
        raise SystemExit(
            "validated NOV EVSI implementation is missing from main-text method inventory"
        )

    protocol = json.loads(G2_PROTOCOL_PATH.read_text(encoding="utf-8"))
    if protocol.get("protocol_id") != "rach-g2-truth-peek-free-v2":
        raise SystemExit("current G2 protocol is not frozen selection-validation v2")
    if protocol.get("supersedes") != "rach-g2-truth-peek-free-v1":
        raise SystemExit("G2 v1 supersession provenance is missing")
    distractors = protocol.get("generator", {}).get("distractor_candidates", {})
    if distractors.get("count") != 2:
        raise SystemExit("G2 v2 must retain exactly two preregistered distractor candidates")
    selection = protocol.get("selection_validation", {})
    if selection.get("policies") != ["rach_seq", "random_order"]:
        raise SystemExit("G2 v2 must compare RACH-SEQ with the random-order baseline")
    if not selection.get("same_systems_truths_candidates_and_budgets_across_policies"):
        raise SystemExit("G2 policy comparison must be matched on generated systems")
    if not selection.get("policy_comparison_is_descriptive_not_acceptance_gate"):
        raise SystemExit("G2 policy contrast must remain descriptive, not a success gate")

    reporting = protocol.get("reporting", {})
    required_reporting = [
        "per_system_records_required",
        "per_seed_required",
        "policy_rows_required",
        "policy_contrast_rows_required",
        "protocol_sha256_required_on_every_output_row",
        "clean_git_commit_sha_required_on_every_output_row",
        "matched_system_signatures_verified_before_aggregation",
    ]
    missing_reporting = [key for key in required_reporting if reporting.get(key) is not True]
    if missing_reporting:
        raise SystemExit(
            "G2 provenance/reporting requirements are missing:\n- "
            + "\n- ".join(missing_reporting)
        )
    if reporting.get("performance_acceptance_thresholds") != "none_report_all_frozen_outcomes":
        raise SystemExit("G2 protocol may not encode a favourable-result acceptance threshold")

    print("submission bundle OK")
    print(f"target: {manifest['primary_target']}")
    print("spine: " + " -> ".join(manifest["claim_spine"]))
    print("governance: " + ", ".join(manifest.get("governance", [])))
    print(f"g2 protocol: {protocol['protocol_id']}")


if __name__ == "__main__":
    main()
