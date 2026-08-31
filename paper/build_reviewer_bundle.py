"""Build a deterministic, double-anonymous reviewer bundle for the methods paper.

The bundle is an allowlisted Mechanism-Resolving Observation Design snapshot, not
a repository archive. Author metadata, public repository metadata, the external
Paper A programme, apps and optional research programmes are omitted.
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
    "causal_model/mechanism_region.py",
    "causal_model/mechanism_replaceability_core.py",
    "causal_model/sequential_observation.py",
    "causal_model/observation_information.py",
    "causal_model/admissible_mechanisms.py",
    "causal_model/observation_value.py",
    "causal_model/sequential_design.py",
    "causal_model/mechanism_replaceability.py",
    "causal_model/mechanism_equivalence.py",
]
REFERENCE_SOURCES = [
    "causal_model/generality_sweep.py",
    "causal_model/known_truth_benchmark.py",
    "causal_model/observation_value_calibration.py",
    "causal_model/controlled_confounding_demo.py",
]
FORBIDDEN_TEXT = (
    "Ruiqi Zhang",
    "Kyoto University",
    "rachelzhang0223",
    "github.com/zuizui0223",
)
COMMIT_SHA_RE = re.compile(r"(?<![0-9a-f])\b[0-9a-f]{40}\b(?![0-9a-f])", re.I)

PRIMARY_INIT = '''"""Mechanism-Resolving Observation Design reviewer API."""
import sys
from . import mechanism_region as _mechanism_region_backend
sys.modules.setdefault(__name__ + ".causal_admissibility", _mechanism_region_backend)
from . import mechanism_replaceability_core as _replaceability_backend
sys.modules.setdefault(__name__ + ".causal_replaceability", _replaceability_backend)
from . import sequential_observation as _sequential_backend
sys.modules.setdefault(__name__ + ".rach_seq", _sequential_backend)
from . import observation_information as _information_backend
sys.modules.setdefault(__name__ + ".nov_evsi", _information_backend)

from .admissible_mechanisms import (
    CandidateInformationValueResult, CandidateObservation, CandidateOutcome,
    MechanismAdmissibilityResult, MechanismResolutionSummary,
    ObservationContribution, compute_admissible_mechanisms,
    heuristic_observation_value, mechanism_entropy, mechanism_resolvability,
    mechanism_resolution_summary, observation_contribution,
)
from .observation_value import (
    InformationValueResult, candidate_mutual_information_bits,
    observation_information_value,
)
from .sequential_design import (
    PredictiveOutcomeDistribution, SequentialDesignResult, SequentialDesignStep,
    expected_edge_cuts, filter_by_outcome, predictive_outcome_distribution,
    sequential_candidate_value, sequential_observation_design,
    validated_information_value,
)
from .mechanism_replaceability import (
    ReplaceabilityResult, mechanism_replaceability_cost,
    mechanism_replaceability_cost_full, mechanism_replaceability_profile,
    mechanism_replaceability_profile_full,
)
from .mechanism_equivalence import mechanism_equivalence_structure

__all__ = [
    "CandidateInformationValueResult", "CandidateObservation", "CandidateOutcome",
    "InformationValueResult", "MechanismAdmissibilityResult",
    "MechanismResolutionSummary", "ObservationContribution",
    "PredictiveOutcomeDistribution", "ReplaceabilityResult",
    "SequentialDesignResult", "SequentialDesignStep",
    "candidate_mutual_information_bits", "compute_admissible_mechanisms",
    "expected_edge_cuts", "filter_by_outcome", "heuristic_observation_value",
    "mechanism_entropy", "mechanism_equivalence_structure",
    "mechanism_replaceability_cost", "mechanism_replaceability_cost_full",
    "mechanism_replaceability_profile", "mechanism_replaceability_profile_full",
    "mechanism_resolvability", "mechanism_resolution_summary",
    "observation_contribution", "observation_information_value",
    "predictive_outcome_distribution", "sequential_candidate_value",
    "sequential_observation_design", "validated_information_value",
]
'''

REVIEW_TEST = '''import json
from pathlib import Path
import causal_model as method
from causal_model import CandidateObservation, CandidateOutcome

class _SW:
    def __init__(self, name): self.name=name

def candidate():
    return CandidateObservation(
        name="trait", description="resolving trait", target_switches=["A"],
        rationale="outcomes separate A", outcomes=[
            CandidateOutcome(name="high", description="high", prior_probability=.5,
                extra_pattern_rows=[{"type":"absolute_summary","variable":"trait","population":"pop","observed_value":"0.75","scale":"0.05"}]),
            CandidateOutcome(name="low", description="low", prior_probability=.5,
                extra_pattern_rows=[{"type":"absolute_summary","variable":"trait","population":"pop","observed_value":"0.25","scale":"0.05"}]),
        ])

def test_information_value_public_surface():
    rows=([{"A":True,"pop_trait":.75},{"A":False,"pop_trait":.25}])*20
    result=method.observation_information_value(rows,[_SW("A")],[candidate()])[0]
    assert result.estimable and result.partition_verified
    assert result.mutual_information_bits == 1.0
    assert result.information_value == 1.0

def test_bundle_preserves_frozen_headline_values():
    data=json.loads(Path("frozen/g2_summary.json").read_text())
    def row(policy,budget):
        return next(r for r in data["policy_budget_aggregate"] if r["policy"]==policy and r["budget"]==budget)
    guided2=row("rach_seq",2); random2=row("random_order",2); guided4=row("rach_seq",4); random4=row("random_order",4)
    assert guided2["mean_frac_resolved_mean"] == 1.0
    assert guided2["frac_converged_mean"] == .99
    assert random2["mean_frac_resolved_mean"] == .6045
    assert random2["frac_converged_mean"] == .435
    assert guided4["mean_distractors_selected_mean"] == .014
    assert random4["mean_distractors_selected_mean"] == 1.169
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
    parts = list(current.relative_to(ROOT).with_suffix("").parts[:-1])
    if level > 0:
        parts = parts[: max(0, len(parts) - (level - 1))]
    if module:
        parts.extend(module.split("."))
    if not parts:
        return None
    candidate = ROOT.joinpath(*parts).with_suffix(".py")
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
            dep = relative_module_path(path, node.level, node.module) if node.level else local_module_path(node.module or "")
            if dep:
                found.add(dep)
    return found


def scientific_module_closure() -> list[Path]:
    pending = [ROOT / path for path in RUNNABLE_SEEDS]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if not path.exists():
            raise SystemExit(f"missing reviewer dependency: {path.relative_to(ROOT)}")
        seen.add(path)
        for dep in dependencies(path):
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


def write_text(dst: Path, text: str) -> None:
    assert_anonymous_text(str(dst), text)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def build(output_dir: Path, figures_dir: Path) -> tuple[Path, Path]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    copy_text(ROOT / "paper/manuscript.md", output_dir / "review_manuscript.md")
    copy_text(ROOT / "paper/supporting_information.md", output_dir / "supporting_information.md")
    copy_text(ROOT / "docs/mechanism_resolution_theory.md", output_dir / "theory/mechanism_resolution_theory.md")
    copy_text(ROOT / "docs/observation_information_foundations.md", output_dir / "theory/observation_information_foundations.md")

    write_text(output_dir / "README_FOR_REVIEW.md", "# Anonymous Mechanism-Resolving Observation Design reviewer bundle\n\nRun `PYTHONPATH=. python -m pytest --rootdir=. -q tests`.\n")
    write_text(output_dir / "requirements-review.txt", "numpy>=1.24\npandas>=2.0\nmatplotlib>=3.7\npytest>=7\n")

    for src in scientific_module_closure():
        copy_text(src, output_dir / src.relative_to(ROOT))
    write_text(output_dir / "causal_model/__init__.py", PRIMARY_INIT)

    reference_dir = output_dir / "reference_sources"
    for rel in REFERENCE_SOURCES:
        copy_text(ROOT / rel, reference_dir / Path(rel).name)
    write_text(output_dir / "tests/test_review_surface.py", REVIEW_TEST)

    frozen = output_dir / "frozen"
    frozen.mkdir()
    copy_text(ROOT / "paper/g2_frozen_benchmark_protocol.json", frozen / "g2_protocol.json")
    write_text(frozen / "g2_summary.json", json.dumps(redact_result_summary(ROOT / "paper/results/g2_frozen_v2_summary.json"), indent=2, sort_keys=True) + "\n")
    write_text(frozen / "submission_validation_summary.json", json.dumps(redact_result_summary(ROOT / "paper/results/submission_validation_summary.json"), indent=2, sort_keys=True) + "\n")
    copy_text(ROOT / "paper/final_figure_inventory.json", frozen / "figure_inventory.json")

    expected_figures = {
        "figure1_controlled_confounding.png",
        "figure2_g2_frozen_v2.png",
        "figure3_information_value_calibration.png",
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
            assert_anonymous_text(path.relative_to(output_dir).as_posix(), path.read_text(encoding="utf-8"))

    manifest = {
        "schema_version": 4,
        "bundle_role": "double_anonymous_peer_review_methods_only",
        "method_name": "Mechanism-Resolving Observation Design",
        "public_repository_metadata_included": False,
        "title_page_included": False,
        "boundary_paper_included": False,
        "historical_frozen_labels_preserved": True,
        "retired_backend_filenames_included": False,
        "files": {},
    }
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(output_dir).as_posix()
        if rel == "bundle_manifest.json":
            continue
        manifest["files"][rel] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    manifest_path = output_dir / "bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
