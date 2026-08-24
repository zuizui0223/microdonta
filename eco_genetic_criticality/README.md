# Eco-genetic criticality program

This directory is a physically separate research program retained in the same
repository for continuity. It contains the multipatch dynamics, criticality and
fragmentation theorems, finite-bin closures, migration/refuge bounds, and their
supporting calculations.

It is not imported by `causal_model`, is not included in the `rach` wheel, and
is not evidence for the RACH methods submission. Its associated material lives
under:

- `docs/eco_genetic_criticality/`
- `examples/eco_genetic_criticality/`
- `tests/eco_genetic_criticality/`

Run its regression tests with:

```bash
pytest -q tests/eco_genetic_criticality
```
