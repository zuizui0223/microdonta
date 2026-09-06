# From a target-identification contract to an outcome-by-outcome limitations report

Status: internal worked example and input-correctness repair. The active MEE
manuscript, frozen G2, full-mechanism objective and package exports are unchanged.
The example uses the existing target-information API, not a new design algorithm.

## 1. Reproduce the report

From the repository root:

```bash
python -m examples.target_limitation_report > target_limitation_report.json
pytest -q tests/test_target_input_contract.py tests/test_target_limitation_report.py
```

`build_target_report(rows, candidates, target_columns=[...])` can also be imported
from the example. Rows must be an already constructed admissible pool with equal
positive weight, a fully declared discrete target and candidate outcome models.
This is not an arbitrary empirical CSV-to-causal-mechanism inference function.
Do not silently feed unequal weights to this unweighted API. Candidate predictive
partitions are checked on the represented rows, not biologically validated by code.

## 2. Missing target information is not target resolution

The previous `_state` implementation used `row.get(column)`. If the requested
column was absent on every row, all target states became `(None,)`. The reported
entropy was zero and downstream target-aware design could stop as identified.

The production target API now rejects absent columns, `None`, non-finite numeric
labels (including nested target tuples), unhashable labels and malformed column
declarations. This validation applies before checking candidate coverage, including
when the candidate list or outcome list is empty. Genuine constant targets still
have zero entropy. Valid inputs keep the same information calculations.

A missing target is an input/model-definition problem: construct the target on
every represented world, or report that it is not specified. A missing candidate
prediction is different: the target can be valid while that candidate's information
value remains non-estimable. Neither is replaced by numerical zero. An explicit
string such as `unknown` is an ordinary declared category to the API; assigning it
to every row does not establish that the intended biological question is resolved.

## 3. Controlled ecological interpretation, not field evidence

The synthetic current pool has 12 equally weighted worlds. Three explanatory
programs are retained: `pollination_only`, `abiotic_only`, and `combined`. Each has
four equally represented submechanism states. Retaining the combined program
avoids falsely forcing the two processes to be mutually exclusive.

For this demonstration ONLY, channel readings deterministically reveal program
bits. No natural-population contact rate, physiology measurement or molecular
assay has been calibrated here. Reading a contact channel in nature does not by
itself prove pollinator-mediated selection, adaptation or evolutionary history.

The same program target is used for every candidate; `target_switches` metadata
does not redefine the scientific question for each measurement.

| Candidate | Target information (bits) | Expected remaining target entropy | All represented outcome branches identify the target? |
|---|---:|---:|---|
| Contact channel | 0.918295834 | 2/3 bit | No |
| Physiology channel | 0.918295834 | 2/3 bit | No |
| Within-program submechanism assay | 0 | log2(3) bits | No |
| Follow-up without an outcome model | Non-estimable | Not available | Not available |

Initial target entropy is log2(3), approximately 1.584962501 bits. Both channel
observations are tied best **among estimable candidates**, not globally best
among all declared candidates, because the unmodelled follow-up is still present.
The submechanism assay distinguishes four worlds inside each program but does not
distinguish the program question. Its zero target value does not mean no scientific
value for a different target.

## 4. Report what each possible result would leave unresolved

For the contact candidate, the idealized demonstration predicts:

- Contact-channel absent (probability 1/3): only `abiotic_only` remains. The target
  is resolved in the pool, while four within-program worlds remain.
- Contact-channel present (probability 2/3): `pollination_only` and `combined`
  remain. Target entropy is 1 bit; recomputing on this branch makes the physiology
  channel fully resolving for the target in the represented pool.

Thus the first observation gives expected progress, not guaranteed one-step
resolution. An explicitly modelled joint channel bundle resolves all three
programs, but this example does not optimize its cost or establish a cheapest
acquisition sequence. Compatibility of joint or sequential measurements in a real
system requires its own observation/transition model.

## 5. A usable reporting contract

The JSON report retains the target image, a pair of disagreeing row indices,
raw information bits, each outcome's probability and remaining target image,
complete-repair status, predictive coverage, all tied positive-best candidates,
recommendation scope and the corresponding next action.

`complete_repair_in_pool` is based on singleton target images in every
positive-probability branch, not a rounded entropy score. The numerical information
tolerance only affects ranking/stopping. Impossible outcomes are retained with
zero probability and undefined identification status, rather than treated as
observed failures. Candidate and outcome names must be unique to prevent accidental
merging of distinct prospective outcomes in the report.

A disagreeing row pair certifies disagreement within the supplied current pool.
It does not prove equality of observable sampling laws or that the pool enumerates
all biologically feasible worlds. Reports explicitly say
`feasible_domain_exhaustiveness: not_certified`.

When all verified singleton values are zero, the report asks for a joint-information
audit rather than asserting impossibility; an XOR regression enforces this.
`sequence_information_limit` remains unset because this adapter does not estimate
a coherent full joint candidate vector. Partial predictive coverage cannot produce
even a complete one-step stop certificate.

## 6. Relationship to Boundary and publication scope

Boundary supplies the structural target/fibre criterion and conflicting-world
certificates. MROD supplies conditional target values and actual candidate outcome
filters. See `target_factorization_bridge.md` for the full-support qualification
and `question_relative_mechanism_target.md` for `T=tau(S)`.

The present adapter makes those distinctions usable in a report. It does not
claim novelty for conditional entropy, target-oriented design or reporting a
posterior predictive partition. It does not turn a model-relative target result
into an intervention effect, a fitness result or proof of adaptation. There are
no changes to the accepted-row selection rule, frozen benchmark or active paper.
