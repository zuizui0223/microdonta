# Private compatibility aliases after the MROD rename

Status: **intentional compatibility layer; not publication-facing API**.

The active method is **Mechanism-Resolving Observation Design** and the advertised
package vocabulary is descriptive: admissible mechanism region, mechanism
entropy/resolvability/replaceability, observation information value, and
sequential observation design.

Several historical module paths are nevertheless registered privately in
`causal_model/__init__.py`:

| Historical import path | Canonical backend |
|---|---|
| `causal_model.causal_admissibility` | `causal_model.mechanism_region` |
| `causal_model.causal_replaceability` | `causal_model.mechanism_replaceability_core` |
| `causal_model.rach_seq` | `causal_model.sequential_observation` |
| `causal_model.nov_evsi` | `causal_model.observation_information` |
| `causal_model.nov_calibration` | `causal_model.information_value_calibration_core` |
| `causal_model.rach_set` | `causal_model.joint_observation_set` |
| `causal_model.replaceability_nov` | `causal_model.replaceability_observation_value` |

These are `sys.modules` aliases only. The retired filenames themselves are absent,
none of these names appears in `causal_model.__all__`, and publication-facing
modules must import descriptive canonical modules rather than the aliases.

## Why the aliases remain

Frozen validation and support code predates the rename and still contains some
historical imports. Removing those aliases or rewriting package source after the
validated submission freeze would change the wheel contents and therefore break
the recorded wheel hash even if numerical behaviour remained identical.

For the current submission, preserving the validated artifact is more important
than cosmetic replacement of private historical identifiers. The authoritative
artifact SHA, workflow runs and hashes are recorded in `paper/release_readiness.json`.

## Rules

1. Do not advertise a historical alias in README, manuscript, Supporting
   Information, tutorials, package metadata, figures, or `causal_model.__all__`.
2. Do not add new publication-facing code that imports a historical alias.
3. Historical G2 machine identifiers remain unchanged as provenance.
4. Species-level *Campanula microdonta* is a biological name and is unrelated to
   repository branding.
5. Removing or renaming these aliases inside the distributed package is a
   package-source change. It requires an intentional new G5/reviewer artifact
   freeze and a new recorded wheel hash before it can become the submission
   version of record.

The naming gate and compatibility tests enforce these rules without changing the
validated package source.
