# Primary-literature audit: multiplicative ecological measurement architectures

## Purpose

This audit addresses a specific reviewer objection: `W=FE` is not introduced as an idiosyncratic biological law of this paper. Closely related multiplicative measurement architectures are already used in ecology to combine an interaction quantity with a per-event or conditional quality term. The N1-N4 results audit the information consequences of that recurring architecture.

This file is separate from `campanula_primary_literature_audit.md`, which has a taxonomic and historical worked-example role.

## Audit rule

For each source we record only claims directly supported by the primary paper or publisher full text. The manuscript should say that the **measurement architecture recurs**, not that all sources use identical biological factors or symbols.

| Domain | Primary source | Explicit architecture | What behaves like quantity/proxy | What behaves like conditional quality | Relevance to N1-N4 |
|---|---|---|---|---|---|
| Pollinator effectiveness in crops | Rader et al. 2012, *Journal of Applied Ecology*, doi:10.1111/j.1365-2664.2011.02066.x | Overall pollinator effectiveness is defined as the product of pollen-transfer efficiency and visitation frequency. Pollen-transfer efficiency itself combines pollen deposited with successful stigma contact; visitation frequency combines abundance and flower visits per unit time. | visitation frequency | pollen-transfer efficiency per visit/contact | A change in visitor composition, handling or stigma contact can alter conversion from visits to realised service across regimes. |
| Community pollinator importance | Ballantyne et al. 2017, *Scientific Reports* 7:8383, doi:10.1038/s41598-017-08798-x | Pollinator importance is the product of visitation frequency and pollinator effectiveness measured by single-visit pollen deposition. | visitation frequency | single-visit pollen deposition | A visitation-only comparison is a proxy comparison; stability of per-visit effectiveness is an identifying assumption. |
| Pollinator importance as an estimand | Reynolds & Fenster 2008, *Oecologia* 156:325-332, doi:10.1007/s00442-008-0982-5 | The abstract explicitly defines pollinator importance as the product of visitation rate and pollinator effectiveness. | visitation rate | pollinator effectiveness | Demonstrates that the multiplicative form is an established estimand, not a construction invented for RACH. |
| Seed dispersal effectiveness | Schupp, Jordano & Gómez 2010, *New Phytologist* 188:333-353, doi:10.1111/j.1469-8137.2010.03402.x | Section IV / Fig. 2 defines seed dispersal effectiveness as `SDE = Quantity × Quality`: number of seeds dispersed by an agent multiplied by the probability that a dispersed seed produces a new adult. Quantity further contains visits × seeds dispersed per visit; quality contains post-handling and post-deposition survival/recruitment probabilities. | number of seeds dispersed / visit quantity | probability a dispersed seed yields a new adult | The paper explicitly emphasizes context dependence of quality across habitats, which is the biological analogue of regime-dependent calibration drift. |

## Source notes

### Rader et al. 2012

**Reference**: Rader, R. et al. 2012. Spatial and temporal variation in pollinator effectiveness: do unmanaged insects provide consistent pollination services to mass flowering crops? *Journal of Applied Ecology* 49. DOI `10.1111/j.1365-2664.2011.02066.x`.

**Direct support**: In the Methods subsection “Overall pollinator effectiveness,” the paper states that overall effectiveness is the product of pollen-transfer efficiency and visit frequency. This is stronger than an informal interpretation: the multiplicative structure is the reported estimand.

**N1-N4 mapping**: Visitation frequency is not sufficient by itself if pollen-transfer efficiency changes among fields, seasons or taxa. That is exactly the type of comparison in which an apparently safe relative proxy design can inherit calibration drift.

### Ballantyne et al. 2017

**Reference**: Ballantyne, G., Baldock, K.C.R., Rendell, L. & Willmer, P.G. 2017. Pollinator importance networks illustrate the crucial value of bees in a highly speciose plant community. *Scientific Reports* 7:8383. DOI `10.1038/s41598-017-08798-x`.

**Direct support**: The paper measures visitation frequency, pollen deposition ability per visit, and defines pollinator importance as their product.

**N1-N4 mapping**: The paper also asks how well visitation frequency predicts effectiveness, making the proxy issue explicit rather than hypothetical.

### Reynolds & Fenster 2008

**Reference**: Reynolds, R.J. & Fenster, C.B. 2008. Point and interval estimation of pollinator importance: a study using pollination data of *Silene caroliniana*. *Oecologia* 156:325-332. DOI `10.1007/s00442-008-0982-5`.

**Direct support**: The abstract calls pollinator importance “the product of visitation rate and pollinator effectiveness.” The statistical contribution of that paper is interval estimation for the product, confirming that this object is treated as a standard ecological quantity.

### Schupp, Jordano & Gómez 2010

**Reference**: Schupp, E.W., Jordano, P. & Gómez, J.M. 2010. Seed dispersal effectiveness revisited: a conceptual review. *New Phytologist* 188:333-353. DOI `10.1111/j.1469-8137.2010.03402.x`.

**Direct support**: Section IV and Fig. 2 state that SDE can be quantified as the number of seeds dispersed by an agent multiplied by the probability that a dispersed seed produces a new adult: `SDE = Quantity × Quality`. The figure marks several lower-level relationships with multiplication signs. The paper further documents strong context dependence of both quantity and quality among habitats.

**N1-N4 mapping**: This is especially useful for the manuscript because it shows both sides of the argument in one established framework: multiplicative decomposition is standard, and the conditional quality term can change with ecological context. N4/N3b therefore target a real transport problem rather than an artificial algebraic possibility.

## Safe manuscript synthesis

> Multiplicative quantity-by-quality decompositions are already standard in ecological measurement. Pollinator importance has repeatedly been defined as visitation frequency multiplied by per-visit effectiveness, while seed dispersal effectiveness is explicitly defined as Quantity × Quality, with quality representing the probability that a dispersed seed ultimately recruits. Our results do not propose these decompositions as new biological laws. They identify the information boundary created when one component is observed only through a proxy whose conversion may change across the comparison.

## Claims not to make

- Do not say that every ecological fitness measure is multiplicative.
- Do not say that these papers establish the exact `F` and `E` interpretation used in every RACH application.
- Do not imply that a correlation between visitation and effectiveness proves stable calibration across regimes.
- Do not use literature examples to replace system-specific validation of the biological factorisation.

## Manuscript role

Use this audit to support one compact paragraph in the Introduction/Methods. The main novelty claim remains:

1. rich net-only observation classes remain invariant under channel reallocation;
2. bounded proxy drift yields a sharp identified set and a breakdown point;
3. the boundary implies a concrete anchor-and-transport observation-design rule.
