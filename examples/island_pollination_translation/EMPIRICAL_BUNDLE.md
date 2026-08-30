# Evidence-aware empirical bundle audit

`translation_tracks.py` declares which gates must be present. The evidence-aware
audit additionally checks whether each claimed gate is supported by an admissible
measurement record rather than by a convenient label or proxy.

Passing this audit means **the measurement contract is complete enough to run the
declared empirical RACH analysis**. It does not, by itself, establish the causal
effect or confirm the izu-core mechanism in nature.

## Generate a template

```bash
python -m examples.island_pollination_translation.audit_bundle template \
  network_context_effective_service \
  network_bundle.json
```

The generated file is intentionally incomplete. Replace every placeholder, add
traceable provenance, and change a gate from `missing` to `present` only when the
corresponding observation exists.

The machine-readable shape is documented in `empirical_bundle.schema.json`.
Runtime validation does not require the optional `jsonschema` package.

## Audit a bundle

```bash
python -m examples.island_pollination_translation.audit_bundle audit \
  network_bundle.json \
  --json \
  --output network_bundle.audit.json
```

Add `--require-ready` when the command should fail unless every required gate is
accepted. Exit codes are:

- `0`: schema is valid; and, with `--require-ready`, every gate is accepted;
- `1`: schema is valid but the measurement contract remains incomplete;
- `2`: JSON or top-level schema is invalid.

## Evidence kinds

- `direct_measurement`: observed quantity with unit, method, comparison unit and
  provenance;
- `prespecified_definition`: a frozen comparison, hierarchy, formula or linkage
  rule;
- `derived_estimand`: formula plus explicit `derived_from` evidence IDs; every
  dependency must itself pass;
- `calibrated_proxy`: proxy record whose target, calibration scope and calibration
  provenance are explicit. Calibration status must be `stable` or `calibrated`.
  `unverified` never closes a channel gate.

A present record must use the bundle's declared comparison unit or one of its
explicitly compatible units. Duplicate evidence IDs, missing dependencies,
post-outcome definitions for outcome-blind gates and placeholder provenance are
rejected.

## N3/N4 guard

For the network-context track, visitation, abundance, identity, richness, degree
or centrality cannot fill `visitor_specific_direct_effectiveness`. A proxy can
fill that gate only when its proxy-to-effectiveness conversion is independently
calibrated or shown stable over the declared comparison scope.

## Independent complete bridge

The complete `change -> service -> dependency/assurance -> response` track also
requires `independent_system=true`. This prevents an Izu-derived or internally
recycled example from being counted as the independent empirical bridge required
by the completion condition.
