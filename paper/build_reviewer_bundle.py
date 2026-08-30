"""Build a deterministic, double-anonymous reviewer bundle for the RACH method paper.

The bundle is an allowlisted methods snapshot, not a repository archive. Author
metadata, public repository metadata, boundary-paper theory, ecological projection,
apps, optional backends, structure discovery and provisional ecological-rule
programs are omitted.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNNABLE_SEEDS = [
    "causal_model/causal_admissibility.py",
    "causal_model/causal_replaceability.py",
    "causal_model/mechanism_equivalence.py",
    "causal_model/nov_evsi.py",
    "causal_model/rach_seq.py",
    "causal_model/generality_sweep.py",
]

REFERENCE_SOURCES = [
    "causal_model/known_truth_benchmark.py",
    "causal_model/nov_calibration.py",
    "causal_model/confound_demo.py",
]

TEST_FILES = [
    "tests/test_nov_evsi.py",
    "tests/test_rach_seq_predictive_reweighting.py",
    "tests/test_rach_seq_nov_selection.py",
    "tests/test_causal_replaceability.py",
]

DENY_MODULE_PARTS = {
    "structure_discovery",
    "bergmann_worked_example",
    "ecological_rules_validation",
    "converse_bergmann",
    "rule_transition",
    "channel_identifiability",
    "proxy_calibration",
    "bounded_proxy_drift",
    "colonization_recruitment",
    "theorem_projection",
    "campanula",
}

FORBIDDEN_TEXT = (
    "Ruiqi Zhang",
    "Kyoto University",
    "rachelzhang0223",
    "github.com/zuizui0223",
)
COMMIT_SHA_RE = re.compile(r"(?<![0-9a-f])\b[0-9a-f]{40}\b(?![0-9a-f])", re.I)

PRIMARY_INIT = '''"""Primary RACH API snapshot for double-anonymous peer review."""
from . import causal_admissibility
from . import rach_seq

CandidateObservation = causal_admissibility.CandidateObservation
CandidateOutcome = causal_admissibility.CandidateOutcome
CausalAdmissibilityResult = causal_admissibility.CausalAdmissibilityResult
ObservationContribution = causal_admissibility.ObservationContribution
RACHSummary = causal_admissibility.RACHSummary
compute_causal_admissibility = causal_admissibility.causal_admissibility
causal_degeneracy = causal_admissibility.causal_degeneracy
causal_resolvability = causal_admissibility.causal_resolvability
observation_contribution = causal_admissibility.observation_contribution
rach_summary = causal_admissibility.rach_summary

SeqResult = rach_seq.SeqResult
SeqStep = rach_seq.SeqStep
run_rach_seq = rach_seq.rach_seq

from .nov_evsi import EVSIResult, next_observation_evsi
from .causal_replaceability import (
    CRCResult,
    causal_replaceability_cost,
    causal_replaceability_cost_full,
    crc_profile,
    crc_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

__all__ = [
    "CandidateObservation", "CandidateOutcome", "CausalAdmissibilityResult",
    "CRCResult", "EVSIResult", "ObservationContribution", "RACHSummary",
    "SeqResult", "SeqStep", "compute_causal_admissibility",
    "causal_degeneracy", "causal_replaceability_cost",
    "causal_replaceability_cost_full", "causal_resolvability", "crc_profile",
    "crc_profile_full", "mechanism_equivalence_structure",
    "next_observation_evsi", "observation_contribution", "run_rach_seq",
    "rach_summary",
]
'''

REVIEW_API_TEST = '''import causal_model as rach

EXPECTED = {
    "CandidateObservation", "CandidateOutcome", "CausalAdmissibilityResult",
    "CRCResult", "EVSIResult", "ObservationContribution", "RACHSummary",
    "SeqResult", "SeqStep", "compute_causal_admissibility",
    "causal_degeneracy", "causal_replaceability_cost",
    "causal_replaceability_cost_full", "causal_resolvability", "crc_profile",
    "crc_profile_full", "mechanism_equivalence_structure",
    "next_observation_evsi", "observation_contribution", "run_rach_seq",
    "rach_summary",
}

def test_reviewer_api_is_exact_primary_rach_surface():
    assert set(rach.__all__) == EXPECTED
    assert all(hasattr(rach, name) for name in EXPECTED)


def test_boundary_and_compatibility_helpers_are_not_primary_api():
    forbidden = {
        "install_rule_transition_contracts", "CausalStructure",
        "score_causal_structure", "heuristic_next_observation_value",
        "expected_edge_cuts", "filter_by_outcome",
        "identify_under_bounded_proxy_drift",
    }
    assert not (forbidden & set(rach.__all__))
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_module_path(module: str) -> Path | None:
    if module == "causal_model":
        return None
    if module.startswith("causal_model."):
        path = ROOT / (module.replace(".", "/") + ".py")
        return path if path.exists() else None
    return None


def relative_module_path(current: Path, level: int, module: str | None) -> Path | None:
    package_parts = list(current.relative_to(ROOT).with_suffix("").parts[:-1])
    if level > 0:
        keep = max(0, len(package_parts) - (level - 1))
        package_parts = package_parts[:keep]
    if module:
        package_parts.extend(module.split("."))
    if not package_parts:
        return None
    candidate = ROOT.joinpath(*package_parts).with_suffix(".py")
    return candidate if candidate.exists() else None


def dependencies(path: Path) -> set[Path]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dep = local_module_path(alias.name)
                if dep:
                    found.add(dep)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                dep = relative_module_path(path, node.level, node.module)
            elif node.module:
                dep = local_module_path(node.module)
            else:
                dep = None
            if dep:
                found.add(dep)
    return found


def excluded(rel: str) -> bool:
    return any(part in rel for part in DENY_MODULE_PARTS)


def scientific_module_closure() -> list[Path]:
    pending = [ROOT / path for path in RUNNABLE_SEEDS]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if not path.exists():
            raise SystemExit(f"missing reviewer seed/dependency: {path.relative_to(ROOT)}")
        rel = path.relative_to(ROOT).as_posix()
        if excluded(rel):
            raise SystemExit(f"excluded module entered reviewer closure: {rel}")
        seen.add(path)
        for dep in dependencies(path):
            dep_rel = dep.relative_to(ROOT).as_posix()
            if excluded(dep_rel):
                continue
            if dep not in seen:
                pending.append(dep)
    return sorted(seen)


def redact_result_summary(src: Path) -> dict:
    data = json.loads(src.read_text(encoding="utf-8"))
    for key in ("code_commit_sha", "workflow_run_id"):
        data.pop(key, None)
    artifact = data.get("artifact")
    if isinstance(artifact, dict):
        artifact.pop("id", None)
        artifact.pop("name", None)
    return data


def assert_anonymous_text(label: str, text: str) -> None:
    for token in FORBIDDEN_TEXT:
        if token.lower() in text.lower():
            raise SystemExit(f"identifying token in reviewer bundle {label}: {token}")
    if COMMIT_SHA_RE.search(text):
        raise SystemExit(f"Git commit-like SHA in reviewer bundle {label}")


def copy_text(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    assert_anonymous_text(str(src.relative_to(ROOT)), text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def write_review_text(dst: Path, text: str) -> None:
    assert_anonymous_text(str(dst), text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def build(output_dir: Path, figures_dir: Path) -> tuple[Path, Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    copy_text(ROOT / "paper/mee_manuscript_draft.md", output_dir / "review_manuscript.md")
    copy_text(ROOT / "paper/supporting_information.md", output_dir / "supporting_information.md")

    readme = """# Anonymous reviewer code and evidence bundle\n\nThis snapshot contains the scientific files needed to evaluate the submitted RACH observation-selection Research Article. Author/title-page metadata, public repository URLs, public Git commit identifiers, the separate channel-identifiability/bounded-drift paper, ecological projection, apps, provisional ecological-rule programs and structure-discovery code are excluded.\n\n`causal_model/` is the runnable primary RACH/NOV/RACH-SEQ snapshot. `reference_sources/` contains exact auxiliary validation sources that are reviewed as source text without expanding optional repository dependencies.\n\n## Minimal environment\n\n```bash\npython -m pip install -r requirements-review.txt\nPYTHONPATH=. python -m pytest --rootdir=. -q tests\n```\n\nFrozen G2 protocol/results are under `frozen/`; Figures 1–3 and Figure S1 are under `figures/`; `bundle_manifest.json` records SHA-256 hashes.\n"""
    write_review_text(output_dir / "README_FOR_REVIEW.md", readme)
    write_review_text(
        output_dir / "requirements-review.txt",
        "numpy>=1.24\npandas>=2.0\nmatplotlib>=3.7\npytest>=7\n",
    )

    for src in scientific_module_closure():
        copy_text(src, output_dir / src.relative_to(ROOT))
    write_review_text(output_dir / "causal_model/__init__.py", PRIMARY_INIT)

    reference_dir = output_dir / "reference_sources"
    for rel in REFERENCE_SOURCES:
        copy_text(ROOT / rel, reference_dir / Path(rel).name)

    for rel in TEST_FILES:
        copy_text(ROOT / rel, output_dir / rel)
    write_review_text(output_dir / "tests/test_reviewer_public_api.py", REVIEW_API_TEST)

    frozen = output_dir / "frozen"
    frozen.mkdir()
    copy_text(ROOT / "paper/g2_frozen_benchmark_protocol.json", frozen / "g2_protocol.json")
    write_review_text(
        frozen / "g2_summary.json",
        json.dumps(
            redact_result_summary(ROOT / "paper/results/g2_frozen_v2_summary.json"),
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    write_review_text(
        frozen / "submission_validation_summary.json",
        json.dumps(
            redact_result_summary(
                ROOT / "paper/results/submission_validation_summary.json"
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    copy_text(ROOT / "paper/final_figure_inventory.json", frozen / "figure_inventory.json")

    expected_figures = {
        "figure1_confound.png",
        "figure2_g2_frozen_v2.png",
        "figure3_nov_calibration.png",
        "figureS1_known_truth.png",
    }
    out_fig = output_dir / "figures"
    out_fig.mkdir()
    for name in sorted(expected_figures):
        src = figures_dir / name
        if not src.exists() or src.stat().st_size == 0:
            raise SystemExit(f"missing rebuilt reviewer figure: {src}")
        shutil.copy2(src, out_fig / name)

    for path in output_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".py", ".json", ".txt"}:
            assert_anonymous_text(
                path.relative_to(output_dir).as_posix(),
                path.read_text(encoding="utf-8"),
            )

    manifest = {
        "schema_version": 2,
        "bundle_role": "double_anonymous_peer_review_methods_only",
        "public_repository_metadata_included": False,
        "title_page_included": False,
        "boundary_paper_included": False,
        "files": {},
    }
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(output_dir).as_posix()
        if rel == "bundle_manifest.json":
            continue
        if excluded(rel):
            raise SystemExit(f"excluded program file in reviewer bundle: {rel}")
        manifest["files"][rel] = {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    manifest_path = output_dir / "bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    zip_path = output_dir.parent / (output_dir.name + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
            archive.write(path, path.relative_to(output_dir.parent))
    return manifest_path, zip_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs/mee/reviewer_bundle")
    parser.add_argument("--figures-dir", default="outputs/g5/figures")
    args = parser.parse_args()
    manifest, archive = build(ROOT / args.output_dir, ROOT / args.figures_dir)
    print(manifest)
    print(archive)


if __name__ == "__main__":
    main()
