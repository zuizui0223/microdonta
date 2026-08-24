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
-> NOV / RACH-SEQ next-observation design
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
-> NOV / RACH-SEQ observation design
-> controlled truth-peek-free validation
-> exact one-step colonisation projection
-> prospective Campanula measurement design
```

Only code needed to support this spine is primary-paper code.

## Validation rule

Synthetic truth may be used to score an algorithm only after the algorithm has
made its choice. In particular, a candidate observation's predictive distribution
must be constructed from the current admissible region (or another predeclared
predictive model), not from the hidden benchmark truth.

The publication benchmark therefore reports both resolution and error control:

```text
observation budget
-> fraction of confounding edges resolved
-> convergence probability
-> false-exclusion rate for the hidden true explanation
```

A benchmark that feeds the hidden true outcome into candidate ranking is invalid
for the main submission, even if it produces better apparent performance.

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

1. **Pass G2 — benchmark validity.** Keep candidate ranking truth-peek-free, lock
   generators/seeds, and produce the final observation-budget/error-control table.
2. **Pass G5 — reproducibility.** Rebuild the complete figure set from a clean
   environment and verify the submission/boundary gates and wheel.
3. Freeze the public RACH API and submission release.

No new model family, ecological example, UI feature, or rule-transition result is
a blocker before these three steps are complete.

## Public API boundary

Package-level imports should expose RACH first: `causal_admissibility`,
`causal_degeneracy`, `causal_resolvability`, replaceability/CRC,
`mechanism_equivalence_structure`, NOV, `rach_seq`, and `rach_summary`.
Legacy structure-scoring helpers may remain for compatibility but must not define
what the package appears to be.
