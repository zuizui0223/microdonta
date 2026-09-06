# Structural novelty is not mechanism information: controlled witness

Status: executable companion validation for the Boundary -> MROD interface. This is a minimal deterministic witness, not a general performance benchmark and not a natural-system mechanism claim.

## Question

Boundary can sometimes certify that a candidate observation is structurally redundant. MROD then scores candidate observations by information about residual mechanism identity. Are those two screens actually different, or is MROD just re-labelling structural rank gain?

The smallest useful witness needs three candidates:

```text
1. redundant observation
2. structurally new but mechanism-independent observation
3. structurally new and mechanism-informative observation
```

If cases 2 and 3 have the same structural rank gain but different `I(S;Q)`, rank alone cannot solve the next-observation problem.

## Construction

Let the latent exact log-linear state be

```text
x = (x0,x1,x2).
```

Current evidence observes only

```text
x0 + x1 = 0,
```

so the current observation row is

```text
M = [(1,1,0)].
```

Define the binary mechanism switch

```text
S = 1[x1 > 0].
```

The nuisance coordinate `x2` is independently balanced at `-1` and `+1` inside both states of `S`. The accepted witness rows therefore all satisfy the same current observation while preserving both mechanism states and independent nuisance variation.

Three scalar candidates are declared:

| candidate | row | rank gain | biological role |
|---|---:|---:|---|
| `redundant` | `(2,2,0)` | 0 | rescaled copy of current direction |
| `nuisance_new` | `(0,0,1)` | 1 | observes nuisance `x2` only |
| `mechanism_new` | `(0,1,0)` | 1 | observes mechanism coordinate `x1` |

The first candidate lies in the current row span. The other two are both outside it and therefore both add one exact structural direction.

## Result

The executable witness in `causal_model/structural_mechanism_screen_demo.py` and `tests/test_structural_mechanism_screen_demo.py` gives exactly:

| candidate | rank gain | `I(S;Q)` bits | normalized MROD value |
|---|---:|---:|---:|
| `redundant` | 0 | 0 | 0 |
| `nuisance_new` | 1 | 0 | 0 |
| `mechanism_new` | 1 | 1 | 1 |

Thus

```text
rank gain = 0  -> zero mechanism information          [in this exact screen]
rank gain = 1  -/-> positive mechanism information   [false converse]
```

The nuisance candidate is genuinely new in the full latent state: it divides the current fibre by `x2`. But the division is balanced identically within both values of `S`, so it provides no information about mechanism identity.

## Candidate-selection consequence

Suppose an uninformed policy chooses uniformly among all three candidates. Its expected normalized mechanism information is

```text
(0 + 0 + 1)/3 = 1/3.
```

Suppose a structural-only policy first removes the row-span-redundant candidate and then has no further criterion to distinguish the two rank-gain-one candidates. Under uniform tie-breaking its expected mechanism information is

```text
(0 + 1)/2 = 1/2.
```

MROD selects the candidate with maximum mechanism information and obtains

```text
1.
```

These numbers are not offered as a general policy-performance estimate. They are an exact witness that structural screening and mechanism-information screening answer different questions.

## What this validates

The witness supports the asymmetric composition:

```text
Boundary structural screen
    -> eliminate observations already determined by the current map

MROD information screen
    -> among non-redundant candidates, identify which ones partition mechanism S
```

Boundary supplies a necessary structural screen in its exact class. MROD supplies the target-specific criterion.

## What this does not validate

The witness does not show:

- that every MROD problem has a log-linear Boundary representation;
- that rank gain is required in noisy or tolerant problems in the same algebraic sense;
- that MROD is globally optimal among all experimental-design criteria;
- that uniform rank-gain tie-breaking is a serious competitor rather than a diagnostic foil;
- that a one-bit mechanism is representative of ecological complexity;
- that the selected observation is cost-optimal.

Its purpose is narrower: to prove by executable construction that `new information about the full latent state` and `new information about the scientific mechanism target` are not synonymous.
