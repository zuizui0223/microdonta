"""Official public Python namespace for Mechanism-Resolving Observation Design.

The implementation remains in the internal ``causal_model`` package during the
compatibility transition. New users should import only from
``mechanism_resolution_design``.
"""
from __future__ import annotations

import causal_model as _implementation

for _name in _implementation.__all__:
    globals()[_name] = getattr(_implementation, _name)

__all__ = list(_implementation.__all__)
__version__ = "0.1.0"

del _name
