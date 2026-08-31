# Publication workspace — Mechanism-Resolving Observation Design

This directory contains the single active *Methods in Ecology and Evolution* methods submission.

The separate mechanistic-evidence / identification-boundary Perspective lives at:

**https://github.com/zuizui0223/boundary**

No active Paper A manuscript, theorem implementation, figure generator or reviewer bundle belongs here.

## Active claim spine

```text
admissible mechanism region
→ mechanism entropy / resolvability / replaceability
→ observation information value V(Q)=I(S;Q|A_epsilon)/K
→ sequential observation design with current-value recomputation
→ truth-peek-free frozen G2 selection benchmark
→ reproducible software and anonymous reviewer bundle
```

The methods paper validates an observation-selection procedure under controlled known-truth systems. It does not claim natural-system mechanism discovery.

## Active files

| Path | Role |
|---|---|
| `manuscript.md` | active Research Article manuscript |
| `supporting_information.md` | active SI |
| `REPOSITORY_SCOPE.md` | methods-only ownership rule |
| `submission_manifest.json` | machine-readable evidence boundary |
| `check_submission_bundle.py` | scientific claim/provenance gate |
| `check_mee_submission.py` | journal-format gate |
| `check_active_naming.py` | retired-name guard |
| `build_reviewer_bundle.py` | anonymous methods-only reviewer snapshot |
| `g2_frozen_benchmark_protocol.json` | immutable benchmark protocol/provenance |
| `results/g2_frozen_v2_summary.json` | immutable primary validation numbers |
| `results/g5_reproducibility_summary.json` | immutable reproducibility record |
| `final_figure_inventory.json` | submission figure inventory |
| `make_g2_figure.py` | G2 figure generator |

## Naming

The formal method/software name is **Mechanism-Resolving Observation Design**. Publication-facing vocabulary is descriptive rather than acronym-based:

```text
admissible mechanism region
mechanism entropy D
mechanism resolvability R
observation information value V(Q)
sequential observation design
information-guided sequential policy
```

The historical frozen G2 protocol identifier and stored policy key are retained unchanged solely for provenance. They are not the current method name.

## Reproduce

```bash
python paper/check_submission_bundle.py
python paper/check_mee_submission.py
python paper/check_active_naming.py
python paper/build_reviewer_bundle.py
pytest -q
```

The separate Paper A repository has its own CI and reviewer bundle and is not a submission dependency for this methods paper.
