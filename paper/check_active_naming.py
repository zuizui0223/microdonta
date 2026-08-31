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
    ROOT / "paper" / "README.md",
    ROOT / "paper" / "REPOSITORY_SCOPE.md",
    ROOT / "paper" / "submission_manifest.json",
    ROOT / "docs" / "mainline.md",
    ROOT / "docs" / "mechanism_resolution_theory.md",
    ROOT / "docs" / "observation_information_foundations.md",
    ROOT / "causal_model" / "__init__.py",
    ROOT / "causal_model" / "admissible_mechanisms.py",
    ROOT / "causal_model" / "observation_value.py",
    ROOT / "causal_model" / "sequential_design.py",
]


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in ACTIVE if not path.exists()]
    if missing:
        raise SystemExit("active naming surface missing:\n- " + "\n- ".join(missing))

    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE)
    if OFFICIAL not in combined:
        raise SystemExit("official method name missing from active surface")

    forbidden = (
        "Restricted Admissible Causal Hypotheses",
        "RACH-SEQ",
        "NOV(Q)",
        "# RACH",
        "RACH: ",
        "microdonta: information-theoretic",
        "microdonta's observation-design method",
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

    manuscript = (ROOT / "paper" / "manuscript.md").read_text(encoding="utf-8")
    for token in ("admissible mechanism region", "observation information value", "sequential observation design"):
        if token not in manuscript:
            raise SystemExit(f"active manuscript missing descriptive term: {token}")

    print("active naming OK")
    print(f"method: {OFFICIAL}")
    print("distribution: mechanism-resolution-design")
    print("historical frozen identifiers: permitted only outside active branding surface")


if __name__ == "__main__":
    main()
