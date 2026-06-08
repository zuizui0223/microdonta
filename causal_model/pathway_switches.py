"""Compatibility shim: re-exports PathwaySwitches from causal_model.switches.

The canonical implementation lives in ``causal_model/switches.py``.
This module exists so that code written as::

    from causal_model.pathway_switches import PathwaySwitches, switches_for_structure

continues to work without modification.
"""

from .switches import PathwaySwitches, switches_for_structure, switches_to_dict

__all__ = ["PathwaySwitches", "switches_for_structure", "switches_to_dict"]
