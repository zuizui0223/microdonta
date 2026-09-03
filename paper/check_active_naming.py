"""Guard the active publication surface against retired method branding."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = "Mechanism-Resolving Observation Design"
ACTIVE = [
    ROOT / "README.md",
    ROOT / "CITATION.cff",
    ROOT / ".zenodo.json",
    ROOT / "pyproject.toml",
    ROOT / "paper" / "manuscript.md",
    ROOT / "paper" / "supporting_information.md",
    ROOT / "paper" / "title_page_draft.md",
    ROOT / "paper" / "cover_letter_draft.md",
    ROOT / "paper" / "mee_submission_requirements_2026.md",
    ROOT / "paper" / "README.md",
    ROOT / "paper" / "REPOSITORY_SCOPE.md",
    ROOT / "paper" / "submission_manifest.json",
    ROOT / "paper" / "final_figure_inventory.json",
    ROOT / "docs" / "mainline.md",
    ROOT / "docs" / "tutorial.md",
    ROOT / "docs" / "mechanism_resolution_theory.md",
    ROOT / "docs" / "observation_information_foundations.md",
    ROOT / "causal_model" / "__init__.py",
    ROOT / "causal_model" / "admissible_mechanisms.py",
    ROOT / "causal_model" / "observation_value.py",
    ROOT / "causal_model" / "sequential_design.py",
    ROOT / "causal_model" / "controlled_confounding_demo.py",
]
RETIRED_PATHS = [
    "causal_model/causal_admissibility.py",
    "causal_model/causal_replaceability.py",
    "causal_model/nov_evsi.py",
    "causal_model/nov_calibration.py",
    "causal_model/rach_seq.py",
    "causal_model/rach_set.py",
    "causal_model/replaceability_nov.py",
    "causal_model/confound_demo.py",
    "tests/test_causal_replaceability.py",
    "tests/test_nov_evsi.py",
    "tests/test_nov_calibration.py",
    "tests/test_rach_seq.py",
    "tests/test_rach_seq_nov_selection.py",
    "tests/test_rach_seq_predictive_reweighting.py",
    "tests/test_rach_set.py",
    "tests/test_replaceability_nov.py",
    "tests/test_confound_demo.py",
]


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in ACTIVE if not path.exists()]
    if missing:
        raise SystemExit("active naming surface missing:\n- " + "\n- ".join(missing))

    stale_paths = [path for path in RETIRED_PATHS if (ROOT / path).exists()]
    if stale_paths:
        raise SystemExit("retired backend/test filenames remain:\n- " + "\n- ".join(stale_paths))

    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE)
    if OFFICIAL not in combined:
        raise SystemExit("official method name missing from active surface")

    forbidden = (
        "Restricted Admissible Causal Hypotheses",
        "RACH-SEQ",
        "NOV(Q)",
        "# RACH",
        "RACH: ",
        "(B) RACH",
        "(C) NOV",
        "expected ΔR (NOV)",
        "microdonta: information-theoretic",
        "microdonta's observation-design method",
        "https://github.com/zuizui0223/microdonta",
    )
    problems = []
    for path in ACTIVE:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                problems.append(f"{path.relative_to(ROOT)}: {token}")
    if problems:
        raise SystemExit("retired active method branding remains:\n- " + "\n- ".join(problems))

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    if 'name = "mechanism-resolution-design"' not in pyproject:
        raise SystemExit("distribution name is not mechanism-resolution-design")
    if 'name = "microdonta"' in pyproject or 'name = "rach"' in pyproject:
        raise SystemExit("retired distribution name remains")
    if 'Repository = "https://github.com/zuizui0223/mrod"' not in pyproject:
        raise SystemExit("package repository URL is not the current mrod repository")

    manuscript = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8").casefold()
    for token in ("admissible mechanism region", "observation information value", "sequential observation design"):
        if token.casefold() not in manuscript:
            raise SystemExit(f"active manuscript missing descriptive term: {token}")

    figure_source = (ROOT / "causal_model" / "controlled_confounding_demo.py").read_text(encoding="utf-8")
    for token in (
        "V(Q)=I(S;Q|A_epsilon)/K",
        "six-bin",
        "mechanism-independent nuisance",
        "controlled_confounding_demo",
    ):
        if token not in figure_source:
            raise SystemExit(f"Figure 1 source missing canonical marker: {token}")
    for token in ("next_observation_value(", "heuristic_observation_value"):
        if token in figure_source:
            raise SystemExit(f"Figure 1 source returned to heuristic ranking: {token}")

    inventory = (ROOT / "paper" / "final_figure_inventory.json").read_text(encoding="utf-8")
    if "figure1_controlled_confounding.png" not in inventory:
        raise SystemExit("Figure 1 inventory did not adopt the controlled-confounding filename")
    if "causal_model.controlled_confounding_demo" not in inventory:
        raise SystemExit("Figure 1 inventory did not adopt the canonical generator")

    print("active naming OK")
    print(f"method: {OFFICIAL}")
    print("distribution: mechanism-resolution-design")
    print("repository: zuizui0223/mrod")
    print("retired backend/test/Figure-1 filenames: absent")
    print("Figure 1 information-value source: canonical and non-heuristic")
    print("historical frozen identifiers: permitted only as machine-level provenance")


if __name__ == "__main__":
    main()
