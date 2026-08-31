"""Build a deterministic anonymous reviewer bundle for the boundary paper.

The bundle is an allowlisted identification-theory snapshot, not a repository
archive. The separate RACH/MEE manuscript, RACH/NOV/G2 implementation, author
metadata and public repository locators are intentionally excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

THEORY_FILES = [
    "causal_model/multichannel_identifiability.py",
    "causal_model/calibration_transport_family.py",
    "causal_model/bounded_proxy_drift.py",
    "causal_model/proxy_calibration_theory.py",
]

FIGURE_SOURCES = [
    "paper/make_mechanistic_evidence_axis_figure.py",
    "paper/make_multichannel_anchor_figure.py",
    "paper/make_boundary_identification_figure.py",
]

# Reviewer tests must run inside the allowlisted snapshot without depending on
# repository governance files or original repository paths.
TEST_FILES = [
    "tests/test_multichannel_identifiability.py",
    "tests/test_calibration_transport_family.py",
    "tests/test_bounded_proxy_drift.py",
]

REFERENCE_NOTES = [
    "paper/mechanistic_evidence_identification_axis.md",
    "paper/mechanistic_evidence_literature_audit.md",
    "paper/multiplicative_measurement_literature_audit.md",
]

FORBIDDEN_TEXT = (
    "Ruiqi Zhang",
    "Kyoto University",
    "rachelzhang0223",
    "github.com/zuizui0223",
)

FORBIDDEN_BUNDLE_PATHS = (
    "mee_manuscript_draft.md",
    "supporting_information.md",
    "generality_sweep.py",
    "nov_evsi.py",
    "rach_seq.py",
    "g2_frozen",
)

COMMIT_SHA_RE = re.compile(r"(?<![0-9a-f])\b[0-9a-f]{40}\b(?![0-9a-f])", re.I)

REVIEW_COUPLING_TEST = '''from math import isclose

from causal_model.bounded_proxy_drift import identify_under_bounded_proxy_drift
from causal_model.calibration_transport_family import breakdown_factor
from causal_model.multichannel_identifiability import residual_equivalence_dimension


def test_review_snapshot_keeps_the_three_boundary_claims():
    chain = residual_equivalence_dimension(channels=5, independent_anchors=2)
    assert chain.residual_dimension == 2

    gamma_star, _ = breakdown_factor(1.0 / 1.34)
    assert isclose(gamma_star, 1.34)

    rho_e_hat = 1.0 / 1.34
    rho_x = 0.8
    result = identify_under_bounded_proxy_drift(
        net_ratio=rho_x * rho_e_hat,
        proxy_ratio=rho_x,
        delta=0.2,
        proxy_channel="fecundity",
    )
    assert result.joint_log_segment.slope == -1.0
    assert result.joint_log_segment.satisfies_net_constraint()
    assert not isclose(
        result.fecundity.upper * result.establishment.upper,
        result.net_ratio,
    )
'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_anonymous_text(label: str, text: str) -> None:
    for token in FORBIDDEN_TEXT:
        if token.lower() in text.lower():
            raise SystemExit(f"identifying token in boundary reviewer bundle {label}: {token}")
    if COMMIT_SHA_RE.search(text):
        raise SystemExit(f"Git commit-like SHA in boundary reviewer bundle {label}")


def copy_text(src: Path, dst: Path) -> None:
    if not src.exists():
        raise SystemExit(f"missing boundary reviewer source: {src.relative_to(ROOT)}")
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

    copy_text(
        ROOT / "paper/boundary_manuscript_submission.md",
        output_dir / "review_manuscript.md",
    )

    readme = """# Anonymous reviewer code and evidence bundle\n\nThis snapshot contains the scientific files needed to evaluate the submitted ecological mechanism-identification boundary paper. The separate RACH/NOV/RACH-SEQ manuscript and benchmark are not included. Public repository metadata, author metadata and Git commit identifiers are also excluded.\n\nThe main theory sources are under `causal_model/`; figure generators are under `figure_sources/`; direct theorem tests are under `tests/`; and `reference_notes/` contains the mechanistic-evidence scope/literature audits plus the primary-literature measurement-architecture audit.\n\n## Minimal environment\n\n```bash\npython -m pip install -r requirements-review.txt\nPYTHONPATH=. python -m pytest --rootdir=. -q tests\n```\n\nThe supplied figures are under `figures/`. `bundle_manifest.json` records SHA-256 hashes for every file.\n"""
    write_text(output_dir / "README_FOR_REVIEW.md", readme)
    write_text(
        output_dir / "requirements-review.txt",
        "numpy>=1.24\nmatplotlib>=3.7\npytest>=7\n",
    )

    write_text(
        output_dir / "causal_model/__init__.py",
        '"""Boundary-paper theory snapshot for anonymous peer review."""\n',
    )
    for rel in THEORY_FILES:
        copy_text(ROOT / rel, output_dir / rel)

    for rel in FIGURE_SOURCES:
        copy_text(ROOT / rel, output_dir / "figure_sources" / Path(rel).name)

    for rel in TEST_FILES:
        copy_text(ROOT / rel, output_dir / rel)
    write_text(output_dir / "tests/test_boundary_reviewer_core.py", REVIEW_COUPLING_TEST)

    for rel in REFERENCE_NOTES:
        copy_text(ROOT / rel, output_dir / "reference_notes" / Path(rel).name)

    expected_figures = {
        "mechanistic_evidence_axes.png",
        "multichannel_anchor_dimension.png",
        "boundary_identification_geometry.png",
    }
    out_fig = output_dir / "figures"
    out_fig.mkdir()
    for name in sorted(expected_figures):
        src = figures_dir / name
        if not src.exists() or src.stat().st_size == 0:
            raise SystemExit(f"missing rebuilt boundary reviewer figure: {src}")
        shutil.copy2(src, out_fig / name)

    # Final content/path audit.
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(output_dir).as_posix()
        for forbidden in FORBIDDEN_BUNDLE_PATHS:
            if forbidden in rel:
                raise SystemExit(f"RACH/MEE file entered boundary reviewer bundle: {rel}")
        if path.suffix.lower() in {".md", ".py", ".txt", ".json"}:
            assert_anonymous_text(rel, path.read_text(encoding="utf-8"))

    manifest = {
        "schema_version": 1,
        "bundle_role": "anonymous_peer_review_boundary_only",
        "public_repository_metadata_included": False,
        "title_page_included": False,
        "mee_manuscript_included": False,
        "rach_method_code_included": False,
        "boundary_manuscript_included": True,
        "files": {},
    }
    for path in sorted(p for p in output_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(output_dir).as_posix()
        if rel == "bundle_manifest.json":
            continue
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
    parser.add_argument("--output-dir", default="outputs/boundary/reviewer_bundle")
    parser.add_argument("--figures-dir", default="paper/figures")
    args = parser.parse_args()
    manifest, archive = build(ROOT / args.output_dir, ROOT / args.figures_dir)
    print(manifest)
    print(archive)


if __name__ == "__main__":
    main()
