"""Final deterministic manuscript polish after all frozen validation runs.

No model, seed, threshold, or result is recomputed here. The script only inserts
already-frozen validation values, removes stale future-tense text, and makes the
Main figure numbering consecutive.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "mee_manuscript_draft.md"
G2_SUMMARY = ROOT / "paper" / "results" / "g2_frozen_v2_summary.json"
VALIDATION_SUMMARY = ROOT / "paper" / "results" / "submission_validation_summary.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if not G2_SUMMARY.exists() or not VALIDATION_SUMMARY.exists():
        raise RuntimeError("frozen result summaries are missing")

    text = MANUSCRIPT.read_text(encoding="utf-8")

    known_truth_anchor = (
        "supported. This tests self-consistency or misspecification robustness, not\n"
        "real-world causation. Confounded switches are deliberately not expected to become\n"
        "uniquely recoverable from a non-identifying pattern."
    )
    known_truth_new = known_truth_anchor + (
        " Under the unchanged submission defaults\n"
        "(200 draws per case, proxy→proxy, seed 42), the zero-noise stratum had mean\n"
        "switch-state accuracy 0.6562 while recall of applicable true-ON switches was\n"
        "1.000. Recall remained 1.000 in the 0.1 and 0.2 pattern-noise strata. This is\n"
        "the intended recovery signature for a non-identifying benchmark: the generating\n"
        "switches remain admissible while additional confounded explanations are not\n"
        "artificially forced away. Full frozen values and execution provenance are in\n"
        "`paper/results/submission_validation_summary.json`."
    )
    if "zero-noise stratum had mean" not in text:
        text = replace_once(text, known_truth_anchor, known_truth_new, "known-truth insertion")

    text = replace_once(
        text,
        "### 4.2 Model selection misleads; RACH exposes the confound (Fig. 2)",
        "### 4.2 Model selection misleads; RACH exposes the confound (Fig. 1)",
        "Figure 1 renumber",
    )
    text = replace_once(
        text,
        "### 4.3 Generality and observation-budget error control (Fig. 3)",
        "### 4.3 Generality and observation-budget error control (Fig. 2)",
        "Figure 2 renumber",
    )
    text = replace_once(
        text,
        "### 4.4 NOV information identity and calibration (Fig. 4)",
        "### 4.4 NOV information identity and calibration (Fig. 3)",
        "Figure 3 renumber",
    )

    text = replace_once(
        text,
        "Every row is tagged with the SHA-256 hash of the exact v2 protocol, and\n"
        "numerical values will be inserted here only from those tagged outputs. The pre-fix\n"
        "99.2%/98.5% values are not submission evidence.",
        "Every row is tagged with the SHA-256 hash of the exact v2 protocol and the clean\n"
        "execution commit. The numerical values above come only from those tagged frozen\n"
        "outputs. The pre-fix 99.2%/98.5% values are not submission evidence.",
        "G2 provenance tense",
    )

    nov_anchor = (
        "computational conditioning shortcut and empirical calibration."
    )
    nov_new = nov_anchor + (
        " In the unchanged submission-default rerun\n"
        "(1,000 draws, seed 7), the initial admissible region contained 597 draws\n"
        "(`R_RACH=0.1071`). Stored-region filtering and fresh deterministic re-inference\n"
        "gave identical resolvability gains for all six directly checked quantitative\n"
        "observations (maximum absolute difference 0). Across eight candidate observations\n"
        "and four controlled truths per observation, predictive EVSI correlated positively\n"
        "with mean realised resolvability gain (`r=0.7664`; mean absolute EVSI-minus-mean-\n"
        "realised difference 0.0739). These calibration values are descriptive checks, not\n"
        "performance gates, and are frozen in\n"
        "`paper/results/submission_validation_summary.json`."
    )
    if "maximum absolute difference 0" not in text:
        text = replace_once(text, nov_anchor, nov_new, "NOV calibration insertion")

    # Keep all Main figure references consecutive; S1 remains supplementary.
    if "Fig. 4" in text or "### 4.2 Model selection misleads; RACH exposes the confound (Fig. 2)" in text:
        raise RuntimeError("stale Main figure numbering remains")

    MANUSCRIPT.write_text(text, encoding="utf-8")
    print("final manuscript polish complete")


if __name__ == "__main__":
    main()
