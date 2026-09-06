# MROD reviewer-objection audit

Status: internal claim-ceiling document for the active Methods in Ecology and Evolution manuscript. It is not part of the anonymous scientific evidence base.

## 1. “This is just Value of Information.”

Concede the common foundation. MROD uses preposterior value-of-information logic and does not claim to invent EVSI. Applied ecological VoI such as Canessa et al. (2015) values information through downstream management actions and outcomes. MROD chooses a narrower internal target: reduction of uncertainty in a declared non-exclusive mechanism vector inside the current admissible region. The contribution must be stated as the ecological mechanism-resolution formulation, evidence-role contract, set-valued reporting and validated observation-selection workflow—not EVSI itself.

## 2. “Experimental design for model discrimination already exists.”

Yes. Classical discriminating design and Bayesian experimental design long predate MROD. Do not claim novelty for choosing experiments that separate rival models. MROD differs in its declared target: mechanisms are represented as jointly active switches rather than requiring one mutually exclusive model label, all compatible parameter–mechanism states are retained, and candidate value is measured against residual joint mechanism identity.

## 3. “Mutual information is standard.”

Yes. The identity

```text
V(Q)=I(S;Q|A_epsilon)/K
```

is not advertised as a new information-theory result. Its role is to make the publication quantity exact and auditable once the residual mechanism target and verified candidate partition have been declared.

## 4. “The admissible region is just ABC rejection.”

The computational restriction resembles ABC and the paper says so. The difference is inferential use: the full accepted parameter–mechanism region is retained as the scientific object needed to report mechanism multiplicity and evaluate future observations, rather than being used only to obtain parameter summaries or force model choice. Do not claim invention of rejection sampling.

## 5. “Why not simply report the best model?”

A modal explanation can coexist with substantial mass on observationally equivalent alternatives. MROD is designed for questions where that multiplicity is scientifically relevant. If current observations clearly separate the declared mechanisms, the admissible mechanism entropy will already be low and little observation-design problem remains.

## 6. “Boundary’s rank theorem already tells you which observation to take.”

No. In the restricted exact log-linear class, Boundary can certify that a candidate inside the current row span is structurally redundant and therefore has zero mechanism information. The converse is false: a new observation direction may partition only nuisance parameters. Rank gain is therefore a zero-value screen, not the MROD value criterion. MROD still requires `I(S;Q|A_epsilon)`.

## 7. “This is active learning.”

Active learning usually chooses cases to label so as to improve a predictive model or classifier. MROD chooses ecological measurements whose outcomes are predicted to discriminate residual mechanism programs. Both are adaptive information acquisition, so generic claims about adaptive querying are not novel. The inferential target and ecological evidence contract are the distinction.

## 8. “Your random-order baseline is weak.”

Correct, and the manuscript explicitly limits that claim. Frozen G2 validates information-guided screening against an uninformed budget allocation. A post-frozen matched `static_initial_information` comparator essentially matches adaptive recomputation on the present benchmark family. The paper therefore does not claim an empirical adaptive advantage on G2; it uses the two-step theorem to state when adaptive recomputation has strict expected value.

## 9. “Then sequential recomputation is unnecessary.”

Not universally. The theorem gives

```text
E[max_q U_q(X)] >= max_q E[U_q(X)]
```

with strict inequality exactly when no remaining candidate is optimal on every positive-probability first-outcome branch. G2 happens to lie near the equality case. Recompute by default because branch structure is not known in advance; do not claim every problem benefits empirically.

## 10. “This is counterfactual causal inference under another name.”

No. MROD’s value is information about mechanism identity inside a declared model family. It is not an ATE, potential outcome, do-intervention effect or mediation estimand. Experimental candidate observations are allowed, but any causal estimand retains its own identification assumptions. Historical switch-OFF filtering in the code is set-membership conditioning, not automatic counterfactual identification.

## 11. “Rejecting the null already establishes mechanism.”

No. Rejecting one null can leave several non-null mechanisms compatible with the same data. Conversely a null-like mechanism can remain one member of the declared vocabulary. MROD begins with the surviving mechanism set rather than treating significance as mechanism resolution.

## 12. “Better fit or more samples will solve the ambiguity.”

Sometimes more samples help, especially when mechanisms make approximately different predictions. The structural claim is narrower: precision cannot repair exact invariance of the observation map. Perfect fit can also coexist with multiple mechanism states. Do not shorten this to “more data never help.”

## 13. “Why not always measure fitness, perform interventions, or go molecular?”

Because biological depth and discriminatory value are different properties. A proximal assay can be shared downstream by several mechanisms, while a field measurement can sharply partition them. MROD does not oppose fitness, molecular or experimental data; it asks whether a feasible measurement resolves the distinction relevant to the question.

## 14. “The candidate outcome model is doing all the work.”

Candidate information is estimable only when outcomes form a verified predictive partition of the current admissible region. If the predictive map is absent or incomplete, the publication-level value is reported as non-estimable rather than replaced by a convenient declared prior. This is a limitation, not a hidden assumption to bypass.

## 15. “Your mechanism vocabulary can omit the true mechanism.”

Yes. No set-valued method can recover an undeclared mechanism solely by retaining the declared set. Admissibility and observation value are conditional on the mechanism vocabulary, prior/parameter support, constraints, observation map, discrepancy and tolerance. The paper must not call the retained set exhaustive of nature.

## 16. “Why no natural-system validation?”

The paper validates an observation-selection algorithm, not a discovered natural mechanism. Controlled systems are needed to know hidden mechanism truth, candidate information structure and whether truth was inspected before selection. A natural application can show usability and ecological plausibility but cannot reveal global optimality relative to unknown causal truth. Do not convert synthetic validation into a natural-system claim.

## 17. “Your normalization `R=1-H(S|A)/K` depends on a chosen switch vocabulary.”

Yes. `K` is the maximum entropy of the declared binary mechanism vector, not a universal ecological scale. This gives a fixed 0–1 interpretation within a declared vocabulary but does not make values directly comparable across arbitrary vocabularies without care. Prior and vocabulary sensitivity remain part of scope.

## 18. “The method could recommend an expensive observation for a tiny gain.”

The current publication quantity is information value, not net monetary utility. Costs can be added in a downstream decision layer or used as budget constraints, but the paper does not claim cost-optimal field design. Keeping mechanism information separate from monetary/management utility is deliberate and distinguishes the current target from management VoI.

## Minimum defensible contribution

Even under the strongest novelty challenge, the paper retains:

1. a reproducible set-valued ecological mechanism target rather than forced winner selection;
2. explicit separation of context, observed targets, diagnostics and future observations;
3. exact normalized mechanism–observation information for verified predictive partitions;
4. a one-way structural redundancy screen with an explicit false converse;
5. adaptive sequential recomputation with a precise two-step strict-value condition;
6. frozen controlled evidence that information-guided screening avoids mechanism-independent measurements under limited budget without hidden-truth leakage;
7. a negative stronger-comparator result that narrows the empirical adaptive claim rather than being hidden.

## Submission stop conditions

Do not submit if the manuscript says or implies that MROD invented mutual information, EVSI, Bayesian experimental design, model discrimination, active learning or structural identifiability; that rank gain guarantees positive mechanism value; that more data never help; that accepted-row switch filtering identifies intervention counterfactuals; that adaptive recomputation empirically beats static information ordering on G2; that the declared mechanism vocabulary is exhaustive of nature; or that the frozen benchmark validates a natural ecological mechanism.
