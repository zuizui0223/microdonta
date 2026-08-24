"""Fail when independently publishable programs become entangled again."""
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


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    for name, program in registry["programs"].items():
        for relative in program["roots"]:
            if not (ROOT / relative).exists():
                errors.append(f"{name}: missing registered root {relative}")

    expected_packages = set(registry["rach_distribution_packages"])
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
    actual_packages = set(re.findall(r'["\']([^"\']+)["\']', package_match.group(1)))
    if actual_packages != expected_packages:
        errors.append(
            "RACH wheel package boundary changed: "
            f"expected {sorted(expected_packages)}, got {sorted(actual_packages)}"
        )

    separate_modules = registry["separate_module_names"]
    stale_paths = [
        ROOT / "causal_model" / f"{module}.py" for module in separate_modules
    ]
    errors.extend(
        f"separate module remains in causal_model: {path.relative_to(ROOT)}"
        for path in stale_paths
        if path.exists()
    )

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

    legacy_tokens = [
        *(f"causal_model.{module}" for module in separate_modules),
        "streamlit run streamlit_app.py",
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
    print("separate program: eco_genetic_criticality")


if __name__ == "__main__":
    main()
