# Figure 1 observation-information freeze

This note records the post-rename correction to the controlled Figure 1 generator.

## Scientific correction

Panel C reports the canonical observation information value

\[
V(Q)=I(S;Q\mid A_\epsilon)/K,
\]

not the retired heuristic expected-resolvability ranking.

For each displayed quantitative candidate, the median prediction under the current admissible mechanism region is fixed **before** an outcome is observed. The declared outcomes are `at_or_below` and `above` that threshold, so they form a disjoint and exhaustive partition whenever every accepted row has a finite prediction. The empirical joint distribution of residual mechanism state and declared outcome then gives the displayed mutual information. Missing or non-finite predictions make the candidate non-estimable; no fallback score is relabelled as information value.

Controlled hidden truth is used only after candidate ranking to materialise the panel-D resolution check. It never enters the panel-C thresholds or ranking.

## Scope

This correction changes Figure 1 presentation and the calculation behind its candidate-ranking panel. It does not alter the frozen G2 protocol, G2 numerical results, observation-information definition, sequential policy or manuscript headline claims.

The next `[g5-final] [reviewer-bundle]` freeze must rebuild Figure 1, the renamed wheel and the anonymous reviewer archive from one exact main commit before release-readiness hashes are considered current.
