# Question-relative mechanism target audit summary

The existing MROD target-aware API already computes `I(T;Q|A)` for a declared target. This audit isolates the scientifically important special case `T=tau(S)`, where the target is a deterministic coarsening of the full mechanism world.

Executable witness:

```text
S=(T,U1,U2), H(S)=3 bits, H(T)=1 bit

deep_submechanism:
    I(S;Q)=2 bits
    I(T;Q)=0 bits

question_class:
    I(S;Q)=1 bit
    I(T;Q)=1 bit
```

Thus full-mechanism information prefers the deeper assay while the question-relative target prefers the coarser class-resolving observation. Holding `T` fixed leaves `H(S)=2` bits, showing that question-relative mechanism resolution can be complete while lower-level mechanism ambiguity remains.

This is an internal theory/witness audit. It does not change the active MEE estimand or claim novelty for standard information-theory identities.
