"""Fail when repository ownership or adapter boundaries drift."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "repository_programs.json"
PYPROJECT_PATH = ROOT / "pyproject.toml"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def current_text_files() -> list[Path]:
    roots = [ROOT / "README.md", ROOT / "docs", ROOT / "paper", ROOT / ".github"]
    files: list[Path] = []
    for item in roots:
        if item.is_file():
            files.append(item)
            continue
        files.extend(
            path
            for path in item.rglob("*")
            if path.is_file()
            and path.suffix in {".md", ".json", ".yml", ".yaml"}
            and "archive" not in path.parts
        )
    return files


def parse_distribution_packages() -> set[str]:
    pyproject_text = PYPROJECT_PATH.read_text(encoding="utf-8")
    setuptools_block = re.search(
        r"\[tool\.setuptools\](.*?)(?:\n\[|\Z)", pyproject_text, flags=re.DOTALL
    )
    package_match = (
        re.search(r"packages\s*=\s*\[(.*?)\]", setuptools_block.group(1), flags=re.DOTALL)
        if setuptools_block
        else None
    )
    if not package_match:
        raise SystemExit("repository boundary check failed:\n- cannot parse tool.setuptools packages")
    return set(re.findall(r'["\']([^"\']+)["\']', package_match.group(1)))


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    for name, program in registry["programs"].items():
        for relative in program["roots"]:
            if not (ROOT / relative).exists():
                errors.append(f"{name}: missing registered root {relative}")

    expected_packages = set(registry["rach_distribution_packages"])
    actual_packages = parse_distribution_packages()
    if actual_packages != expected_packages:
        errors.append(
            "RACH wheel package boundary changed: "
            f"expected {sorted(expected_packages)}, got {sorted(actual_packages)}"
        )

    for name, external in registry["external_programs"].items():
        for relative in external["forbidden_roots"]:
            if (ROOT / relative).exists():
                errors.append(f"external program copied locally ({name}): {relative}")
        for module in external["forbidden_module_names"]:
            stale = ROOT / "causal_model" / f"{module}.py"
            if stale.exists():
                errors.append(f"external module remains in causal_model: {stale.relative_to(ROOT)}")

    if (ROOT / "streamlit_app.py").exists():
        errors.append("interactive app returned to the repository root")

    for rule in registry["forbidden_imports"]:
        source_root = ROOT / rule["from_root"]
        target = rule["to_module"]
        for path in source_root.rglob("*.py"):
            for module in imported_modules(path):
                if module == target or module.startswith(target + "."):
                    errors.append(
                        f"forbidden dependency {path.relative_to(ROOT)} -> {module}"
                    )

    translation_state = json.loads(
        (ROOT / "examples/island_pollination_translation/CURRENT_STATE.json").read_text(
            encoding="utf-8"
        )
    )
    expected_tracks = registry["programs"]["island_pollination_translation"]["track_ids"]
    actual_tracks = [row["track_id"] for row in translation_state["tracks"]]
    if actual_tracks != expected_tracks:
        errors.append(
            "island translation tracks changed: "
            f"expected {expected_tracks}, got {actual_tracks}"
        )
    if any(row["izu_core_submission_blocker"] for row in translation_state["tracks"]):
        errors.append("an adapter was silently promoted to an izu-core submission blocker")

    portfolio_path = ROOT / registry["portfolio_registry"]
    portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    expected_repositories = {
        "hotarubukuro", "azami", "bita", "island", "microdonta", "pollipi",
        "insepi", "acsp", "eco-genetic-criticality", "ccoc", "izu-core",
        "eco-genetic-warning-extensions", "mltr", "ced", "mrm",
        "shimahotarubukuro", "fcp", "eog", "odsp", "EAzami", "chun",
        "sdmr", "crest"
    }
    listed = [entry["name"] for entry in portfolio["repositories"]]
    if len(listed) != len(set(listed)):
        errors.append("portfolio registry contains duplicate repository names")
    if set(listed) != expected_repositories:
        errors.append(
            "portfolio registry drift: "
            f"missing={sorted(expected_repositories - set(listed))}, "
            f"extra={sorted(set(listed) - expected_repositories)}"
        )

    legacy_tokens = [
        "streamlit run streamlit_app.py",
        "`eco_genetic_criticality/`",
        "`docs/eco_genetic_criticality/`",
        "`examples/eco_genetic_criticality/`",
        "`tests/eco_genetic_criticality/`",
    ]
    for path in current_text_files():
        text = path.read_text(encoding="utf-8")
        for token in legacy_tokens:
            if token in text:
                errors.append(f"stale active reference in {path.relative_to(ROOT)}: {token}")

    if errors:
        raise SystemExit("repository boundary check failed:\n- " + "\n- ".join(errors))

    print("repository program boundaries OK")
    print("RACH distribution: " + ", ".join(sorted(actual_packages)))
    print("external owner: zuizui0223/eco-genetic-criticality")
    print("portfolio repositories: 23")
    print("izu-core adapters: " + ", ".join(actual_tracks))


if __name__ == "__main__":
    main()
