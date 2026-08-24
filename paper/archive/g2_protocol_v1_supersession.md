# G2 protocol v1 supersession record

`rach-g2-truth-peek-free-v1` was frozen but **never executed as the final submission benchmark**.

It is superseded before any final G2 output was inspected because static review identified a validation-design flaw: the candidate set contained only one directly resolving observation per confound and no mechanism-uninformative distractors or random-selection baseline. Under that design, a high edge-resolution rate could demonstrate that the observation vocabulary was sufficient without testing whether RACH-SEQ selected useful observations more efficiently than an uninformed policy.

The archived JSON preserves the exact v1 bytes. No v1 numerical result is eligible for the manuscript.

Protocol v2 adds, before final execution:

- two binary nuisance measurements generated independently of the mechanism vector;
- a uniform random candidate-order baseline evaluated on the same generated systems, hidden truths, candidate sets, and budgets;
- policy-level reporting and direct policy contrasts;
- no success threshold requiring RACH-SEQ to outperform random selection.

The reason for the change is therefore stronger falsifiability of the observation-selection claim, not inspection or optimisation of a benchmark result.
