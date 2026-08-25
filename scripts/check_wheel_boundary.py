"""Audit the built ``rach`` wheel against the publication package boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


FORBIDDEN_PREFIXES = (
    "apps/",
    "paper/",
    "tests/",
    "examples/",
    "scripts/",
    "docs/",
    "outputs/",
)
ALLOWED_PACKAGE_PREFIXES = ("causal_model/", "attraction_trait_model/")


def audit_wheel(wheel: Path) -> dict:
    raw = wheel.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(wheel) as zf:
        members = sorted(zf.namelist())

    forbidden = [
        name for name in members
        if name.startswith(FORBIDDEN_PREFIXES)
        or "__pycache__" in name
        or name.endswith((".pyc", ".pyo"))
    ]
    if forbidden:
        raise RuntimeError("forbidden wheel members:\n- " + "\n- ".join(forbidden))

    dist_info = [name for name in members if ".dist-info/" in name]
    package_members = [
        name for name in members if name.startswith(ALLOWED_PACKAGE_PREFIXES)
    ]
    unexpected = [
        name for name in members
        if not name.startswith(ALLOWED_PACKAGE_PREFIXES)
        and ".dist-info/" not in name
    ]
    if unexpected:
        raise RuntimeError("unexpected top-level wheel members:\n- " + "\n- ".join(unexpected))
    if "causal_model/__init__.py" not in members:
        raise RuntimeError("causal_model package missing from wheel")
    if not dist_info or not package_members:
        raise RuntimeError("wheel is missing package or dist-info members")

    top_levels = sorted({name.split("/", 1)[0] for name in members if "/" in name})
    return {
        "wheel": wheel.name,
        "sha256": digest,
        "member_count": len(members),
        "top_levels": top_levels,
        "forbidden_member_count": 0,
        "publication_api_note": (
            "Only causal_model and the optional attraction_trait_model backend are "
            "distributed as packages; apps, paper workspace, tests, examples, scripts, "
            "docs, and outputs are excluded. causal_model.__all__ is separately locked "
            "by tests/test_public_rach_api.py to the primary RACH interface."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a built rach wheel")
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--output", default="outputs/g5/wheel_audit.json")
    args = parser.parse_args(argv)

    wheels = sorted(Path(args.dist_dir).glob("rach-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one rach wheel, found {len(wheels)}")
    result = audit_wheel(wheels[0])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
