# When a different observation beats any number of further repeats

Status: **internal finite-model diagnostic**, not a new optimal-design algorithm.
This extends the replication-information audit with a current-data action
comparison. Existing production APIs, public exports, active MEE manuscript,
submission manifests, frozen G2 results and figures are unchanged.

## 1. The comparison starts after the data already observed

Let D be the current observed history, mu_D strictly positive weights on the
remaining finite full-world domain, and T one fixed discrete question target.
For the old binary protocol, C(w) is its observable-law class, including all
persistent nuisance variables in w. All future repeats are fresh and conditionally
iid given that same full world. An alternative Q has a declared predictive
likelihood P(Q|w,D) valid **after** the current evidence. No realised future
outcome may enter its ranking.

A prior predictive likelihood cannot simply be reused after D unless its
conditional-independence/stationarity assumptions justify that reuse. A reread
of the same stored image is not automatically a fresh repeat. Interventions,
changed sampling units, persistent calibration errors or order effects require
an appropriate enlarged world/transition model. The required reference strings
record these assumptions, but do not establish their truth.

## 2. A sufficient ceiling-crossing condition

Write Z_m for m further readings from the old protocol. At fixed D,

```text
I(T;Z_m | D) <= I(T;C | D) = B_D
```

for every finite m. This also covers a transcript with stopping determined only
by those readings and independent randomization, provided no new observation
channel or world-dependent external information enters that transcript.

Proof: the fixed protocol gives conditional independence T _||_ Z_m | (C,D).
The mutual-information chain rule gives

```text
I(T;C | D) = I(T;Z_m | D) + I(T;C | Z_m,D).
```

Nonnegativity proves the bound. A stopped transcript is a function of the full
repeat sequence and independent randomization, so data processing applies.
The existing finite Bernoulli audit identifies B_D as the asymptotic ceiling.

Consequently,

```text
I(T;Q | D) > B_D
```

is sufficient for one alternative observation to provide more **expected
additional target information** than any finite number of old-protocol repeats.
It does not say every realised Q outcome is better than every realised repeat
sequence. It neither guarantees complete target identification nor optimizes
cost, time, decision loss or mixed-channel sequences.

This is a sufficient condition only. An alternative can beat the next old
reading without exceeding the old protocol's unlimited-repeat ceiling.
Failure of the condition is NOT a reason to prefer repeating.

## 3. Three outputs that must not be conflated

The implementation reports each candidate's raw information, its advantage over
one old reading, and its advantage over B_D. It also computes

```text
I(T;Q | C,D),
```

using the existing noisy-likelihood scorer separately in each old-law class.
This measures information inside distinctions the old protocol cannot resolve.
The chain rule gives I(T;Q|D)-B_D <= I(T;Q|C,D). But positive within-class
information does not guarantee positive marginal information: an XOR target
contrast can remain hidden until C is learned. This is tested, not interpreted
as an immediate switch recommendation or a sequence-impossibility result.

`exceeds_repeat_ceiling_with_margin` is a numerical comparison using an explicit
absolute bit tolerance, not an exact structural-identification certificate.
Target resolution uses the represented target image, not the tolerance. Near-equal
old laws are not combined by a tolerance; the existing exact supplied-ratio
comparison is reused. The model domain remains `not_certified` as exhaustive.

## 4. Controlled noisy ecological example

The three equally weighted programs are `pollination_only`, `abiotic_only` and
`combined`. Synthetic contact-positive probabilities are (0.9,0.1,0.9), while
physiology-positive probabilities are (0.1,0.9,0.9). These are stipulated channel
likelihoods, not a calibration of real contact/physiology measurements and not
evidence of selection, fitness effects or adaptation. The example assumes fresh
readings from both channels are independent of past readings given the program.

| Observed contact history | Next contact, bits | Physiology, bits | All further contact ceiling, bits | Best next singleton |
|---|---:|---:|---:|---|
| None | 0.479083 | 0.479083 | 0.918296 | Tie |
| Present | 0.120730 | 0.529725 | 0.297472 | Physiology |
| Absent | 0.334998 | 0.194910 | 0.684038 | Contact |
| Present, present | 0.015368 | 0.530987 | 0.053908 | Physiology |
| Present, absent | 0.479083 | 0.479083 | 0.918296 | Tie |
| Absent, absent | 0.058284 | 0.029829 | 0.163861 | Contact |

After one positive contact result, current program weights are (9/19,1/19,9/19).
Physiology's 0.529725 bits exceed the entire remaining contact-information
ceiling of 0.297472 bits, a margin of 0.232253 bits. After one negative result,
weights are (1/11,9/11,1/11), and the next contact reading is more informative.
There is therefore no universal 'switch after n readings' rule in this example:
the observed results, not only n, determine the current comparison.

Calibration matters. Holding the contact model/history fixed, increasing the
synthetic physiology error to 0.2 removes ceiling dominance, although physiology
still beats one contact reading. At error 0.3, contact wins even the next-step
comparison. These are sampled specifications, not a robustness certificate for
all intermediate values. No measurement type is inherently superior.

## 5. Reporting and reproduction

```bash
python -m examples.replication_switch_report > replication_switch_report.json
python -m pytest -q tests/test_replication_switch_audit.py
```

The function `audit_replication_switch` accepts only the current weighted pool
and prospective likelihoods. Its example conditions on an explicitly observed
contact history using `condition_on_selected`, then scores without seeing future
outcomes. At exact zero-likelihood exclusion, callers must explicitly restrict
the current support and every candidate matrix together; zero input weights are
not silently accepted as structural exclusion.

Missing likelihoods remain non-estimable. A known Q can demonstrably beat the
old protocol even while another candidate is unmodelled, but it cannot be called
globally best in that incomplete vocabulary. No positive singleton gives only
a one-step/tolerance report; joint-information impossibility is not inferred.
The JSON retains both provenance and the pair of old-law-identical worlds that
still disagree about the target.

Tests compare 512 three-world target/rate/alternative configurations against an
independent joint-table oracle and enumerate old sequences at m=1,2,3 (1,536
bounds). Another 128 seeded cases check noisy alternatives, unequal weights and
conditional within-law information. Other tests cover missing predictions,
true resolution, tolerance, input schemas, no mutation and branch-specific
recommendations. Local isolated testing uses byte-identical copies of the two
existing production/audit dependencies; full repository CI is a separate gate.

## 6. Prior art and ownership

Information-gain design, sequential re-evaluation, nuisance-aware inference and
data processing are established. Relevant primary work includes Foster et al.
(2021), *Deep Adaptive Design: Amortizing Sequential Bayesian Experimental Design*,
PMLR 139:3384-3395 (https://proceedings.mlr.press/v139/foster21a.html), and Sloman et
al. (2024), *Bayesian Active Learning in the Presence of Nuisance Parameters*,
PMLR 244:3245-3263 (https://proceedings.mlr.press/v244/sloman24a.html).
Those papers supply context, not these particular witnesses or a novelty claim.

Boundary owns the declared observable-law/target distinction. This MROD audit
uses that distinction to bound the remaining value of repeating and compare it
with a different next observation. It adds a checked reporting criterion, not
a new universal optimizer, and remains outside the active submission claim set.
