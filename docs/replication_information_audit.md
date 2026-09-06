# What more of the same observation can and cannot resolve

Status: **internal finite-model audit**, not a new optimizer or an addition to
active MEE performance claims. The current full-mechanism objective, manuscript,
submission manifest, frozen G2 results/figures and public exports are unchanged.
This audit reuses the existing noisy-likelihood scorer and outcome conditioner
in `causal_model/empirical_observation_contract.py`.

## 1. The scientific question is a replication protocol, not just a sample size

Declare a finite current domain of full worlds W with strictly positive weights,
a fixed discrete question target T, and one calibrated binary observation law
for each world. Fresh readings Y_1,...,Y_n are conditionally independent and
identically distributed **given the same full world**, including persistent
nuisance or measurement parameters. Let p_w be that world's success probability.

The `conditional_iid_reference` is mandatory provenance for this assumption; a
string does not prove independence or calibration. A new plant each time, a
persistent plant-specific effect, a changing environment, repeated views of one
saved image, or a destructive measurement are different sampling protocols.

The implemented model does not infer independence, stationarity, calibration or
exhaustiveness of nature from supplied likelihood tables. Missing likelihoods
remain non-estimable. An unmodelled missing-record process is not silently added;
include it explicitly in an observation model before applying an appropriate audit.

## 2. An expected residual floor under the declared protocol

Let C(W)=p_W denote the observable-law class: worlds belong to the same class if
they have exactly the same declared binary sampling law. Let N_n=sum_i Y_i.
The full sequence and its count have the same information about W and T in this
conditionally iid Bernoulli model: the combinatorial factor in the binomial
likelihood is independent of W.

The finite-world model has the Markov property T -> C -> N_n. Therefore

```text
H(T | N_n) = H(T | C) + I(T; C | N_n),
I(T; N_n) <= I(T; C),
H(T | N_n) >= H(T | C).
```

Here conditional entropies average over possible data, at the declared current
weights. They are NOT lower bounds on the entropy after each realised outcome.
A surprising or strongly discriminating result can leave much less uncertainty;
another result can leave more. No pathwise monotonicity is claimed.

**Proof of the decomposition.** Expand I(T; C,N_n) in both orders. Because
I(T; N_n | C)=0, I(T; C)=I(T; N_n)+I(T; C | N_n). Rearranging the entropy
identity gives the statements above. Nonnegativity supplies the bound.

As n grows, the sample proportion identifies the finite law class C almost
surely: its distinct probabilities have positive separation, and the law of
large numbers gives N_n/n -> p_W. Finite-alphabet conditional entropy then gives
H(C|N_n)->0. Since 0<=I(T;C|N_n)<=H(C|N_n),

```text
lim_n I(T; N_n) = I(T; C),
lim_n H(T | N_n) = H(T | C).
```

Expected information is nondecreasing in n, using the chain rule on nested full
sequences and count sufficiency. This is not a rate guarantee: arbitrarily close
but distinct laws can require impractically many repeats.

`irreducible_target_entropy_bits` is H(T|C): the expected residual floor for this
ONE fixed protocol and finite declared model. `asymptotic_information_bits` is
I(T;C). Neither is a limit on every observation available to science.

## 3. A structural witness is stronger than a small information score

The report retains a pair of row indices whenever two worlds share C but differ
in T. Their likelihood ratio equals one for every possible iid sequence with
positive probability under their common law. Their posterior odds therefore stay
equal to their current odds; no repeat of this protocol separates that pair.

The existence of such a pair is weight-independent as long as every declared
world has positive weight. The magnitude H(T|C) is weight-dependent. The code
uses exact equality of the normalized supplied likelihood ratio, not an `isclose`
threshold. Close estimated probabilities do not certify exact equivalence.
Uncertain calibration requires a larger state model or a sensitivity analysis.

Conversely, I(T;Y_1)=0 does NOT establish that full-world laws are the same.
Marginalizing a persistent nuisance variable can hide dependence that appears
in repeated readings. The example in section 5 deliberately tests this failure.

## 4. Three explanations and a measurement that cannot finish the job

A controlled example gives equal weight to three question targets:

```text
pollination_only: Pr(contact reading present)=0.9
abiotic_only:     Pr(contact reading present)=0.1
combined:        Pr(contact reading present)=0.9
```

These are declared synthetic likelihoods, not validated field predictions. In
particular, contact is not assumed to prove natural selection or adaptation.

The first and third programs share an observable law. Initially H(T)=log2(3).
The two law classes have masses 2/3 and 1/3, and the first contains two equally
weighted targets. Consequently H(T|C)=2/3 bit and the information ceiling is
log2(3)-2/3=0.918295834 bits.

| Fresh readings | Expected information, bits | Expected remaining target entropy, bits |
|---:|---:|---:|
| 1 | 0.479082650 | 1.105879851 |
| 2 | 0.678377880 | 0.906584621 |
| 10 | 0.915772985 | 0.669189516 |
| 20 | 0.918284234 | 0.666678266 |
| 50 | 0.918295834 | 0.666666667 |
| Infinite-repeat limit in the declared model | 0.918295834 | 0.666666667 |

More precise contact information can resolve the noise surrounding the law class,
but not pollination-only versus combined membership within that class. An
additional channel that distinguishes those programs requires its own predictive
model. The audit does not identify a cheapest observation or an optimal schedule.

## 5. A positive observational-design result: preserve repeated-unit identity

Compare two synthetic population programs:

- Heterogeneous: half the individuals have p=0.2 and half p=0.8.
- Homogeneous: all individuals have p=0.5.

With one reading from each newly sampled independent individual, both programs
produce independent Bernoulli(0.5) observations. No number of such unlinked
single readings distinguishes these two declared programs.

With repeated readings of the SAME individual, its p remains fixed. Both
programs still predict Pr(Y_1=1)=0.5, but

```text
Pr(Y_1 != Y_2 | heterogeneous) = 0.32,
Pr(Y_1 != Y_2 | homogeneous)   = 0.50.
```

Thus with equal program priors,

```text
I(T;Y_1)       = 0,
I(T;Y_1,Y_2)   = 0.024309740 bits,
I(T;Y_1:10)    = 0.336911078 bits,
I(T;Y_1:50)    = 0.939901445 bits.
```

The code represents four full worlds with p=(0.2,0.8,0.5,0.5), preserving
persistent nuisance before forming the repeated-data likelihood. Averaging those
probabilities by T first and then taking a product instead describes nuisance
redrawn each time; it incorrectly reports zero information for the persistent-
individual design. Both protocols are implemented as separate witnesses.

This is not a claim that repeated measurements always beat spatial replication.
It shows why sampling-unit identity and the dependence model are part of the
observation map. Retaining individual IDs and paired outcomes can matter more
than adding an unstructured total count. This is the observation-process analogue
of the earlier singleton-zero/joint-positive warning, not a new synergy theorem.

## 6. Statistical learning is not finite-data exact determination

For two worlds with p=0.1 and p=0.9, the same protocol has H(T|C)=0. Its expected
residual is 0.468995594 bit after one reading and 0.000012359518 bit after twenty.
The information approaches one bit, unlike the three-program example.

Yet every finite binary sequence has strictly positive likelihood under both
worlds. Exact represented-support target determination has NOT occurred after
any finite number of readings. This is compatible with identifiability from the
sampling law and arbitrarily strong statistical evidence. The code checks each
positive-probability outcome's target support, not rounded entropy or MI=H(T).
Expected residual is also calculated directly from posterior branches so that
H(T)-I rounding does not falsely display exact determination.

## 7. Reproduction and validation

```bash
python -m examples.replication_limit_report > replication_limit_report.json
python -m pytest -q tests/test_replication_information_audit.py
```

The four files are an internal audit module, an example CLI, these notes, and one
focused test module. The existing noisy-likelihood API supplies the information
scores and actual posterior conditioning. An independent direct-sequence oracle
checks count compression for all 256 combinations of binary target maps and
binary rate choices on four worlds, at n=0,1,2,3 (1,024 comparisons). Other tests
cover nonuniform weights, identical laws, deterministic endpoints, impossible
outcomes, missing targets/predictions, close-but-distinct laws, and underflow.

The maximum n=256 is an exhaustive-computation guard, not a theoretical limit.
Positive probabilities that underflow raise an error; they are never silently
reclassified as structural zeros. No resampling or truncation of worlds is used.
All `complete_repair_in_declared_pool` flags are conditional on the enumerated
model. `feasible_domain_exhaustiveness` remains `not_certified`.

## 8. Prior art and relation to Boundary

The information criterion and nuisance-aware design are established, not new
inventions of this audit. For context, primary research includes:

- Kleinegesse, S. & Gutmann, M.U. (2020). Bayesian Experimental Design for Implicit
  Models by Mutual Information Neural Estimation. PMLR 119:5316-5326.
  https://proceedings.mlr.press/v119/kleinegesse20a.html
- Sloman, S.J., Bharti, A., Martinelli, J. & Kaski, S. (2024). Bayesian Active
  Learning in the Presence of Nuisance Parameters. PMLR 244:3245-3263.
  https://proceedings.mlr.press/v244/sloman24a.html

These citations establish the prior-art setting; the elementary finite-law
proof above and controlled witnesses are supplied explicitly, not attributed as
new theorems or as exact examples from those papers.

Boundary's target-factorization criterion can be applied to the statistical
observation map W -> C(W): the target factors through this map exactly when
it is constant in every observable-law class. MROD adds the expected information
profile at finite repetition budgets. No cross-repository runtime import is
introduced, and neither active paper absorbs this optional audit.
