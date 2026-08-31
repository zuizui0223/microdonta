"""Publication-facing mechanism-replaceability interface."""
from __future__ import annotations

from . import mechanism_replaceability_core as _backend

ReplaceabilityResult = _backend.CRCResult
mechanism_replaceability_cost = _backend.causal_replaceability_cost
mechanism_replaceability_cost_full = _backend.causal_replaceability_cost_full
mechanism_replaceability_profile = _backend.crc_profile
mechanism_replaceability_profile_full = _backend.crc_profile_full

__all__ = [
    "ReplaceabilityResult",
    "mechanism_replaceability_cost",
    "mechanism_replaceability_cost_full",
    "mechanism_replaceability_profile",
    "mechanism_replaceability_profile_full",
]
