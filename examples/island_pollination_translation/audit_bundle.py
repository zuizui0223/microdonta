"""Command-line interface for empirical translation-bundle audits."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .empirical_bundle import (
    BundleFormatError,
    assessment_to_dict,
    audit_bundle_file,
    bundle_template,
)


def _print_human(assessment) -> None:
    print(f"bundle: {assessment.bundle_id or '<missing>'}")
    print(f"track: {assessment.track_id or '<missing>'}")
    print(f"schema_valid: {str(assessment.schema_valid).lower()}")
    print(
        "measurement_contract_ready: "
        f"{str(assessment.measurement_contract_ready).lower()}"
    )
    if assessment.passed_gates:
        print("passed_gates:")
        for gate in assessment.passed_gates:
            print(f"  - {gate}")
    if assessment.missing_gates:
        print("missing_gates:")
        for gate in assessment.missing_gates:
            print(f"  - {gate}")
    if assessment.schema_errors:
        print("schema_errors:")
        for error in assessment.schema_errors:
            print(f"  - {error}")
    rejected = [row for row in assessment.diagnostics if not row.accepted]
    if rejected:
        print("rejected_evidence:")
        for row in rejected:
            detail = "; ".join(row.reasons) if row.reasons else "rejected"
            print(f"  - {row.evidence_id} [{row.gate}]: {detail}")
    print(f"permitted_conclusion: {assessment.permitted_conclusion}")
    print(f"prohibited_conclusion: {assessment.prohibited_conclusion}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit or generate evidence-aware bundles for the three izu-core -> "
            "RACH empirical translation tracks."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit one empirical bundle JSON")
    audit.add_argument("bundle", type=Path)
    audit.add_argument("--json", action="store_true", help="print JSON")
    audit.add_argument("--output", type=Path, help="write the JSON report")
    audit.add_argument(
        "--require-ready",
        action="store_true",
        help="exit nonzero unless every empirical gate is accepted",
    )

    template = subparsers.add_parser(
        "template", help="write an incomplete bundle template"
    )
    template.add_argument("track_id")
    template.add_argument("output", type=Path)
    template.add_argument(
        "--force", action="store_true", help="replace an existing output file"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "template":
        if args.output.exists() and not args.force:
            print(f"refusing to replace existing file: {args.output}")
            return 2
        try:
            payload = bundle_template(args.track_id)
        except ValueError as exc:
            print(str(exc))
            return 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return 0

    try:
        assessment = audit_bundle_file(args.bundle)
    except BundleFormatError as exc:
        print(f"bundle format error: {exc}")
        return 2

    payload = assessment_to_dict(assessment)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_human(assessment)

    if not assessment.schema_valid:
        return 2
    if args.require_ready and not assessment.measurement_contract_ready:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
