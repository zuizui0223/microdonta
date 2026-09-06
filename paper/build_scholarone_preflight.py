"""Assemble anonymous ScholarOne preflight Markdown from the validated source tree.

This script does not declare the submission ready. It assembles the anonymous
Main Document and Supporting Information from the exact ``artifact_validation_sha``
source and copies the frozen Figure 1-3/S1 images beside them. Human title-page
metadata and the unresolved AI-application-version disclosure remain governed by
``paper/scholarone_upload_manifest.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

MAIN_FIGURES = (
    "figure1_controlled_confounding.png",
    "figure2_g2_frozen_v2.png",
    "figure3_information_value_calibration.png",
)
SUPP_FIGURE = "figureS1_known_truth.png"


def _strip_submission_track_note(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    skip_following_rule = False
    for line in lines:
        if line.startswith("> **Submission-track draft for Methods in Ecology and Evolution."):
            skip_following_rule = True
            continue
        if skip_following_rule and line.strip() == "":
            continue
        if skip_following_rule and line.strip() == "---":
            skip_following_rule = False
            continue
        skip_following_rule = False
        cleaned.append(line)
    return "\n".join(cleaned).strip() + "\n"


def assemble_main_text(text: str) -> str:
    text = _strip_submission_track_note(text)
    # Figure S1 belongs in the Supporting Information upload, not the Main Document.
    text = re.sub(r"\n\*\*Figure S1\.[^\n]*\n", "\n", text)
    insertions = {
        "**Figure 1.": f"![](figures/{MAIN_FIGURES[0]}){{ width=95% }}\n\n**Figure 1.",
        "**Figure 2.": f"![](figures/{MAIN_FIGURES[1]}){{ width=95% }}\n\n**Figure 2.",
        "**Figure 3.": f"![](figures/{MAIN_FIGURES[2]}){{ width=95% }}\n\n**Figure 3.",
    }
    for marker, replacement in insertions.items():
        if marker not in text:
            raise ValueError(f"missing Main Document caption marker: {marker}")
        text = text.replace(marker, replacement, 1)
    return text


def assemble_supporting_text(text: str) -> str:
    marker = "**Figure S1."
    if marker not in text:
        raise ValueError("missing Supporting Information Figure S1 caption")
    return text.replace(
        marker,
        f"![](figures/{SUPP_FIGURE}){{ width=95% }}\n\n{marker}",
        1,
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(source_root: Path, figures_dir: Path, output_dir: Path, source_sha: str) -> Path:
    manuscript = source_root / "paper" / "manuscript.md"
    supplement = source_root / "paper" / "supporting_information.md"
    if not manuscript.exists() or not supplement.exists():
        raise FileNotFoundError("validated manuscript or Supporting Information source is missing")

    output_dir.mkdir(parents=True, exist_ok=True)
    copied_figures = output_dir / "figures"
    copied_figures.mkdir(parents=True, exist_ok=True)

    for name in (*MAIN_FIGURES, SUPP_FIGURE):
        src = figures_dir / name
        if not src.exists() or src.stat().st_size == 0:
            raise FileNotFoundError(f"missing rebuilt figure: {src}")
        shutil.copy2(src, copied_figures / name)

    main_out = output_dir / "main_document_preflight.md"
    supp_out = output_dir / "supporting_information_preflight.md"
    main_out.write_text(assemble_main_text(manuscript.read_text(encoding="utf-8")), encoding="utf-8")
    supp_out.write_text(assemble_supporting_text(supplement.read_text(encoding="utf-8")), encoding="utf-8")

    manifest = {
        "schema_version": 1,
        "purpose": "ScholarOne anonymous PDF preflight assembly",
        "validated_source_sha": source_sha,
        "final_submission_ready": False,
        "readiness_note": "Human ScholarOne blockers remain authoritative in paper/scholarone_upload_manifest.json.",
        "main_document": main_out.name,
        "supporting_information": supp_out.name,
        "figures": {
            name: _sha256(copied_figures / name)
            for name in (*MAIN_FIGURES, SUPP_FIGURE)
        },
    }
    manifest_path = output_dir / "preflight_assembly_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    path = build(args.source_root, args.figures_dir, args.output_dir, args.source_sha)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
