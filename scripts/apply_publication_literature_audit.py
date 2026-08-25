"""Apply the frozen publication-only Campanula primary-literature wording audit.

This script changes prose/documentation only. It must not modify benchmark
protocols, frozen result files, inference code, generators, or tests.
"""
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one old block, found {count}")
    return text.replace(old, new, 1)


root = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Main manuscript: source-bounded Campanula wording, 1990a/b disambiguation,
# and final figure inventory.
# ---------------------------------------------------------------------------
mpath = root / "paper" / "mee_manuscript_draft.md"
m = mpath.read_text(encoding="utf-8")

old = """Published Izu Islands records describe increased autonomous selfing, reduced
flower size, and pollinator turnover along island isolation gradients (Inoue &
Amano 1986; Inoue 1988, 1990). Those summaries are biologically informative but
do not provide trait-specific total performance (W(z)), a resolved factor
(F(z)) or (E(z)), or a proxy whose conversion is shown to be stable across
islands. In the projection ledger the record is therefore
`not_applicable` to N1–N4 as an empirical channel-identification claim.
"""
new = """Published comparisons of mainland Honshu and Izu-island *Campanula* document
population differences in pollinator assemblage, flower size and breeding/mating
system, but they do not establish a single continuous response to geographic
isolation. Inoue & Amano (1986) reported *Bombus diversus* on mainland Honshu,
*B. ardens* plus halictid bees on Oshima, and halictid-bee pollination on
Niijima, Kozushima and Hachijo; island flowers were smaller than mainland
flowers, and Hachijo material was self-compatible and potentially autogamous.
Inoue (1988) expanded natural-population bagging and pollinator observations,
finding mainland Honshu and Oshima predominantly self-incompatible while the
other surveyed Izu islands were predominantly self-compatible, with bumblebees
absent from the islands except Oshima. Inoue (1990a) then described mainland
Honshu and Oshima as self-incompatible/outcrossing, Toshima and Niijima as
self-compatible but largely outcrossing, and Miyake and Hachijo as
self-compatible and predominantly inbreeding; Inoue (1990b) related dichogamy
and sex allocation to estimated selfing rates. The earlier papers treated the
island material within *C. punctata*, whereas the 1990 mating-system papers
treated Izu-island populations as *C. microdonta* and mainland populations as
*C. punctata*. Allozyme work independently documented mainland–island genetic
differentiation and lower outcrossing estimates in self-compatible island groups
(Inoue & Kawahara 1990). These are population patterns and proxies, not direct
measurements of a RACH channel. They do not provide trait-specific total
performance (W(z)), a resolved factor (F(z)) or (E(z)), or a proxy whose
conversion is shown to be stable across regimes. In the projection ledger the
record is therefore `not_applicable` to N1–N4 as an empirical
channel-identification claim.
"""
m = replace_once(m, old, new, "manuscript Campanula source synthesis")

old = """- Inoue, K. 1990. Evolution of mating systems in island populations of
  *Campanula microdonta*: pollinator availability hypothesis. *Plant Species
  Biology* 5: 57–64.
- Inoue, K. & Kawahara, T. 1990. Allozyme differentiation and genetic structure in
"""
new = """- Inoue, K. 1990a. Evolution of mating systems in island populations of
  *Campanula microdonta*: pollinator availability hypothesis. *Plant Species
  Biology* 5: 57–64.
- Inoue, K. 1990b. Dichogamy, sex allocation, and mating system of *Campanula
  microdonta* and *C. punctata*. *Plant Species Biology* 5: 197–203.
- Inoue, K. & Kawahara, T. 1990. Allozyme differentiation and genetic structure in
"""
m = replace_once(m, old, new, "manuscript Inoue 1990a/b references")

old = """## Figure plan

1. **Figure 1 — Exact boundary and workflow.** N1 observational symmetry; N2–N4
   sufficient/insufficient measurement boundary; hand-off to RACH.
2. **Figure 2 — Controlled confound.** Model ranking versus the admissible set,
   causal degeneracy, and the resolving observation.
3. **Figure 3 — Sequential selection and error control.** Frozen v2 budget curves
   for RACH-SEQ and random-order baseline, convergence, edge resolution,
   observations used, distractors selected, false exclusion, and seed-level
   uncertainty/contrasts.
4. **Figure 4 — NOV information and calibration.** `I(S;Q|A_ε)/K` identity,
   admissible-region conditioning versus fresh re-inference, and realised-gain
   calibration.
5. **Figure 5 — Earned ecological projection.** Exact one-step colonisation
   factorisation, projection-ledger boundary, and prospective Campanula
   measurement design.

ABM endpoint sweeps, sensitivity analyses, and detailed known-truth panels belong
in Supplementary Information. Ecological-rule panels and structure discovery are
not part of this submission.
"""
new = """## Figure plan

1. **Figure 1 — Controlled confound.** ABC model ranking versus the admissible
   set, causal degeneracy, NOV ranking, and the resolving quantitative
   observation.
2. **Figure 2 — Sequential selection and error control.** Frozen v2 budget curves
   for RACH-SEQ and the matched random-order baseline: convergence, initial-edge
   resolution, observations used, distractors selected, and seed-level
   uncertainty.
3. **Figure 3 — NOV conditioning and calibration.** Stored-region conditioning
   versus fresh deterministic re-inference and predictive EVSI versus realised
   resolvability gain.
4. **Figure S1 — Known-truth recovery.** Controlled self-consistency across the
   frozen noise strata, retained as Supplementary validation rather than a
   natural-system mechanism claim.

N1–N4 and the earned one-step ecological projection are presented directly as
formal results/equations in the text rather than reserving ungenerated main-figure
numbers. ABM endpoint sweeps and extended sensitivity analyses belong in
Supplementary Information. Ecological-rule panels and structure discovery are not
part of this submission.
"""
m = replace_once(m, old, new, "manuscript final figure plan")
mpath.write_text(m, encoding="utf-8")

# ---------------------------------------------------------------------------
# Literature ledger: clarify what the source supports versus legacy pattern labels.
# ---------------------------------------------------------------------------
ipath = root / "docs" / "inoue_literature_values.md"
i = ipath.read_text(encoding="utf-8")
i = replace_once(
    i,
    "- Inoue, K. 1990. Evolution of mating systems in island populations of\n",
    "- Inoue, K. 1990a. Evolution of mating systems in island populations of\n",
    "Inoue 1990a label",
)
i = replace_once(
    i,
    "- Inoue, K. 1990. Dichogamy, sex allocation, and mating system of *Campanula\n",
    "- Inoue, K. 1990b. Dichogamy, sex allocation, and mating system of *Campanula\n",
    "Inoue 1990b label",
)

old = """| Flower size | Island flowers are smaller than mainland flowers, interpreted as adaptation to smaller pollinators. Exact per-island corolla values require PDF transcription. | current y_obs as directional flower-size gradient |
"""
new = """| Flower size | Island flowers were reported smaller than mainland flowers; adaptation to smaller pollinators was proposed as a possible explanation, not demonstrated. Exact per-island corolla values require PDF transcription. | supports an island-vs-mainland flower-size contrast; not a source-confirmed monotonic distance slope |
"""
i = replace_once(i, old, new, "Inoue flower-size interpretation")

old = """| Dichogamy, 1990b | Staminate-phase duration differs among mating-system classes; male reproductive effort decreases with estimated selfing rate. This is dichogamy/sex-phase timing evidence, not a measured static herkogamy endpoint. | hypothesis_prediction / future observation, not y_obs |
"""
new = """| Dichogamy, 1990b | Staminate-phase duration differs among mating-system classes; male reproductive effort decreases with estimated selfing rate. This is dichogamy/sex-phase timing evidence, not a measured static herkogamy endpoint. | hypothesis_prediction / future observation, not y_obs |
| Allozyme/outcrossing, 1990 | Mainland and island populations form differentiated genetic groups; outcrossing estimates are higher in mainland/Oshima groups, intermediate in northern self-compatible islands, and lower in southern predominantly inbreeding islands. Genetic diversity within island populations decreases with distance from the mainland. | independent population-genetic context; not trait-specific W/F/E |
"""
i = replace_once(i, old, new, "Inoue allozyme/outcrossing row")

old = """## Current y_obs consequence

The current ABC acceptance target deliberately remains narrow:

- `selfing_distance`: selfing increases / outcrossing declines along the island
  isolation gradient. Source: Inoue 1990a, with 1986/1988 breeding-system
  corroboration.
- `flower_size_distance`: flower size declines from mainland/less isolated
  contexts toward island small-pollinator contexts. Source: Inoue & Amano 1986.

Pollinator assemblage is observed context (`x_obs`), not an output target.
"""
new = """## Current y_obs consequence

The current ABC acceptance target deliberately remains narrow. The historical
pattern names ending in `_distance` are **legacy implementation labels**, not a
claim that the cited primary papers estimated a continuous linear response to
geographic distance.

- `selfing_distance`: interpret as an ordered mating-system contrast across the
  declared mainland/island comparison: mainland/Oshima are predominantly
  self-incompatible/outcrossing, northern self-compatible islands remain largely
  outcrossing, and southern self-compatible islands are predominantly inbreeding.
  Source: Inoue 1990a/1990b and Inoue & Kawahara 1990, with 1986/1988
  breeding-system corroboration. Do not describe this as a source-fitted
  monotonic distance law.
- `flower_size_distance`: interpret only as the source-confirmed island-versus-
  mainland smaller-flower contrast from Inoue & Amano 1986. The source summary
  does not establish a monotonic per-island flower-size decline with distance.

Pollinator assemblage is observed context (`x_obs`), not an output target.
"""
i = replace_once(i, old, new, "Inoue y_obs legacy distance labels")
ipath.write_text(i, encoding="utf-8")

# ---------------------------------------------------------------------------
# Channel protocol: make the published record statement source-faithful.
# ---------------------------------------------------------------------------
cpath = root / "docs" / "campanula_channel_protocol.md"
c = cpath.read_text(encoding="utf-8")
old = """The current source-confirmed Izu-island record contains directional patterns in:

```text
selfing rate
flower size
Bombus to halictid pollinator transition.
```

It does not currently contain:
"""
new = """The current source-confirmed mainland/Izu comparison contains cross-population
patterns in:

```text
breeding and mating system (SI/SC; outcrossing/inbreeding, with 1990 estimates)
island-versus-mainland flower size
Bombus-versus-halictid pollinator assemblage.
```

These comparisons do not by themselves establish a continuous monotonic
isolation-distance response for each trait. They also do not currently contain:
"""
c = replace_once(c, old, new, "Campanula current published record")
old = """This is not a failure of the record. It tells us exactly why trait geometry,
flower-size means, selfing rates, and visitor identity cannot settle the channel
question on their own.
"""
new = """This is not a failure of the record. It tells us exactly why trait geometry,
flower-size contrasts, breeding/mating-system summaries, genetic outcrossing
estimates, and visitor identity cannot settle the channel question on their own.
"""
c = replace_once(c, old, new, "Campanula channel evidence boundary")
cpath.write_text(c, encoding="utf-8")

# Publication-only guardrails.
for forbidden in (
    "pollinator turnover along island isolation gradients",
    "selfing increases / outcrossing declines along the island isolation gradient",
    "**Figure 5 — Earned ecological projection.**",
):
    for p in (mpath, ipath, cpath):
        if forbidden in p.read_text(encoding="utf-8"):
            raise RuntimeError(f"stale overstatement remains in {p}: {forbidden}")

print("publication literature audit patch complete")
