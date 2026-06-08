"""Latent parameter schema for causal generative models.

General-purpose. System-specific latent parameter lists belong in the
corresponding examples/ directory.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LatentParameter:
    """Unobserved or hard-to-measure quantity constrained by pattern matching."""

    name: str
    meaning: str
    lower: float | None = None
    upper: float | None = None
    unit: str = ""
    notes: str = ""
