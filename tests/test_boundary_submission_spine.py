from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_boundary_submission_spine_keeps_two_axis_frame_and_three_quantitative_pillars():
    text = (ROOT / "paper" / "boundary_submission_spine.md").read_text(encoding="utf-8")

    # The Perspective headline is now the evidentiary distinction, while the
    # existing identification results remain the three quantitative pillars.
    assert "Governing conceptual distinction" in text
    assert "mechanistic proximity" in text
    assert "identification strength" in text
    assert "Three quantitative pillars" in text
    assert "Pillar 1 — Net-only information boundary" in text
    assert "Pillar 2 — Calibration-transport family and breakdown" in text
    assert "Pillar 3 — Operational consequences" in text

    # The reframe must remain explicitly non-hierarchical and non-anti-molecular.
    assert "does **not** assert a monotone relation between the axes" in text
    assert "molecular/genomic data can be highly proximal and highly identifying" in text
    assert "candidate mechanism set and observation map" in text

    assert "1/Gamma <= kappa <= Gamma" in text
    assert "Gamma* = max(rho_hat, 1/rho_hat)" in text
    assert "0 anchors" in text and "1 anchor" in text and "2 anchors" in text
    assert "Design Rule 2 — Preserve the coupling" in text

    # The legacy percentage parameterization must not be promoted back to the
    # canonical robustness scale.
    assert "delta` is the primary robustness scale" in text
    assert "34% upward drift" in text


def test_boundary_figure_source_uses_symmetric_gamma_family():
    text = (ROOT / "paper" / "make_boundary_identification_figure.py").read_text(encoding="utf-8")

    assert "calibration_transport_family" in text
    assert "breakdown_factor" in text
    assert "gamma_star" in text
    assert "delta_star" not in text
    assert "identify_under_bounded_proxy_drift" not in text
