"""Audit the built Mechanism-Resolving Observation Design wheel."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

FORBIDDEN_PREFIXES = ("apps/", "paper/", "tests/", "examples/", "scripts/", "docs/", "outputs/")
ALLOWED_PACKAGE_PREFIXES = (
    "mechanism_resolution_design/",
    "causal_model/",
    "attraction_trait_model/",
)


def audit_wheel(wheel: Path) -> dict:
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    with zipfile.ZipFile(wheel) as zf:
        members = sorted(zf.namelist())
    forbidden = [
        name
        for name in members
        if name.startswith(FORBIDDEN_PREFIXES)
        or "__pycache__" in name
        or name.endswith((".pyc", ".pyo"))
    ]
    if forbidden:
        raise RuntimeError("forbidden wheel members:\n- " + "\n- ".join(forbidden))
    dist_info = [name for name in members if ".dist-info/" in name]
    package_members = [name for name in members if name.startswith(ALLOWED_PACKAGE_PREFIXES)]
    unexpected = [
        name
        for name in members
        if not name.startswith(ALLOWED_PACKAGE_PREFIXES) and ".dist-info/" not in name
    ]
    if unexpected:
        raise RuntimeError("unexpected top-level wheel members:\n- " + "\n- ".join(unexpected))
    if "mechanism_resolution_design/__init__.py" not in members:
        raise RuntimeError("official mechanism_resolution_design package missing from wheel")
    if "causal_model/__init__.py" not in members:
        raise RuntimeError("internal compatibility implementation package missing from wheel")
    if not dist_info or not package_members:
        raise RuntimeError("wheel is missing package or dist-info members")
    top_levels = sorted({name.split("/", 1)[0] for name in members if "/" in name})
    return {
        "wheel": wheel.name,
        "sha256": digest,
        "member_count": len(members),
        "top_levels": top_levels,
        "forbidden_member_count": 0,
        "method_name": "Mechanism-Resolving Observation Design",
        "distribution": "mechanism-resolution-design",
        "public_namespace": "mechanism_resolution_design",
        "publication_api_note": (
            "mechanism_resolution_design is the official public namespace; causal_model "
            "is retained as an internal compatibility/implementation package and "
            "attraction_trait_model is an optional simulator backend. Paper workspace, "
            "tests, examples, scripts, docs and outputs are excluded."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit the mechanism-resolution-design wheel")
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--output", default="outputs/g5/wheel_audit.json")
    args = parser.parse_args(argv)
    wheels = sorted(Path(args.dist_dir).glob("mechanism_resolution_design-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"expected exactly one mechanism-resolution-design wheel, found {len(wheels)}"
        )
    result = audit_wheel(wheels[0])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
