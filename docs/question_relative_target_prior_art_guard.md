# Prior-art ceiling for question-relative mechanism targets

Status: internal claim guard.

The identities used by the question-relative target audit are standard information theory:

```text
T=tau(S)
H(T|A) <= H(S|A)
I(T;Q|A) <= I(S;Q|A)
```

They follow from deterministic coarsening, the entropy chain rule and the mutual-information chain rule/data-processing principle. MROD does not claim novelty for those identities, task-specific information gain, hierarchical latent variables or sufficient/coarsened targets.

The repository-level contribution is narrower: connect the already implemented target-aware observation utilities to the biological design rule that a study need only resolve the predeclared mechanism distinction it actually claims, and demonstrate executable ranking reversal between full-mechanism learning and question-relative mechanism resolution.
