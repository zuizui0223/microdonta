# Horizon information profile as a limitation diagnostic

Status: **internal audit only**. This note does not modify the active MEE manuscript, public API, frozen G2 policy or current positive-singleton selection algorithm.

## Question

After the current admissible mechanism region `A` has been constructed, MROD normally scores one candidate observation at a time:

```text
V(Q)=I(S;Q|A)/K.
```

The executable XOR witness shows that

```text
V(Q)=0 for every singleton Q
```

does not imply that combinations of those observations are uninformative. The limitation question can therefore be indexed by a **fixed-bundle horizon** rather than collapsed into one generic zero-information label.

## Definition

Let `C` be a finite declared candidate vocabulary with a coherent joint predictive vector. For integer `b>=1`, define

```text
J_b(A)
= max_{B subseteq C, 1 <= |B| <= b} I(S;Q_B|A)/K.
```

`J_b` is called the **horizon information profile** here only as an internal diagnostic label. It is not proposed as a new information-theory quantity or optimization method. The maximization is over fixed bundles; it is not an optimization over outcome-dependent adaptive trees.

The exhaustive implementation is

```text
causal_model/horizon_information_profile.py
```

and is intentionally restricted to small controlled systems.

## Immediate properties

### H1. Monotonicity

Because the feasible fixed-bundle set for horizon `b` is contained in the feasible set for `b+1`,

```text
J_1 <= J_2 <= ... <= J_|C|.
```

Thus later bundle horizons cannot contain less *best available fixed-bundle information* than earlier horizons.

### H2. Entropy bound

For every bundle,

```text
I(S;Q_B|A) <= H(S|A),
```

so

```text
0 <= J_b <= H(S|A)/K = 1-R(A).
```

The implementation also rejects inputs whose empirical mechanism entropy exceeds the declared `K`-bit normalization.

### H3. One-step stop versus delayed fixed-bundle information

If

```text
J_1=0
```

but

```text
J_b>0
```

for some `b>1`, then the current positive-singleton greedy rule has no informative immediate move but the declared candidate vocabulary is not sequence-information-limited. The smallest such `b` is recorded as the **first positive bundle size** for this exhaustive fixed-bundle diagnostic.

It is not the minimum number of steps required by an adaptive policy. An outcome-dependent policy can choose different later candidates on different branches and is a different optimization problem.

The XOR witness gives exactly

```text
J_1=0,
J_2=1
```

for a one-bit mechanism target.

### H4. Full-vocabulary zero is a sequence-information limit

At the maximum horizon,

```text
J_|C| = I(S;Q_C|A)/K,
```

because the full candidate vector is one of the admissible bundles and every smaller fixed bundle is a projection of that vector.

Therefore

```text
J_|C|=0
```

licenses the sequence-information-limit statement for the declared candidate vector used in the stopping claim guard.

## Interpretation

The profile refines the next action without pretending that every limitation has the same cause:

```text
J_1 > 0
    immediate singleton actionability

J_1 = 0 but J_b > 0 for some b > 1
    some informative fixed bundle exists; non-myopic/bundle-level design should be considered

J_|C| = 0
    declared candidate vector is sequence-information-limited
```

This diagnosis is distinct from **prediction limitation**. `J_b` is defined only when the candidate outcomes have a coherent joint predictive representation on the current state. Missing or incompatible outcome models must be repaired before a horizon profile is interpreted.

## Claim ceiling

Do not interpret this audit as proving or supplying:

- a new non-myopic Bayesian experimental-design algorithm;
- a scalable optimizer for large candidate vocabularies;
- an acquisition order from a high-information bundle;
- a minimum adaptive step count;
- cost-optimal or management-optimal design;
- global optimality of the current MROD greedy policy;
- adaptive submodularity or any other structural guarantee;
- novelty for synergistic information or batch information acquisition.

The exhaustive search cost grows combinatorially as

```text
sum_{j=1}^b choose(|C|, j),
```

so the implementation is a **controlled claim-ceiling diagnostic**, not the publication method.

## Relation to the limitation-to-action prototype

The internal reporting layer can use the horizon result only to refine a zero-singleton state:

```text
singleton zero + bundle horizon not audited
    -> audit joint/bundle information before claiming sequence impossibility

singleton zero + first positive bundle size b>1
    -> report existence of an informative fixed bundle; do not infer an adaptive order

full-horizon zero
    -> report sequence-information limit relative to the declared candidate vector
```

The active paper remains a positive-singleton information-guided method. This audit exists to stop its limitation language from exceeding what the algorithm has established.
