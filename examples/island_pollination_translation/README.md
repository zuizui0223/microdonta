# izu-core → microdonta empirical translation bridge

This example carries three empirical translation questions from the `izu-core`
island-ecology programme into **RACH next-observation design**.

## Resolution status

The word *resolved* has two different meanings here and they must not be mixed.

| level | current status | meaning |
|---|---|---|
| Methods / epistemic resolution | **3 / 3 closed** | The estimand or causal chain, identifiability/proxy boundary, required observations, forbidden shortcuts and falsifiable completion condition are explicit. |
| Real-system empirical resolution | **0 / 3 closed** | No qualifying real observation bundle yet establishes any of the three causal claims. |

The authoritative machine-readable record is `CURRENT_STATE.json` (schema 2.0).
Thus the current RACH Methods paper may say that all three inherited *epistemic
problems* have been converted into falsifiable observation contracts. It must not
say that the three ecological mechanisms have been empirically demonstrated.
Future empirical closure is tracked separately and is not a blocker for the
current `izu-core` or microdonta/RACH submission.

The boundary is deliberate:

- `izu-core` has already closed the primary synthetic island-ecology hypotheses for
  its current paper;
- the three questions here are future empirical mechanism-identification tracks;
- microdonta closes their **measurement and identifiability specification**, not
  their real-system causal answer;
- microdonta/RACH does not reinterpret the frozen ABM result as empirical proof.

## Why this belongs in microdonta

RACH keeps all causal explanations still compatible with the declared model family
and asks which next observation would reduce the remaining causal degeneracy. The
three `izu-core` sidelines have exactly that form.

```text
izu-core
  frozen synthetic mechanism / response architecture
      ↓
  unresolved empirical mapping
      ↓
microdonta / RACH
  explicit estimand + identifiability boundary + missing gates
      ↓
  next-observation design
      ↓
  empirical equivalence class reduced only after new admissible observation
```

This also matches the theorem/proxy boundary already used by microdonta: a visit
count or network statistic is not automatically a direct reproductive channel. If
the observation is a proxy, its conversion has to be stable or calibrated.

## Track 1 — real signed functional starting position

### Epistemic closure

Within the frozen ABM, pre-existing lineage position in an abstract functional
matching space is the replicated minimal tested generator of within-run
response-sign branching. The corresponding empirical estimand is fixed as

```text
signed_position
= plant_matching_trait - pollinator_functional_center
```

before inspecting the downstream outcome.

The mapping requires compatible plant/pollinator units, a source-native functional
center, a prespecified sign convention, downstream response and sampling
uncertainty. An unsigned matching score is not a substitute. Nor are pollinator
guild midpoints, family/body-size proxies or a floral syndrome label. If a trait
or functional center is proxied, N3/N4 proxy-calibration conditions apply.

### Empirical status

**Open.** No current real-system record passes all required gates. The remaining
question is whether this prespecified signed position actually predicts the
direction or magnitude of a real island response.

## Track 2 — real network context → effective service

### Epistemic closure

Local network context is a strong bidirectional branch allocator in the frozen
ABM. For a real system, however, network context is not itself service. The direct
service estimand is

```text
effective_service = Σ_k V_k E_k
```

where `V_k` is visitor-specific rate and `E_k` is direct per-visit effectiveness.
The same prespecified hierarchy must also provide local context and downstream
reproductive outcome.

Visitor abundance, identity, richness, network degree or centrality cannot be
silently called `effective_service`. They remain proxies unless direct
effectiveness is measured or the proxy-to-service conversion satisfies the N3/N4
stability/calibration conditions.

### Empirical status

**Open.** Partial bridges exist, but there is no current strict mapping-ready
system with the required rate × effectiveness linkage plus matched reproductive
outcome.

## Track 3 — complete change → service → dependency/assurance → response bridge

### Epistemic closure

The ecological synthesis separates four causal layers:

```text
pollinator functional change
    → effective service
    → reproductive dependency / autonomous assurance
    → floral, reproductive or evolutionary response
```

This is specified as a **RACH-SEQ missing-link observation problem**. Each link is
an observation target that can cut a different mechanism-equivalence edge. A
missing middle link remains missing and must not be inferred from its neighbours.

### Empirical status

**Open.** Several external systems provide adjacent pieces, but there are currently
zero complete bridge systems. Empirical closure requires at least one independent
system with all four links on the same or a prespecified compatible unit, together
with sampling hierarchy, uncertainty and source provenance.

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

Empirical readiness is conjunctive: an empirical track closes only when every
required gate is present. This is intentionally stricter than accepting a
convenient proxy. Epistemic closure means that those gates and the forbidden
shortcuts have already been made explicit; it is not itself biological evidence.

## Current separation of responsibilities

| repository | responsibility |
|---|---|
| `izu-core` | frozen island ecological result, H1–H5, external response-state challenge, protected failures |
| `microdonta` | causal admissibility, proxy/calibration boundaries, equivalence classes, falsifiable observation contracts and next-observation design |
| future empirical programme | collect qualifying real-system bundles and test the three ecological claims |

The connection is therefore **complementary rather than duplicative**. `izu-core`
asks what ecological response architecture the frozen ABM supports; microdonta
asks exactly what additional observation would be required before assigning a
named real system to one of those causal mechanisms.
