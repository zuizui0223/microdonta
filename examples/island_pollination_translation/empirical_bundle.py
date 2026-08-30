"""Evidence-aware audit for the three izu-core -> RACH empirical tracks.

The translation registry declares which gate names must be present. This module
adds the evidence contract needed for real data. A gate counts as observed only
when its evidence kind is allowed, its comparison unit is declared, provenance
is traceable, derived quantities have valid inputs, and proxies satisfy the
N3/N4 calibration boundary.

Passing this audit closes the declared measurement contract. It does not by
itself establish the ecological causal claim; effect estimation and the declared
RACH admissible-family analysis remain separate steps.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .translation_tracks import audit_track, default_translation_tracks


SCHEMA_VERSION = "1.0"
EVIDENCE_KINDS = frozenset(
    {
        "direct_measurement",
        "prespecified_definition",
        "derived_estimand",
        "calibrated_proxy",
    }
)
EVIDENCE_STATUSES = frozenset({"present", "missing"})
CALIBRATION_STATUSES = frozenset({"stable", "calibrated", "unverified"})


@dataclass(frozen=True)
class Provenance:
    """Traceable source identifier and a locator inside that source."""

    source_id: str
    locator: str


@dataclass(frozen=True)
class CalibrationEvidence:
    """Evidence that a proxy-to-channel map is stable or calibrated."""

    status: str
    scope: str
    provenance: Provenance | None


@dataclass(frozen=True)
class EvidenceRecord:
    """One declared piece of evidence for a structural completion gate."""

    evidence_id: str
    gate: str
    status: str
    evidence_kind: str
    description: str
    unit: str | None
    comparison_unit: str | None
    method: str | None
    uncertainty: str | None
    provenance: Provenance | None
    formula: str | None
    derived_from: tuple[str, ...]
    frozen_before_outcome: bool
    proxy_target: str | None
    calibration: CalibrationEvidence | None


@dataclass(frozen=True)
class EmpiricalObservationBundle:
    """A candidate real-system observation package for one translation track."""

    schema_version: str
    bundle_id: str
    track_id: str
    system_id: str
    comparison_unit: str
    compatible_comparison_units: tuple[str, ...]
    independent_system: bool | None
    evidence: tuple[EvidenceRecord, ...]
    notes: str = ""


@dataclass(frozen=True)
class EvidenceDiagnostic:
    """Audit result for one evidence record."""

    evidence_id: str
    gate: str
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EmpiricalBundleAssessment:
    """Machine-readable assessment of measurement-contract readiness."""

    bundle_id: str
    track_id: str
    schema_valid: bool
    measurement_contract_ready: bool
    passed_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]
    auxiliary_gates: tuple[str, ...]
    accepted_evidence_ids: tuple[str, ...]
    rejected_evidence_ids: tuple[str, ...]
    schema_errors: tuple[str, ...]
    diagnostics: tuple[EvidenceDiagnostic, ...]
    permitted_conclusion: str
    prohibited_conclusion: str

    @property
    def ready(self) -> bool:
        """Backward-friendly alias for measurement-contract readiness."""

        return self.measurement_contract_ready


class BundleFormatError(ValueError):
    """Raised when JSON cannot be parsed into the declared bundle schema."""


_TRACKS = {track.track_id: track for track in default_translation_tracks()}

_ALLOWED_KINDS_BY_GATE: dict[str, frozenset[str]] = {
    "predeclared_plant_matching_trait": frozenset(
        {"direct_measurement", "calibrated_proxy"}
    ),
    "source_native_pollinator_functional_center": frozenset(
        {"direct_measurement", "derived_estimand", "calibrated_proxy"}
    ),
    "matched_trait_units_and_comparison_unit": frozenset(
        {"prespecified_definition"}
    ),
    "outcome_blind_signed_position_formula": frozenset(
        {"prespecified_definition"}
    ),
    "downstream_reproductive_or_evolutionary_response": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "matched_transition_or_context_unit": frozenset({"prespecified_definition"}),
    "repeated_local_context_support": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "visitor_specific_rate": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "visitor_specific_direct_effectiveness": frozenset(
        {"direct_measurement", "derived_estimand", "calibrated_proxy"}
    ),
    "downstream_reproductive_outcome": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "pollinator_functional_change": frozenset(
        {"direct_measurement", "derived_estimand", "calibrated_proxy"}
    ),
    "effective_service_or_direct_pollen_function": frozenset(
        {"direct_measurement", "derived_estimand", "calibrated_proxy"}
    ),
    "reproductive_dependency_or_autonomous_assurance": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "downstream_floral_reproductive_or_evolutionary_response": frozenset(
        {"direct_measurement", "derived_estimand"}
    ),
    "compatible_unit_linkage": frozenset({"prespecified_definition"}),
    "sampling_hierarchy_and_uncertainty": frozenset(
        {"prespecified_definition"}
    ),
    "source_provenance": frozenset({"prespecified_definition"}),
}

_OUTCOME_BLIND_GATES = frozenset(
    {
        "predeclared_plant_matching_trait",
        "matched_trait_units_and_comparison_unit",
        "outcome_blind_signed_position_formula",
        "matched_transition_or_context_unit",
        "compatible_unit_linkage",
        "sampling_hierarchy_and_uncertainty",
    }
)
_FORMULA_REQUIRED_GATES = frozenset({"outcome_blind_signed_position_formula"})
_PLACEHOLDER_MARKERS = ("replace-with", "todo", "tbd", "placeholder")


def _text(value: Any, *, default: str = "") -> str:
    return value.strip() if isinstance(value, str) else default


def _optional_text(value: Any) -> str | None:
    result = _text(value)
    return result or None


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return False
    lowered = value.strip().lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _parse_provenance(value: Any, *, field: str) -> Provenance | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise BundleFormatError(f"{field} must be an object")
    return Provenance(
        source_id=_text(value.get("source_id")),
        locator=_text(value.get("locator")),
    )


def _parse_calibration(value: Any, *, field: str) -> CalibrationEvidence | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise BundleFormatError(f"{field} must be an object")
    status = _text(value.get("status"))
    if status not in CALIBRATION_STATUSES:
        raise BundleFormatError(
            f"{field}.status must be one of {sorted(CALIBRATION_STATUSES)}"
        )
    return CalibrationEvidence(
        status=status,
        scope=_text(value.get("scope")),
        provenance=_parse_provenance(
            value.get("provenance"), field=f"{field}.provenance"
        ),
    )


def _parse_evidence(value: Any, *, index: int) -> EvidenceRecord:
    field = f"evidence[{index}]"
    if not isinstance(value, Mapping):
        raise BundleFormatError(f"{field} must be an object")

    status = _text(value.get("status"))
    if status not in EVIDENCE_STATUSES:
        raise BundleFormatError(
            f"{field}.status must be one of {sorted(EVIDENCE_STATUSES)}"
        )
    kind = _text(value.get("evidence_kind"))
    if kind not in EVIDENCE_KINDS:
        raise BundleFormatError(
            f"{field}.evidence_kind must be one of {sorted(EVIDENCE_KINDS)}"
        )

    derived_from = value.get("derived_from", ())
    if not isinstance(derived_from, Sequence) or isinstance(
        derived_from, (str, bytes)
    ):
        raise BundleFormatError(
            f"{field}.derived_from must be an array of evidence IDs"
        )
    if not all(isinstance(item, str) for item in derived_from):
        raise BundleFormatError(f"{field}.derived_from must contain strings only")

    frozen = value.get("frozen_before_outcome", False)
    if not isinstance(frozen, bool):
        raise BundleFormatError(f"{field}.frozen_before_outcome must be boolean")

    return EvidenceRecord(
        evidence_id=_text(value.get("evidence_id")),
        gate=_text(value.get("gate")),
        status=status,
        evidence_kind=kind,
        description=_text(value.get("description")),
        unit=_optional_text(value.get("unit")),
        comparison_unit=_optional_text(value.get("comparison_unit")),
        method=_optional_text(value.get("method")),
        uncertainty=_optional_text(value.get("uncertainty")),
        provenance=_parse_provenance(
            value.get("provenance"), field=f"{field}.provenance"
        ),
        formula=_optional_text(value.get("formula")),
        derived_from=tuple(item.strip() for item in derived_from if item.strip()),
        frozen_before_outcome=frozen,
        proxy_target=_optional_text(value.get("proxy_target")),
        calibration=_parse_calibration(
            value.get("calibration"), field=f"{field}.calibration"
        ),
    )


def load_empirical_bundle(
    source: str | Path | Mapping[str, Any],
) -> EmpiricalObservationBundle:
    """Load a bundle from a JSON file or an already parsed mapping."""

    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise BundleFormatError(f"cannot read bundle {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise BundleFormatError(f"invalid JSON in {path}: {exc}") from exc
    else:
        data = source

    if not isinstance(data, Mapping):
        raise BundleFormatError("bundle root must be an object")

    evidence_data = data.get("evidence")
    if not isinstance(evidence_data, Sequence) or isinstance(
        evidence_data, (str, bytes)
    ):
        raise BundleFormatError("evidence must be an array")

    compatible = data.get("compatible_comparison_units", ())
    if not isinstance(compatible, Sequence) or isinstance(compatible, (str, bytes)):
        raise BundleFormatError("compatible_comparison_units must be an array")
    if not all(isinstance(item, str) for item in compatible):
        raise BundleFormatError(
            "compatible_comparison_units must contain strings only"
        )

    independent = data.get("independent_system")
    if independent is not None and not isinstance(independent, bool):
        raise BundleFormatError("independent_system must be boolean or null")

    return EmpiricalObservationBundle(
        schema_version=_text(data.get("schema_version")),
        bundle_id=_text(data.get("bundle_id")),
        track_id=_text(data.get("track_id")),
        system_id=_text(data.get("system_id")),
        comparison_unit=_text(data.get("comparison_unit")),
        compatible_comparison_units=tuple(
            item.strip() for item in compatible if item.strip()
        ),
        independent_system=independent,
        evidence=tuple(
            _parse_evidence(record, index=index)
            for index, record in enumerate(evidence_data)
        ),
        notes=_text(data.get("notes")),
    )


def _valid_provenance(provenance: Provenance | None) -> bool:
    return bool(
        provenance
        and provenance.source_id
        and provenance.locator
        and not _is_placeholder(provenance.source_id)
        and not _is_placeholder(provenance.locator)
    )


def _base_reasons(
    record: EvidenceRecord,
    *,
    allowed_comparison_units: frozenset[str],
    duplicate_ids: frozenset[str],
) -> list[str]:
    reasons: list[str] = []
    if not record.evidence_id:
        reasons.append("missing evidence_id")
    elif record.evidence_id in duplicate_ids:
        reasons.append("duplicate evidence_id")
    if not record.gate:
        reasons.append("missing gate")
    if record.status == "missing":
        reasons.append("declared missing")
        return reasons

    allowed_kinds = _ALLOWED_KINDS_BY_GATE.get(record.gate, EVIDENCE_KINDS)
    if record.evidence_kind not in allowed_kinds:
        reasons.append(
            f"evidence kind {record.evidence_kind!r} is not allowed for "
            f"gate {record.gate!r}"
        )
    if not record.description or _is_placeholder(record.description):
        reasons.append("present evidence requires a non-placeholder description")
    if (
        not record.comparison_unit
        or _is_placeholder(record.comparison_unit)
        or record.comparison_unit not in allowed_comparison_units
    ):
        reasons.append(
            "comparison_unit is missing or outside the declared compatible units"
        )
    if not _valid_provenance(record.provenance):
        reasons.append("present evidence requires traceable provenance")
    if record.gate in _OUTCOME_BLIND_GATES and not record.frozen_before_outcome:
        reasons.append("gate must be frozen before outcome inspection")

    if record.evidence_kind in {
        "direct_measurement",
        "derived_estimand",
        "calibrated_proxy",
    }:
        if not record.unit or _is_placeholder(record.unit):
            reasons.append("measurement evidence requires a non-placeholder unit")
        if not record.method or _is_placeholder(record.method):
            reasons.append("measurement evidence requires a non-placeholder method")

    if record.evidence_kind == "prespecified_definition":
        if record.gate in _FORMULA_REQUIRED_GATES and (
            not record.formula or _is_placeholder(record.formula)
        ):
            reasons.append("this prespecified gate requires an explicit formula")

    if record.evidence_kind == "derived_estimand":
        if not record.formula or _is_placeholder(record.formula):
            reasons.append("derived_estimand requires an explicit formula")
        if not record.derived_from:
            reasons.append("derived_estimand requires derived_from evidence IDs")

    if record.evidence_kind == "calibrated_proxy":
        if not record.proxy_target or _is_placeholder(record.proxy_target):
            reasons.append("calibrated_proxy requires a declared proxy_target")
        calibration = record.calibration
        if calibration is None:
            reasons.append("calibrated_proxy requires calibration evidence")
        else:
            if calibration.status not in {"stable", "calibrated"}:
                reasons.append(
                    "proxy calibration is unverified; N3/N4 does not permit "
                    "channel substitution"
                )
            if not calibration.scope or _is_placeholder(calibration.scope):
                reasons.append("proxy calibration requires a declared comparison scope")
            if not _valid_provenance(calibration.provenance):
                reasons.append("proxy calibration requires traceable provenance")
    return reasons


def audit_empirical_bundle(
    bundle: EmpiricalObservationBundle,
) -> EmpiricalBundleAssessment:
    """Audit whether a real-system bundle closes every required evidence gate."""

    schema_errors: list[str] = []
    if bundle.schema_version != SCHEMA_VERSION:
        schema_errors.append(
            f"schema_version must be {SCHEMA_VERSION!r}, "
            f"got {bundle.schema_version!r}"
        )
    for name, value in (
        ("bundle_id", bundle.bundle_id),
        ("track_id", bundle.track_id),
        ("system_id", bundle.system_id),
        ("comparison_unit", bundle.comparison_unit),
    ):
        if not value or _is_placeholder(value):
            schema_errors.append(f"{name} must be nonempty and non-placeholder")

    track = _TRACKS.get(bundle.track_id)
    if track is None:
        schema_errors.append(f"unknown translation track: {bundle.track_id!r}")
    if (
        bundle.track_id == "complete_service_dependency_response_bridge"
        and bundle.independent_system is not True
    ):
        schema_errors.append(
            "complete bridge requires independent_system=true for a non-Izu "
            "validation system"
        )

    ids = [record.evidence_id for record in bundle.evidence if record.evidence_id]
    duplicate_ids = frozenset(
        evidence_id for evidence_id, count in Counter(ids).items() if count > 1
    )
    if duplicate_ids:
        schema_errors.append(
            "duplicate evidence IDs: " + ", ".join(sorted(duplicate_ids))
        )

    allowed_units = frozenset(
        {bundle.comparison_unit, *bundle.compatible_comparison_units}
    )
    records_by_id = {
        record.evidence_id: record
        for record in bundle.evidence
        if record.evidence_id and record.evidence_id not in duplicate_ids
    }
    base_reason_map = {
        id(record): _base_reasons(
            record,
            allowed_comparison_units=allowed_units,
            duplicate_ids=duplicate_ids,
        )
        for record in bundle.evidence
    }
    resolution_cache: dict[str, tuple[bool, tuple[str, ...]]] = {}

    def resolve(
        record: EvidenceRecord, stack: tuple[str, ...] = ()
    ) -> tuple[bool, tuple[str, ...]]:
        if record.evidence_id and record.evidence_id in resolution_cache:
            return resolution_cache[record.evidence_id]
        reasons = list(base_reason_map[id(record)])
        if record.evidence_kind == "derived_estimand" and record.status == "present":
            if record.evidence_id in stack:
                reasons.append("cyclic derived_from dependency")
            else:
                for dependency_id in record.derived_from:
                    dependency = records_by_id.get(dependency_id)
                    if dependency is None:
                        reasons.append(
                            f"derived_from references missing evidence "
                            f"{dependency_id!r}"
                        )
                        continue
                    accepted, dependency_reasons = resolve(
                        dependency, (*stack, record.evidence_id)
                    )
                    if not accepted:
                        reasons.append(
                            f"derived_from evidence {dependency_id!r} is not accepted"
                        )
                        if dependency_reasons:
                            reasons.append(
                                f"dependency {dependency_id!r}: "
                                f"{dependency_reasons[0]}"
                            )
        result = (not reasons, tuple(dict.fromkeys(reasons)))
        if record.evidence_id:
            resolution_cache[record.evidence_id] = result
        return result

    diagnostics: list[EvidenceDiagnostic] = []
    accepted_ids: list[str] = []
    rejected_ids: list[str] = []
    accepted_gates: set[str] = set()
    auxiliary_gates: set[str] = set()
    required_gates = frozenset(track.required_gates) if track else frozenset()

    for index, record in enumerate(bundle.evidence):
        accepted, reasons = resolve(record)
        display_id = record.evidence_id or f"<evidence[{index}]>"
        diagnostics.append(
            EvidenceDiagnostic(display_id, record.gate, accepted, reasons)
        )
        if accepted:
            accepted_ids.append(display_id)
            if record.gate in required_gates:
                accepted_gates.add(record.gate)
            elif record.gate:
                auxiliary_gates.add(record.gate)
        else:
            rejected_ids.append(display_id)

    if track is None:
        track_assessment = None
        passed_gates: tuple[str, ...] = ()
        missing_gates: tuple[str, ...] = ()
        permitted = "Fix the bundle schema before interpreting empirical readiness."
        prohibited = (
            "Do not infer empirical closure from an invalid or unknown track bundle."
        )
    else:
        track_assessment = audit_track(bundle.track_id, accepted_gates)
        passed_gates = track_assessment.passed_gates
        missing_gates = track_assessment.missing_gates
        permitted = track_assessment.permitted_conclusion
        prohibited = (
            track_assessment.prohibited_conclusion
            + " Passing this evidence audit closes the measurement contract only; "
            "it does not by itself establish the ecological causal effect."
        )

    schema_valid = not schema_errors
    measurement_contract_ready = bool(
        schema_valid and track_assessment and track_assessment.ready
    )
    return EmpiricalBundleAssessment(
        bundle_id=bundle.bundle_id,
        track_id=bundle.track_id,
        schema_valid=schema_valid,
        measurement_contract_ready=measurement_contract_ready,
        passed_gates=passed_gates,
        missing_gates=missing_gates,
        auxiliary_gates=tuple(sorted(auxiliary_gates)),
        accepted_evidence_ids=tuple(accepted_ids),
        rejected_evidence_ids=tuple(rejected_ids),
        schema_errors=tuple(schema_errors),
        diagnostics=tuple(diagnostics),
        permitted_conclusion=permitted,
        prohibited_conclusion=prohibited,
    )


def audit_bundle_file(path: str | Path) -> EmpiricalBundleAssessment:
    """Load and audit one JSON bundle."""

    return audit_empirical_bundle(load_empirical_bundle(path))


def assessment_to_dict(assessment: EmpiricalBundleAssessment) -> dict[str, Any]:
    """Convert an assessment to JSON-safe primitives."""

    return asdict(assessment)


def _template_kind(gate: str) -> str:
    allowed = _ALLOWED_KINDS_BY_GATE.get(gate, EVIDENCE_KINDS)
    for preferred in (
        "prespecified_definition",
        "direct_measurement",
        "derived_estimand",
        "calibrated_proxy",
    ):
        if preferred in allowed:
            return preferred
    raise RuntimeError(f"no template kind for gate {gate!r}")


def bundle_template(track_id: str) -> dict[str, Any]:
    """Return an explicitly incomplete JSON template for one track."""

    try:
        track = _TRACKS[track_id]
    except KeyError as exc:
        raise ValueError(f"unknown translation track: {track_id}") from exc

    comparison_unit = "replace-with-comparison-unit"
    evidence: list[dict[str, Any]] = []
    for index, gate in enumerate(track.required_gates, start=1):
        kind = _template_kind(gate)
        record: dict[str, Any] = {
            "evidence_id": f"gate-{index:02d}-{gate}",
            "gate": gate,
            "status": "missing",
            "evidence_kind": kind,
            "description": f"Supply evidence for {gate}",
            "comparison_unit": comparison_unit,
            "frozen_before_outcome": gate in _OUTCOME_BLIND_GATES,
        }
        if kind in {"direct_measurement", "derived_estimand", "calibrated_proxy"}:
            record.update(
                {
                    "unit": "replace-with-measurement-unit",
                    "method": "replace-with-measurement-method",
                }
            )
        if kind == "derived_estimand":
            record.update(
                {
                    "formula": "replace-with-formula",
                    "derived_from": ["replace-with-evidence-id"],
                }
            )
        if gate in _FORMULA_REQUIRED_GATES:
            record["formula"] = (
                "plant_matching_trait - pollinator_functional_center"
            )
        if kind == "calibrated_proxy":
            record.update(
                {
                    "proxy_target": gate,
                    "calibration": {
                        "status": "unverified",
                        "scope": "replace-with-comparison-scope",
                        "provenance": {
                            "source_id": "replace-with-source-id",
                            "locator": "replace-with-source-locator",
                        },
                    },
                }
            )
        evidence.append(record)

    return {
        "schema_version": SCHEMA_VERSION,
        "bundle_id": f"replace-with-{track_id}-bundle-id",
        "track_id": track_id,
        "system_id": "replace-with-real-system-id",
        "comparison_unit": comparison_unit,
        "compatible_comparison_units": [],
        "independent_system": (
            False
            if track_id == "complete_service_dependency_response_bridge"
            else None
        ),
        "evidence": evidence,
        "notes": (
            "Template only. Change status to present only after replacing every "
            "placeholder and supplying traceable provenance."
        ),
    }


__all__ = [
    "BundleFormatError",
    "CalibrationEvidence",
    "EmpiricalBundleAssessment",
    "EmpiricalObservationBundle",
    "EvidenceDiagnostic",
    "EvidenceRecord",
    "Provenance",
    "SCHEMA_VERSION",
    "assessment_to_dict",
    "audit_bundle_file",
    "audit_empirical_bundle",
    "bundle_template",
    "load_empirical_bundle",
]
