"""Causal structure schema for latent causal generative models.

General-purpose framework. System-specific default structures belong in
the corresponding examples/ directory (e.g., examples/campanula_izu/).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CausalEdge:
    """Directed causal relation between two named variables."""

    source: str
    target: str
    relation: str = "positive"
    description: str = ""


@dataclass(frozen=True)
class CausalStructure:
    """Candidate causal hypothesis to be tested by generative pattern matching."""

    name: str
    edges: tuple[CausalEdge, ...] = field(default_factory=tuple)
    latent_parameters: tuple[str, ...] = field(default_factory=tuple)
    expected_patterns: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    notes: str = ""
