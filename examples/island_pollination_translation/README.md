# izu-core → microdonta empirical translation bridge

This example carries the three unresolved empirical translation questions from the
`izu-core` island-ecology programme into **RACH next-observation design**.

The boundary is deliberate:

- `izu-core` has already closed the primary synthetic island-ecology hypotheses for
  its current paper;
- the three questions here are **future empirical mechanism-identification tracks**;
- they are not prerequisites for the current `izu-core` submission;
- microdonta/RACH does not reinterpret the frozen ABM result as empirical proof.

## Why this belongs in microdonta

RACH keeps all causal explanations still compatible with the declared model family
and asks which next observation would reduce the remaining causal degeneracy.  The
three `izu-core` sidelines have exactly that form.

```text
izu-core
  frozen synthetic mechanism / response architecture
      ↓
  unresolved empirical mapping
      ↓
microdonta / RACH
  explicit missing gates
      ↓
  next-observation design
      ↓
  causal equivalence class reduced only after new admissible observation
```

This also matches the theorem/proxy boundary already used by microdonta: a visit
count or network statistic is not automatically a direct reproductive channel.
If the observation is a proxy, its conversion has to be stable or calibrated.

## Track 1 — real signed functional starting position

### Starting point from izu-core

Within the frozen ABM, pre-existing lineage position in an abstract functional
matching space is the replicated minimal tested generator of within-run
response-sign branching.

### What is still missing

A real island system must define the analogous **signed** starting position before
looking at the downstream outcome:

```text
signed_position
= plant_matching_trait - pollinator_functional_center
```

The mapping needs compatible plant/pollinator units, a source-native functional
center, a prespecified sign convention and a downstream response on compatible
units.

An unsigned matching score is not a substitute.  Nor are pollinator guild
midpoints, family/body-size proxies or a floral syndrome label.

### RACH role

This is a next observation aimed at separating a true starting-state mechanism
from downstream context, lineage identity and other propagation filters.  If a
trait or functional center is proxied, N3/N4 proxy-calibration conditions apply.

## Track 2 — real network context → effective service

### Starting point from izu-core

Local network context is a strong **bidirectional branch allocator** in the frozen
ABM.  It can attenuate a decline, cross the sign boundary, or make a response worse.

### What is still missing

For a real system, local context must be linked to direct service on the same
prespecified hierarchy:

```text
effective_service = Σ_k V_k E_k
```

where `V_k` is visitor-specific rate and `E_k` is direct per-visit effectiveness.
The minimum gate also includes matched context/reproductive outcomes.

Visitor abundance, identity, richness or network degree cannot be silently called
`effective_service`.

### RACH role

This is primarily a **proxy-calibration / channel-measurement** problem.  It tests
whether the network-context observation actually measures the service channel
needed to distinguish competing causal explanations.

## Track 3 — complete change → service → dependency/assurance → response bridge

### Starting point from izu-core

The current ecological synthesis separates four layers:

```text
pollinator functional change
    → effective service
    → reproductive dependency / autonomous assurance
    → floral, reproductive or evolutionary response
```

Several external island systems provide adjacent pieces of this chain, but the
current programme has no complete matched bridge.

### What is still missing

At least one independent non-Izu system should measure all four links on the same
or a prespecified compatible unit, with sampling hierarchy, uncertainty and
source provenance retained.

### RACH role

This is naturally a **RACH-SEQ observation package**.  Each observed link can cut a
different mechanism-equivalence edge.  A missing middle link remains missing; it
must not be inferred from its neighbours.

## Programmatic gate audit

```python
from examples.island_pollination_translation import (
    audit_track,
    default_translation_tracks,
)

for track in default_translation_tracks():
    print(track.track_id, track.current_state)

assessment = audit_track(
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

Readiness is conjunctive: a track closes only when every required gate is present.
This is intentionally stricter than accepting a convenient proxy.

## Current separation of responsibilities

| repository | responsibility |
|---|---|
| `izu-core` | frozen island ecological result, H1–H5, external response-state challenge, protected failures |
| `microdonta` | causal admissibility, proxy/calibration boundaries, equivalence classes, next-observation design |

The connection is therefore **complementary rather than duplicative**.  `izu-core`
asks what ecological response architecture the frozen ABM supports; microdonta asks
what additional observation would be needed before assigning a named real system
to one of those causal mechanisms.
