# Optional cover letter — editor-facing draft

> **Not for peer review.** Current Methods in Ecology and Evolution guidance states that covering letters are optional and should add editorially relevant information not already present in the manuscript. Replace the bracketed signature before use.

Dear Editors,

Please consider our Research Article, **“Mechanism-Resolving Observation Design: information-theoretic selection of observations under ecological mechanism ambiguity,”** for publication in *Methods in Ecology and Evolution*.

Three points may be useful for editorial assessment. First, although the submission includes open-source software, its primary contribution is a specific inferential and observation-design workflow rather than a software-only application. The paper builds on established traditions of multiple working hypotheses, model-discrimination design and value of information; it does not claim to originate those ideas. Its distinct starting point is post-data: current observations have already left a potentially non-exclusive admissible mechanism region. The method retains that region, quantifies its remaining joint mechanism ambiguity, values feasible follow-up measurements by normalized mechanism–observation mutual information, conditions the region on the realised measurement and recomputes what should be observed next. Its selection behaviour is tested in a frozen truth-peek-free simulation benchmark in which candidate information and hidden mechanism truth are known independently of the selection policy.

Second, the target is deliberately narrower than generic uncertainty or causal inference. Rejecting a null hypothesis, obtaining a close model fit, increasing replication and identifying an intervention contrast can each be scientifically valuable without uniquely resolving mechanism identity. Likewise, pre-data multiple-working-hypotheses workflows can identify degeneracy before data collection. MROD addresses the later question of what to observe after the current evidence has already produced a residual joint mechanism set. A structural redundancy condition can rule out observations already determined by the current evidence, but structural novelty is not enough: a new measurement can still vary only with nuisance parameters, so the publication-level criterion remains mechanism–observation mutual information.

Third, a separate conceptual Perspective on mechanistic-evidence and identification boundaries has been developed as an independent project. It diagnoses structural observation limits but does not contain this submission’s primary method, frozen observation-selection benchmark or software-validation claim, and it is not used as evidence for the present Research Article. For peer review, we have also prepared a double-anonymous executable code bundle generated and self-tested from the validated submission freeze.

Thank you for considering the manuscript.

Sincerely,

[Corresponding author]
