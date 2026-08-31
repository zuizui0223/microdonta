from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_builder():
    path = ROOT / "paper" / "build_boundary_reviewer_bundle.py"
    spec = importlib.util.spec_from_file_location("boundary_reviewer_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_boundary_reviewer_bundle_is_isolated_and_self_contained(tmp_path):
    builder = _load_builder()

    figures = tmp_path / "figures"
    figures.mkdir()
    for name in (
        "mechanistic_evidence_axes.png",
        "boundary_identification_geometry.png",
        "multichannel_anchor_dimension.png",
    ):
        (figures / name).write_bytes(b"review-figure-placeholder")

    output = tmp_path / "boundary_reviewer_bundle"
    manifest_path, archive_path = builder.build(output, figures)

    assert manifest_path.exists()
    assert archive_path.exists() and archive_path.stat().st_size > 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["boundary_manuscript_included"] is True
    assert manifest["mee_manuscript_included"] is False
    assert manifest["rach_method_code_included"] is False
    assert manifest["public_repository_metadata_included"] is False

    paths = set(manifest["files"])
    assert "review_manuscript.md" in paths
    assert "figures/mechanistic_evidence_axes.png" in paths
    assert "figures/boundary_identification_geometry.png" in paths
    assert "figures/multichannel_anchor_dimension.png" in paths
    assert "reference_notes/mechanistic_evidence_identification_axis.md" in paths
    assert "causal_model/multichannel_identifiability.py" in paths
    assert "causal_model/calibration_transport_family.py" in paths
    assert not any("mee_manuscript" in path for path in paths)
    assert not any("nov_evsi.py" in path for path in paths)
    assert not any("rach_seq.py" in path for path in paths)
    assert not any("g2_frozen" in path for path in paths)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(output)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--rootdir=.", "-q", "tests"],
        cwd=output,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
