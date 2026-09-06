# Target-factorization adapter: structural identification is not just entropy zero

Status: internal Boundary -> MROD contract. The active MEE manuscript, frozen G2,
public mechanism objective I(S;Q|A)/K and target-aware API are unchanged.

The canonical theorem and proof live in Boundary:
https://github.com/zuizui0223/boundary/blob/main/docs/target_factorization_bridge.md .
The existing question-relative note `question_relative_mechanism_target.md`
explains the special target T=tau(S); the present note connects that question to
what current observations can identify.

## Exact contract

For a declared feasible-world domain D, exact observation O and fixed target T:

```text
T constant on every nonempty O-fibre in D
<=> exists g on O(D) with T=g(O) throughout D.
```

Constancy on the one realised fibre C_y is local identification only. For a
finite domain and strictly positive mass on every declared world,

```text
T=g(O) on D <=> H(T|O)=0.
```

Zero-mass alternatives and unvisited simulation worlds invalidate the structural
converse. Empirical entropy zero is a statement about the represented support,
not proof that all scientifically compatible worlds agree. Discrete entropy is
used; no differential-entropy or general measurable-space claim is implied.

## Next observation and complete repair are different outputs

Condition on current C_y and keep the same target and row weighting for every Q.
The existing target API supplies raw bits I(T;Q|C_y) and a within-target score
I(T;Q|C_y)/H(T|C_y) when H is positive. Full mechanism normalization by K is a
separate scale; do not compare their magnitudes as a universal utility.

```text
I(T;Q|C_y)=0       -> no immediate target information under these weights
0<I(T;Q|C_y)<H(T) -> expected progress, not guaranteed complete identification
I(T;Q|C_y)=H(T)   -> every positive-mass outcome identifies T
```

The last line is a structural statement about all of C_y only with full support
and a correct, coherent candidate map. Equivalently, Q separates every pair with
the same current observation but different target values.

If T is already identified, additional target information is zero even when a
candidate provides substantial information about within-target mechanisms. But
zero values for all declared candidates do not imply that T is identified; the
candidate vocabulary may miss the distinction. Singleton zero also does not
rule out joint synergy. Non-estimable candidates remain non-estimable, not zero.

A deterministic recoding Q=h(O) adds no information after exact O. A fresh noisy
replicate or recovery of discarded raw variables is not necessarily such a
recoding. Equality of realised data is not equality of observable sampling laws.

## Shared fixture and verification

`tests/fixtures/target_factorization_v1.json` is mirrored in Boundary, contract
`boundary-mrod-target-factorization-v1`, SHA-256:

```text
d12478f3354170130a8ed11e0c019a0099f5dc942d4365195770619ae3f14841
```

`tests/test_target_factorization_bridge.py` tests the existing production target
API and actual candidate outcome filters against the same worlds that Boundary
uses to construct reconstruction maps or conflicting pairs. It checks:

- full-support entropy/factorization equivalence and complete-repair equivalence;
- a resolved question with two remaining bits of full-mechanism information;
- positive information of 0.918295834 bits with 2/3 bit still unresolved;
- local/global and zero-mass/structural distinctions;
- zero information among registered candidates with unresolved target entropy.

Tests have no cross-repository runtime import or network dependency. These are
finite controlled witnesses, not empirical ecological claims or a substitute
for causal assumptions.

## Actionable limitations report

The handoff is a declared target, its current compatible image and unresolved
contrasts, followed by candidate predictions and conditional values. Report
expected progress separately from complete repair and from biological adequacy
of the target itself. Resolving a pollination-process question is not automatically
resolving an evolutionary-history or adaptation question.

No new optimizer is introduced. Factorization, goal-oriented experimental design,
and even likelihood-free target information design using ABC have prior art;
see Taraldsen (2018), Attia et al. (2018), and Chakraborty, Huan & Catanach (2024)
in the canonical Boundary note. This is an executable interface and claim audit.
