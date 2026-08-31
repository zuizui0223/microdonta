from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_boundary_claim_evidence_matrix_covers_headline_and_three_quantitative_pillars():
    text = (ROOT / "paper" / "boundary_claim_evidence_matrix.md").read_text(encoding="utf-8")

    # Conceptual claim is literature-backed and explicitly scoped.
    assert "Mechanistic proximity and identification strength are non-equivalent properties" in text
    assert "Rudman et al. 2018" in text
    assert "Smith et al. 2020" in text
    assert "Do not claim statistical independence" in text

    # Quantitative core remains the already-tested boundary theory.
    assert "k-1-r" in text
    assert "Gamma*=max(rho_hat,1/rho_hat)" in text
    assert "rho_F rho_E=rho_W" in text
    assert "Design Rule 1" in text
    assert "Design Rule 2" in text

    # Cross-domain motivation and scope limits remain explicit.
    assert "Schupp, Jordano & Gómez 2010" in text
    assert "community `sum_m V_mE_m` adds aggregation ambiguity" in text
    assert "The paper does not require RACH/NOV/G2" in text


def test_claim_escalation_rule_prevents_perspective_scope_creep():
    text = (ROOT / "paper" / "boundary_claim_evidence_matrix.md").read_text(encoding="utf-8")
    assert "Claim escalation stop rule" in text
    assert "directly supported by the literature audit" in text
    assert "an exact theorem under an explicitly stated observation map" in text
    assert "Perspective-level proposal rather than an established universal fact" in text
