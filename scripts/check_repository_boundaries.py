"""Fail when repository ownership or programme boundaries drift."""
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

    state_path = ROOT / "examples/island_pollination_empirical_tracks/CURRENT_STATE.json"
    empirical_state = json.loads(state_path.read_text(encoding="utf-8"))
    programme = registry["programs"]["island_pollination_empirical_tracks"]
    expected_tracks = programme["track_ids"]
    actual_tracks = [row["track_id"] for row in empirical_state["tracks"]]
    if actual_tracks != expected_tracks:
        errors.append(
            "island empirical tracks changed: "
            f"expected {expected_tracks}, got {actual_tracks}"
        )
    if empirical_state.get("external_manuscript_dependency") is not False:
        errors.append("island empirical programme acquired an external manuscript dependency")
    if empirical_state.get("external_repository_dependency") is not False:
        errors.append("island empirical programme acquired an external repository dependency")
    if programme.get("external_manuscript_dependency") is not False:
        errors.append("registry marks island empirical programme as manuscript-dependent")
    if programme.get("external_repository_dependency") is not False:
        errors.append("registry marks island empirical programme as repository-dependent")

    old_root = ROOT / "examples/island_pollination_translation"
    if old_root.exists():
        errors.append("legacy izu-core translation bridge remains in current tree")

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

    stale_tokens = [
        "streamlit run streamlit_app.py",
        "`eco_genetic_criticality/`",
        "`docs/eco_genetic_criticality/`",
        "`examples/eco_genetic_criticality/`",
        "`tests/eco_genetic_criticality/`",
        "island_pollination_translation",
        "three izu-core adapters",
        "izu-core-to-RACH adapter",
        "merged izu-core bridge",
    ]
    for path in current_text_files():
        text = path.read_text(encoding="utf-8")
        for token in stale_tokens:
            if token in text:
                errors.append(f"stale active reference in {path.relative_to(ROOT)}: {token}")

    if errors:
        raise SystemExit("repository boundary check failed:\n- " + "\n- ".join(errors))

    print("repository program boundaries OK")
    print("RACH distribution: " + ", ".join(sorted(actual_packages)))
    print("standalone island empirical tracks: " + ", ".join(actual_tracks))
    print("portfolio repositories: 23")


if __name__ == "__main__":
    main()
