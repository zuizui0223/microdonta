# microdonta / RACH mainline

Status: normative development boundary for the MEE submission.

microdonta has one scientific product:

> Given observations that may be compatible with multiple ecological mechanisms,
> retain the admissible explanations, quantify what remains unresolved, and choose
> the next observation that is expected to separate them without pretending that a
> non-identifying pattern has selected a causal winner.

## Product contract

### Input

1. a declared mechanism vocabulary `S`;
2. a pre-data biological constraint grammar `G(theta)`;
3. fixed ecological context `x_obs`;
4. independent observations `y_obs` and their observation map;
5. a predeclared distance/tolerance defining `A_epsilon`;
6. candidate future observations whose predictive outcomes are derived without
   access to benchmark truth or inspected outcomes.

### Core computation

```text
observation contract
-> N1-N4 identifiability gate where an exact W=F*E projection is available
-> A_epsilon: restricted admissible causal hypotheses
-> CA / D_RACH / R_RACH / CRC
-> mechanism-equivalence structure
-> validated NOV = I(S;Q | A_epsilon)/K
-> RACH-SEQ next-observation design
```

### Output

The primary output is never "the best mechanism" by default. It is:

- the surviving explanation set and causal admissibility profile;
- degeneracy/resolvability and replaceability diagnostics;
- unresolved mechanism-equivalence edges;
- the ranked next measurement and the remaining observation budget;
- an explicit statement when the observation class cannot identify a channel.

## Publication spine

The MEE paper is fixed to:

```text
N1-N4 exact channel-identifiability boundary
-> RACH admissible explanation set
-> information-theoretic NOV/EVSI and RACH-SEQ observation design
-> controlled truth-peek-free validation
-> exact one-step colonisation projection
-> prospective Campanula measurement design
```

Only code needed to support this spine is primary-paper code.

## Predictive-probability and NOV boundary

Synthetic truth may be used to score an algorithm only after the algorithm has
made its choice. A candidate observation's predictive distribution is derived
from the **current** admissible region whenever its listed outcomes form a
verified mutually exclusive and exhaustive partition. Hidden benchmark truth is
never a predictive prior.

The publication-level single-shot NOV is `next_observation_evsi`. For a verified
current-region predictive map,

```text
NOV(Q)
= sum_q Pr(q | current A_epsilon)
    [R(A_epsilon | Q=q) - R(A_epsilon)]
= I(S;Q | A_epsilon) / K.
```

Thus

```text
0 <= NOV(Q) <= 1 - R_RACH(A_epsilon).
```

`NOV(Q)=0` exactly when `Q` carries no information about the remaining mechanism
vector under current `A_epsilon`; the upper bound is attained exactly when the
observation resolves all remaining switch entropy under the declared system.
This is the normative meaning of validated NOV in microdonta.

If a candidate's outcomes overlap, are incomplete, or required simulator columns
are absent, the stored admissible region does not identify the predictive outcome
distribution. `next_observation_evsi` therefore reports that candidate as **not
estimable**; it does not silently substitute a declared prior and call the result
a validated EVSI. The older target-switch score is retained only as the explicitly
named compatibility helper `heuristic_next_observation_value` and is not part of
the primary public API.

RACH-SEQ is slightly broader because it must still be able to rank a declared
field-design candidate set. At each sequential step it uses
`Pr(q | current A_epsilon)` when a partition is verified; otherwise it may use a
predeclared outcome prior as an explicit fallback. Every step records which
probability source was used. Thus fallback ranking is transparent and is never
confused with the validated single-shot `I(S;Q|A_epsilon)/K` quantity.

## Validation rule

The publication benchmark reports both resolution and error control:

```text
observation budget
-> fraction of confounding edges resolved
-> convergence probability
-> false-exclusion rate for the hidden true explanation
```

A benchmark that feeds the hidden true outcome into candidate ranking is invalid
for the main submission, even if it produces better apparent performance.

The final G2 configuration is preregistered in
`paper/g2_frozen_benchmark_protocol.json`. The final runner accepts no scientific
parameter overrides; every output is tagged with the SHA-256 hash of that protocol.
The protocol has no favourable performance threshold: favourable, null, or
adverse frozen outcomes are all reportable results.

## Exact ecological projection boundary

N1-N4 apply exactly only after a positive factorisation such as `W=F*E` is earned
for a declared ecological output. The current exact ecological bridge is one-step
expected retained juvenile recruitment. Multistep invasion growth, persistence,
endpoint trait-space geometry, and other ABM outputs remain extension-required
unless separately factorised.

## What is not the mainline

The following may remain in the repository for compatibility, Supplement, or
future work, but they do not set development priority or support primary claims:

- rule-transition / endpoint ABM panels;
- provisional ecological-rule discovery;
- structure discovery;
- the optional attraction-trait simulator;
- Streamlit/UI work;
- new ecological case studies beyond the prospective Campanula design;
- the externally owned eco-genetic-criticality programme.

The three izu-core adapters are translation contracts into the RACH observation
layer. They do not change the mainline and are not empirical validation of RACH.

## Active development order

1. **Pass G2 — benchmark validity.** Keep candidate ranking truth-peek-free,
   use current-`A_epsilon` sequential predictive reweighting, and run the frozen
   protocol to produce the final observation-budget/error-control table.
2. **Pass G5 — reproducibility.** Rebuild the complete figure set from a clean
   environment and verify the submission/boundary gates and wheel.
3. Freeze the public RACH API and submission release.

No new model family, ecological example, UI feature, or rule-transition result is
a blocker before these three steps are complete.

## Public API boundary

Package-level callables expose RACH first: `compute_causal_admissibility`,
`causal_degeneracy`, `causal_resolvability`, replaceability/CRC,
`mechanism_equivalence_structure`, `next_observation_evsi`, `run_rach_seq`, and
`rach_summary`. Canonical submodules such as
`causal_model.causal_admissibility` and `causal_model.rach_seq` remain importable
under their own names and are never shadowed by root-level functions. Legacy
structure-scoring helpers and heuristic NOV may remain for compatibility but must
not define what the package appears to be.
