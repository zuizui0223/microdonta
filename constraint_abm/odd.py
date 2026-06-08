"""ODD protocol helpers."""

from __future__ import annotations


def render_odd_stub(title: str, purpose: str, entities: list[str], processes: list[str]) -> str:
    """Render a minimal ODD protocol scaffold."""

    entity_lines = "\n".join(f"- {entity}" for entity in entities)
    process_lines = "\n".join(f"- {process}" for process in processes)
    return f"""# {title}

## Overview

### Purpose

{purpose}

### Entities, State Variables, and Scales

{entity_lines}

### Process Overview and Scheduling

{process_lines}

## Design Concepts

To be expanded following the ODD protocol.

## Details

To be expanded with initialization, input data, and submodels.
"""
