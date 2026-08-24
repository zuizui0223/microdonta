"""Fail CI when the primary submission boundary drifts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "paper" / "submission_manifest.json"
MANUSCRIPT_PATH = ROOT / "paper" / "mee_manuscript_draft.md"
MAINLINE_PATH = ROOT / "docs" / "mainline.md"


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
        "Numerical benchmark statements remain subject",
        "## 2. Exact channel-identifiability boundary",
        "### 2.2 N1:",
        "### 2.3 N2:",
        "### 2.4 N3–N4:",
        "## 3. RACH:",
        "## 4. Controlled validation",
        "## 5. Exact ecological projection and ABM boundary",
        "## 6. Prospective worked design:",
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
    ]
    present = [marker for marker in forbidden_main_claims if marker in manuscript]
    if present:
        raise SystemExit("excluded claims re-entered the primary manuscript:\n- " + "\n- ".join(present))

    mainline = MAINLINE_PATH.read_text(encoding="utf-8")
    mainline_required = [
        "microdonta has one scientific product",
        "N1-N4 exact channel-identifiability boundary",
        "next_observation_evsi",
        "validated admissible-region EVSI",
        "heuristic_next_observation_value",
        "performance threshold",
        "Pass G2",
        "Pass G5",
        "What is not the mainline",
    ]
    absent_mainline = [marker for marker in mainline_required if marker not in mainline]
    if absent_mainline:
        raise SystemExit(
            "normative RACH mainline markers are missing:\n- " + "\n- ".join(absent_mainline)
        )

    method_paths = set(manifest["main_text"].get("method", []))
    if "causal_model/nov_evsi.py" not in method_paths:
        raise SystemExit("validated NOV EVSI implementation is missing from main-text method inventory")

    print("submission bundle OK")
    print(f"target: {manifest['primary_target']}")
    print("spine: " + " -> ".join(manifest["claim_spine"]))
    print("governance: " + ", ".join(manifest.get("governance", [])))


if __name__ == "__main__":
    main()
