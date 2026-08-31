# Mechanistic evidence needs an identification axis

Status: normative conceptual framing for the boundary paper.

## Core distinction

Ecological work uses *mechanistic* in more than one legitimate sense. Genomic, molecular and physiological measurements can be close to biological machinery and therefore mechanistically proximal. A different question is whether an observation distinguishes the competing mechanisms relevant to a particular claim.

The boundary paper separates these properties:

```text
biological proximity to a mechanism  !=  identification of a mechanism
```

A molecular or genomic observation can be close to the machinery of a process yet remain compatible with several competing causal mechanisms. Conversely, a field-level observation can be strong mechanistic evidence if, relative to explicit alternatives, it excludes mechanisms or sharply contracts the admissible mechanism set.

The governing sentence is:

> Mechanistic evidence should be classified partly by what it identifies, not by biological measurement level alone.

A compact equivalent is:

> Measurement level and identification strength are distinct properties of ecological evidence.

## Replace one ranking with two distinct axes

Do not claim that ecology has formally adopted a universal hierarchy from field pattern to molecular mechanism. The safer observation is that biological depth and mechanistic strength are often discussed together, while their inferential roles are not the same.

Use two axes:

```text
Axis 1: biological measurement level / mechanistic proximity
Axis 2: identification strength
        non-identifying -> partially identifying -> point-identifying
```

No monotone relation between these axes is assumed.

Examples:

- a high-dimensional gene-expression profile shared by several candidate mechanisms can be biologically proximal but non-identifying;
- a direct molecular intervention or measurement that uniquely separates declared alternatives can be both proximal and strongly identifying;
- a net field pattern such as total effective service can be distal and non-identifying;
- a simple field measurement of a missing channel can be distal but highly identifying because it collapses an equivalence dimension.

The labels "distal" and "proximal" describe where a measurement sits in a biological chain. The labels "non-identifying", "partially identifying" and "point-identifying" describe what inference the observation map supports. They answer different questions.

## What the current theorems establish

The multiplicative-chain and proxy-calibration results are not the whole conceptual claim; they are worked identification theorems that make the distinction exact in a recurring ecological architecture.

For

```text
W = prod_j F_j,
```

endpoint-only measurement leaves a `k-1` dimensional equivalence class. This remains true no matter how precise or technologically sophisticated the measurement of `W` is. Identification changes only when the observation map changes, for example through direct channel anchors.

For

```text
X_i = q_i F_i,
```

a proxy can be biologically close to `F` yet fail to identify its relative change when `q_1/q_0` is unrestricted. Finite transport information yields a sharp identified set; direct calibration can restore point identification.

These examples support a broader evidentiary principle without claiming a theorem for every possible ecological observation map.

## Scope guard

Do not write:

- molecular data are not mechanistic;
- genomics cannot identify mechanisms;
- field observations are as mechanistic as molecular measurements in general;
- biological scale is irrelevant;
- ecology explicitly endorses one universal pattern-to-molecule hierarchy;
- measurement level and identification strength are statistically independent.

Write instead:

- molecular and genomic measurements can provide mechanistic proximity, causal perturbations and strong biological constraints;
- none of those properties alone guarantees identification among the particular competing mechanisms under study;
- field observations need not remain merely descriptive when they are selected or designed to discriminate explicit alternatives;
- the evidentiary status of a measurement is conditional on the candidate mechanism set and observation map;
- the two axes are distinct, but they may be correlated in particular research programmes.

## Consequence for Paper A

Paper A should be framed as a Perspective on ecological evidence, with the product/proxy theorems as the quantitative demonstration:

```text
measurement level is not identification strength
-> net-only equivalence
-> k-1-r channel-anchor rule
-> proxy transport family
-> breakdown analysis
-> design and reporting rules
```

The main question is no longer only "when does a product hide its factors?" It is:

> When does an ecological observation discriminate among explicit mechanisms rather than only characterise a pattern or net effect?

## Boundary with Paper B / RACH

The two papers remain separate.

Paper A asks:

```text
What can the current observation map identify in principle?
```

Paper B / RACH asks:

```text
Given explicit competing mechanisms and candidate observations, which observation should be acquired next to reduce mechanism ambiguity?
```

The conceptual handoff is real, but RACH, NOV and RACH-SEQ remain non-headline and non-required for Paper A.

## Literature positioning

The literature is supportive but should be used without caricature.

- Ungerer, Johnson & Herman (2008) define ecological genomics around genetic mechanisms in natural environments, establishing the legitimacy of the mechanistic-proximity axis.
- Rudman et al. (2018) argue that genomic data can deepen mechanistic understanding while explicitly noting that genomic data alone are not sufficient to resolve the eco-evolutionary questions they discuss.
- Grace et al. (2025) distinguish causal-effect estimation from mechanistic investigation and emphasise different evidentiary requirements.
- Correia, Dee & Ferraro (2025) show that inference about intermediary ecological processes requires explicit definitions, assumptions, design and sensitivity analysis.
- Smith et al. (2020) show that field experiments can reveal mechanistic drivers under natural conditions, demonstrating that field-level evidence is not intrinsically restricted to pattern description.
- Siegel & Dee (2025) reinforce the broader design-first point that observational ecological data can support causal inference when the target and assumptions are explicit.

The paper therefore does not attack molecular ecology. It formalises a missing distinction within a broader mechanistic aspiration: proximity to machinery is one source of mechanistic insight; identification among alternatives is another.

See `paper/mechanistic_evidence_literature_audit.md` for the source-by-source claim audit and submission stop conditions.
