# Boundary -> MROD: formal interface through observation fibres

Status: cross-project theory note. This file does not create a runtime dependency on `boundary`.

## 1. Common state space

Let the full declared model state be

```text
Z = (theta, S),
```

where `theta` collects continuous or nuisance parameters and `S` is the mechanism variable of scientific interest. Let the current observation map be

```text
O : Z -> Y.
```

For an exact observed value `y`, the compatible fibre is

```text
A_0(y) = {z : G(theta)=1 and O(z)=y}.
```

MROD's `A_epsilon` is the tolerance-thickened analogue produced by the declared discrepancy rule. The unresolved mechanism set is not the full fibre itself but its projection onto mechanism identity,

```text
M_epsilon(y) = pi_S(A_epsilon(y)).
```

This separates the two projects cleanly:

- **Boundary** studies what geometry/equivalence the observation map leaves in the fibre;
- **MROD** studies uncertainty in the mechanism projection of that fibre and the information supplied by future observations.

## 2. Structural redundancy implies zero next-observation information

Let `Q` be a deterministic candidate observation. Suppose that on the relevant model support it is already determined by the current observation:

```text
Q = h(O)
```

for some function `h`. Then, after conditioning on the current exact observation `O=y`, `Q` is constant on the compatible fibre. Therefore it cannot distinguish any function of the latent state, including mechanism identity `S`:

```text
I(S; Q | O) = 0.
```

Equivalently, inside an exact current fibre,

```text
I(S; Q | A_0(y)) = 0.
```

So a structurally redundant candidate is guaranteed to have zero mechanism information, independent of which mechanism vocabulary is later projected from the fibre.

This gives a one-way screening theorem:

```text
no new observation direction
        =>
zero mechanism information
        =>
do not spend observation budget on that candidate for mechanism resolution.
```

## 3. Boundary's rank theorem is a special exact screen

For the positive log-linear class used in `boundary`, current observations are

```text
M x = y.
```

A scalar candidate has row `a^T`. If

```text
a in rowspan(M),
```

then there is a coefficient vector `c` with `a^T = c^T M`, and therefore

```text
a^T x = c^T y.
```

The candidate value is already determined by the current observation. It cannot refine the current fibre and, by the result above, cannot carry new information about any mechanism label defined on that fibre.

Thus Boundary's exact rank test can serve as a **structural zero-value screen** before MROD scoring in this restricted observation class.

## 4. The converse is deliberately false

A candidate outside the current row span changes the structural fibre, but this does **not** guarantee positive information about the mechanism variable `S`.

The candidate may separate only nuisance or continuous parameter variation while leaving the distribution of `S` identical across its outcomes. In that case the observation is structurally new but mechanism-irrelevant:

```text
new observation direction
        !=>
positive I(S;Q | A_epsilon).
```

This distinction already has an executable witness in `tests/test_observation_information.py`: `test_evsi_is_zero_for_mechanism_independent_observation` constructs a candidate whose high/low outcome varies across accepted rows but is exactly balanced within both mechanism states. The candidate therefore has a genuine outcome partition yet `I(S;Q)=0` and observation information value zero.

This is why MROD is not reducible to observation rank.

## 5. Resulting two-stage logic

The projects therefore compose asymmetrically:

```text
Boundary structural screen
    Is Q already determined by the current observation map?
    If yes: Q cannot resolve mechanism ambiguity.
    If no: Q is structurally new, but mechanism relevance is still unknown.

MROD mechanism-information screen
    Does Q partition the current admissible region differently across S?
    Quantify this by I(S;Q | A_epsilon)/K.

Sequential design
    Among verified candidates with positive current information,
    choose the largest current value and recompute after the realised outcome.
```

Boundary therefore supplies a necessary condition for a candidate to add information in its exact structural class; MROD supplies the target-specific value criterion. Neither subsumes the other.

## 6. Relation to the exact and tolerant cases

The clean implication `Q=h(O) => I(S;Q|O)=0` is exact. MROD generally works with a tolerance-thickened region `A_epsilon`, where finite precision and approximate predictions matter. A measurement that is exactly redundant at the structural level remains structurally redundant, but measurements that are only approximately redundant can gain practical discrimination as precision improves.

Accordingly:

- Boundary should not claim that replication or precision never helps;
- MROD should not infer positive mechanism value merely because a candidate measures a new biological quantity;
- the observation model, tolerance and predictive partition must remain explicit.

## 7. Scientific interpretation

This bridge sharpens the practical question behind a limitations section. The first question is not `what expensive variable did we fail to measure?` but `which distinctions are collapsed by the current observation map?` Once a candidate is known to add a genuinely new observation direction, the second question is `does that direction actually separate the mechanisms we care about?`

A molecular assay, fitness measurement or field observation can fail at either stage. Conversely, a relatively simple observational measurement can be useful when it both adds a new observation direction and separates the residual mechanism projection.
