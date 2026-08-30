# Channel identifiability from trait performance

## Question

Suppose a trait's total performance can be written as

```text
W(z) = F(z) E(z),
```

with positive channels `F` and `E`. The question is not merely whether the product can be algebraically factorised. It is what mechanistic information survives when an ecological study observes the net response in increasingly rich ways.

The executable finite-grid form is `causal_model.channel_identifiability_theory`; proxy extensions are in `causal_model.proxy_calibration_theory`.

---

## 1. What rich net observations still fail to preserve

A complete net performance curve can look mechanistically rich. It determines every threshold-feasible set

```text
Omega_t = {z : W(z) >= t}
```

for every `t>0`, and therefore every lower and upper edge, width, measure, component count and other geometric or topological summary derived from those sets. More generally, any observation of the form

```text
O = Phi(W)
```

sees only the product.

This class includes:

```text
the complete performance curve W(z)
all threshold-feasible sets Omega_t
all boundaries and widths of those sets
all connected-component counts
all geometry or topology computed solely from W
all summaries or rankings whose input is only W
```

The non-trivial point of N1 is therefore not that “a product has two factors.” It is that even arbitrarily detailed knowledge of the full response surface and all of its threshold geometry remains net-only.

---

## 2. Theorem N1 — exact invariance of the complete net-only observation class

For any positive function `c(z)`, define

```text
F_c(z) = c(z) F(z)
E_c(z) = E(z) / c(z).
```

Then

```text
F_c(z) E_c(z) = W(z)
```

pointwise. Consequently every net-only statistic is invariant over the equivalence class

```text
[(F,E)]_W = { (cF, E/c) : c(z)>0 }.
```

In particular,

```text
Phi(F_c E_c) = Phi(W)
```

for every net-only operator `Phi`, and for every threshold `t`,

```text
Omega_t(F_c,E_c) = Omega_t(F,E).
```

### Consequence

> Complete net-response information, including every threshold geometry derived from it, contains no data-based information about how the observed product is allocated between the latent channels.

This is structural non-identification, not low statistical power. External biological restrictions can of course distinguish members of the equivalence class; the claim is specifically that those restrictions are not supplied by a net-only observation.

A before/after special case follows immediately. For any positive multiplier `a(z)`,

```text
P_F: (F_1,E_1) = (aF_0,E_0)
P_E: (F_1,E_1) = (F_0,aE_0)
```

produce exactly the same `W_1=aF_0E_0`, and hence every `Phi(W_1)` is identical under the two distinct channel-change programs.

---

## 3. Theorem N2 — one resolved channel plus net performance is sufficient

If `W_i` and one positive mathematical channel are observed, the other is uniquely recovered by division. For example,

```text
E_i(z) = W_i(z) / F_i(z),
```

and symmetrically

```text
F_i(z) = W_i(z) / E_i(z).
```

Therefore the before/after ratios

```text
rho_F = F_1/F_0
rho_E = E_1/E_0
```

are point identified from net performance plus one resolved channel. Mixed changes are allowed; no exclusive-change assumption is required.

### Design Rule 1 — anchor and transport

> Directly measure at least one latent channel in an anchor regime. This estimates the local mapping between an empirical proxy and the mathematical channel. For every comparison regime, either revalidate that mapping directly or prespecify an admissible between-regime calibration-drift set and report the resulting identified interval and breakdown point.

Thus N2 is not a license to measure a channel once and transport its empirical proxy conversion without qualification. The operational cases are:

```text
W + direct channel in each regime
    -> point identification (N2)

anchor calibration + justified stable proxy conversion
    -> point identification of relative change (N3)

anchor calibration + bounded conversion drift
    -> partial identification + breakdown point (N3b)

proxy comparison + unrestricted conversion drift
    -> no directional identification (N4)
```

The proxy results are proved in `docs/proxy_calibration_theorem.md`.

---

## 4. What follows for trait-space studies

Observed contraction, shift, fragmentation or persistence can be biologically informative without being a unique channel fingerprint. A net-only observation might include a full trait-specific performance curve, a distribution of viable phenotypes, a threshold boundary, mean reproductive output or a declared persistence score. If the quantity depends only on `W=FE`, N1 applies regardless of how finely that net response is measured.

The practical implication is not “measure everything.” It is “measure one channel in a way whose cross-regime mapping is either validated or sensitivity-bounded.” That is the smallest observation design that breaks the equivalence class under the declared two-factor model.

---

## 5. Relation to RACH

N1-N4 define an information boundary before RACH is run. RACH should not be presented as a way to defeat an algebraically non-identifying observation. Its role is downstream:

1. declare which mechanism programs remain admissible under the available observation map;
2. retain unresolved programs rather than forcing a winner;
3. identify which additional measurement would separate them;
4. apply Design Rule 1 when that measurement is a channel proxy.

The information-theoretic NOV score is therefore a subordinate observation-selection device inside the boundary established by N1-N4, not a competing headline result.

---

## 6. Scope

- The factorisation is positive and multiplicative.
- The result applies to any trait domain; one-dimensional geometry is only a convenient representation.
- Other model structures can introduce identifying information, but that information must be stated explicitly rather than attributed to net geometry alone.
- N1 is a statement about information in the declared observation map, not a claim that the underlying biological channels are interchangeable.
