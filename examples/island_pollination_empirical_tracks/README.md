# Island pollination empirical tracks

This programme defines three standalone empirical observation-design problems for island plant–pollinator systems. It belongs to **microdonta/RACH** and is not a companion, extension, validation layer, or submission dependency of any other manuscript.

The shared principle is simple: a causal mechanism is not identified until the required observation channel is measured on compatible units. Convenient proxies do not close a missing gate unless their calibration is stable or independently established.

## Track 1 — signed functional starting position

Question:

> Does a prespecified signed plant position relative to the local pollinator functional environment predict a downstream response?

The target estimand is

```text
signed_position = plant_matching_trait - pollinator_functional_center
```

Required observations include a predeclared plant matching trait, a source-native pollinator functional centre on compatible units, a fixed sign convention, downstream response, and sampling uncertainty.

Unsigned matching, guild midpoints, body-size substitutions, family-level values, or post-outcome choice of the functional centre do not satisfy this gate.

## Track 2 — network context to effective service

Question:

> Does a measured change in local partner context alter rate-weighted effective pollination service and downstream reproduction?

The target service quantity is

```text
effective_service = sum_k(visitor_rate_k * direct_effectiveness_k)
```

Visitor abundance, visitor identity, richness, degree, or interaction frequency alone are not direct service measurements. Visitor-specific rate and direct per-visit effectiveness must be linked on the declared comparison hierarchy.

## Track 3 — complete change → service → dependency/assurance → response chain

Question:

> Can one empirical system close the full causal sequence on the same or prespecified compatible units?

```text
pollinator functional change
    -> effective service
    -> reproductive dependency / autonomous assurance
    -> downstream floral, reproductive, or evolutionary response
```

This is a RACH-SEQ observation package. Each link must be observed or independently calibrated. A missing middle link remains missing; it cannot be inferred from adjacent observations or assembled post hoc from incompatible studies.

## Programmatic audit

```python
from examples.island_pollination_empirical_tracks import (
    audit_empirical_track,
    default_empirical_tracks,
)

for track in default_empirical_tracks():
    print(track.track_id, track.current_state)

assessment = audit_empirical_track(
    "network_context_effective_service",
    {
        "matched_transition_or_context_unit",
        "repeated_local_context_support",
        "visitor_specific_rate",
        "downstream_reproductive_outcome",
    },
)

assert not assessment.ready
assert "visitor_specific_direct_effectiveness" in assessment.missing_gates
```

Readiness is conjunctive: every required gate must be present.

## Ownership boundary

This programme is owned entirely by microdonta/RACH. Its state, tests, terminology, priorities, and completion rules are governed locally. No external repository or manuscript is required to define, justify, complete, or publish these tracks.
