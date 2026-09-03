# Adaptive recomputation theorem for mechanism-resolving observation design

Status: theorem-level condition for when sequential recomputation adds value beyond the strongest fixed second-measurement ordering.

## Question

The current method recomputes `I(S;Q | A_t)` after each realised observation. That algorithmic rule is not itself a scientific result. The nontrivial question is:

> When is recomputation *strictly necessary*—meaning that no precommitted second measurement can match the expected mechanism-information value of an adaptive choice?

This document answers that question exactly for a two-step finite design with a fixed first observation and a finite remaining candidate set.

## Setup

Let `X` be the realised outcome of the first selected observation, with positive-probability branches `x`.

For each remaining candidate `q`, define its branch-specific second-step mechanism-learning value

\[
U_q(x)=I(S;Q_q\mid X=x),
\]

or the normalized MROD value `U_q(x)/K`. The normalization does not change rankings or the theorem.

An adaptive policy observes `X=x` and then chooses a branchwise maximizer. Its expected second-step value is

\[
V_{\rm adapt}=\mathbb E_X\left[\max_q U_q(X)\right].
\]

A static policy must choose one remaining candidate before seeing `X`. The strongest possible static comparator is therefore

\[
V_{\rm static}=\max_q\mathbb E_X[U_q(X)].
\]

Random ordering is weaker than this comparator and is not used in the theorem.

## Theorem A1 — adaptive recomputation never underperforms the best static second measurement

\[
\boxed{V_{\rm adapt}\ge V_{\rm static}.}
\]

### Proof

For every fixed candidate `q` and every branch `x`,

\[
\max_j U_j(x)\ge U_q(x).
\]

Taking expectation gives

\[
\mathbb E[\max_jU_j(X)]\ge\mathbb E[U_q(X)].
\]

This holds for every `q`, hence it also holds for the candidate with the largest expected fixed value:

\[
V_{\rm adapt}\ge\max_q\mathbb E[U_q(X)]=V_{\rm static}.
\]

∎

## Theorem A2 — necessary and sufficient condition for strict adaptive advantage

Let

\[
A(x)=\operatorname{argmax}_q U_q(x)
\]

be the set of branchwise maximizers. Then

\[
\boxed{V_{\rm adapt}=V_{\rm static}}
\]

if and only if

\[
\boxed{\bigcap_{x:P(X=x)>0}A(x)\ne\varnothing.}
\]

Equivalently,

\[
\boxed{V_{\rm adapt}>V_{\rm static}}
\]

if and only if **no one remaining candidate is optimal on every positive-probability first-outcome branch**.

### Proof — sufficiency for equality

If a candidate `q*` belongs to every `A(x)`, then

\[
U_{q*}(x)=\max_qU_q(x)
\]

for every positive-probability branch. Therefore

\[
\mathbb E[U_{q*}(X)]=\mathbb E[\max_qU_q(X)]=V_{\rm adapt}.
\]

Since the best static value is at least the value of `q*` and Theorem A1 gives the reverse inequality,

\[
V_{\rm static}=V_{\rm adapt}.
\]

### Proof — necessity for equality

Assume `V_adapt=V_static`. Let `q*` be a static candidate attaining `V_static`. Define the branchwise gap

\[
D(x)=\max_qU_q(x)-U_{q*}(x)\ge0.
\]

Equality of adaptive and static expected values gives

\[
\mathbb E[D(X)]=0.
\]

A nonnegative random variable has expectation zero only when it is zero on every positive-probability branch. Hence

\[
U_{q*}(x)=\max_qU_q(x)
\]

for every such branch, so `q*` belongs to the intersection of all branchwise argmax sets. ∎

## Corollary A2a — unique rank reversal is sufficient for strict advantage

If two positive-probability branches `x_1,x_2` have different **unique** best remaining candidates, then their argmax sets are disjoint. Theorem A2 therefore gives

\[
V_{\rm adapt}>V_{\rm static}.
\]

This is the precise version of the informal statement “the ranking changes after seeing the first result.” Mere rank movement is not enough if one candidate remains tied for best on every branch; the empty common-argmax condition is exact.

## Corollary A2b — when recomputation is unnecessary

If one remaining candidate is optimal in every possible first-outcome branch, recomputing scores may still be useful for reporting, but it cannot improve expected second-step value over precommitting that candidate.

Thus adaptive recomputation is not claimed as universally beneficial. Its benefit has an exact branchwise condition.

## Minimal four-world witness

Take four equally likely mechanism states

\[
S\in\{a,b,c,d\}.
\]

The first observation is

\[
X=0\text{ for }a,b,
\qquad
X=1\text{ for }c,d.
\]

Two remaining deterministic candidates are defined so that

- `Q1` distinguishes `a` from `b` but is constant on `c,d`;
- `Q2` is constant on `a,b` but distinguishes `c` from `d`.

Because each candidate is a deterministic function of `S`, its conditional mutual information equals the entropy of its outcome within a branch. Therefore

| branch | `I(S;Q1|X=x)` | `I(S;Q2|X=x)` |
|---|---:|---:|
| `X=0` | 1 bit | 0 bits |
| `X=1` | 0 bits | 1 bit |

The branchwise argmax intersection is empty. Hence

\[
V_{\rm adapt}=1\text{ bit},
\qquad
V_{\rm static}=0.5\text{ bit}.
\]

The first observation itself carries one bit, so the expected two-step totals are 2 bits adaptively versus 1.5 bits under the best precommitted second candidate.

### Minimality within this deterministic branch-switch class

Strict adaptive advantage requires at least two positive-probability first-outcome branches with no common maximizer. A branch with a single compatible mechanism state has zero conditional mechanism entropy, so every candidate has zero conditional mutual information there and every candidate is tied for best. Such a branch cannot eliminate the maximizer from another branch.

Therefore each of at least two branches must contain at least two compatible mechanism states. At least four states are required. The witness above attains that lower bound.

## Relation to the frozen G2 benchmark

G2 establishes that current information-guided sequential design outperforms random order on the declared synthetic family while retaining hidden truth. Theorems A1–A2 answer a different question: they compare adaptive recomputation with the **best possible fixed second candidate** for a fixed first observation.

The new theorem therefore removes a weak interpretation of the G2 result. The benefit of recomputation is not “information ranking beats randomness.” It is:

> when first-observation outcomes induce incompatible branchwise optimal next measurements, no static second-measurement ordering can attain the adaptive expected value.

The theorem does not prove that the full greedy MROD policy is globally optimal over arbitrary multi-step experiment trees. That would require additional adaptive-submodularity or dynamic-programming conditions and is not claimed.

## Executable obligations

`tests/test_adaptive_recomputation_theorem.py` must verify:

1. `V_adapt >= V_static` over exhaustive small utility tables;
2. equality iff the positive-branch argmax intersection is nonempty;
3. strict advantage for unique branchwise rank reversal;
4. equality when one candidate is common-best across all branches;
5. the four-world mutual-information witness gives 1 versus 0.5 second-step bits;
6. no deterministic three-world construction of the specified two-branch type can produce the same strict branch-switch witness.
