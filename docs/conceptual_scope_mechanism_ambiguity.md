# Mechanism ambiguity: conceptual scope of MROD

Mechanism-Resolving Observation Design (MROD) starts after a declared set of mechanisms has been confronted with the current observation set and more than one explanation remains admissible. Its target is the residual ambiguity among those explanations and the value of candidate observations for reducing it.

This is a narrower object than generic uncertainty.

## Not the same as null-hypothesis testing

A null test asks whether one designated null statement is compatible with the data. MROD asks which distinctions among the still-admissible mechanism programs remain unresolved.

Rejecting a null can leave many non-null mechanisms compatible with the same observations. Conversely, a null mechanism can simply be one member of the declared mechanism vocabulary and remain inside the admissible region when the data do not separate it.

```text
reject H0  !=  resolve mechanism identity
```

MROD is therefore not a replacement significance test.

## Not the same as residual error or goodness of fit

The admissible region is defined by a declared discrepancy/tolerance rule, but the scientific object after acceptance is the multiplicity of compatible mechanism programs. Two programs can both match the observed targets exactly and still differ in mechanism identity.

```text
low discrepancy  !=  low mechanism ambiguity
```

`Residual mechanism entropy` means ambiguity left inside the accepted mechanism region. It is not a regression residual, unexplained variance or model error term.

## Not the same as sampling uncertainty

More replication can reduce sampling uncertainty and can make approximately different predictions distinguishable. But if the current observation map is structurally invariant across two mechanisms, repeating the same observation type does not create a new mechanism distinction.

MROD therefore treats `more data` and `a more discriminating observation` as different design moves.

## Not the same as counterfactual causal identification

MROD's primary singleton quantity

```text
V(Q) = I(S; Q | A_epsilon) / K
```

is a preposterior information quantity about mechanism identity inside the declared admissible region. It is not, by itself, an average treatment effect, potential outcome, do-intervention estimand or mediation effect.

A candidate observation can be observational, experimental, molecular, demographic or otherwise; what matters for MROD is whether its predictive outcome partition separates the mechanisms that remain admissible. If the scientific question requires a causal intervention estimand, the assumptions needed to identify that estimand still apply.

Likewise, a joint candidate vector is not automatically licensed by stacking singleton predictions from mutually incompatible interventions or destructive measurements. When an earlier acquisition changes the distribution of a later one, an order-specific transition or potential-outcome model is required before sequence-level information is interpreted.

## Relationship to Boundary

The separate `boundary` project characterizes what a current observation map can identify in principle and, for restricted exact classes, when adding an observation changes structural identification. MROD takes the unresolved distinctions as a design object and ranks feasible future observations by expected information gain.

```text
Boundary:
current observation map
-> identified/equivalence set
-> unresolved mechanism distinctions

MROD:
unresolved distinctions + candidate measurements
-> information value
-> next observation
```

The interface is deliberately asymmetric. Boundary does not need to run MROD to state an identification limit. MROD does not claim that its entropy or information score creates causal truth beyond the declared mechanism and predictive families.

## Mechanistic depth is not the objective

A measurement closer to molecular machinery is not automatically more mechanism-resolving. A field-level observation can be more useful when competing mechanisms predict different field outcomes, while a proximal measurement can be shared downstream by several explanations.

The design target is therefore not `deepest available measurement` but `measurement that best separates the unresolved mechanisms relevant to the question`.

## Limitation-to-design translation

A useful ecological limitation statement can be converted into an MROD problem only after its logical status is made explicit:

```text
which mechanisms remain compatible?
-> which distinctions among them are unresolved?
-> which feasible singleton candidate observations have identified predictive partitions?
-> if some declared candidate values are non-estimable, report prediction limitation
-> if a positive singleton value exists, choose a highest-current-value immediate observation
-> if every declared singleton is estimable but every V(Q)=0, report a validated one-step information stop
-> do not call that one-step stop a sequence-level impossibility without a coherent joint candidate audit
-> if a licensed joint vector Q_C has I(S;Q_C|A_epsilon)=0, report a sequence-information limit relative to that declared candidate vocabulary
-> if singleton values are zero but joint information is positive, move to a non-myopic/bundle/sequence-design problem rather than discarding the measurement vocabulary
```

These states imply different next actions. Prediction limitation calls for a better candidate-outcome model. A one-step zero state calls for checking complementary or bundle information before declaring impossibility. A genuine coherent-joint zero result calls for changing the declared measurement vocabulary. Budget exhaustion remains a separate resource constraint.

This turns `future work should collect more data` into a conditional observation decision without pretending that every limitation is resolvable by the current greedy rule or by available measurements.
