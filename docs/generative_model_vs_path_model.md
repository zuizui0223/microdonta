# Generative Model vs Path Model

This repository is designed to go beyond statistical path comparison.

## Short Distinction

```text
island = statistical path comparison
microdonta = causal mechanism generation
```

The `island` analysis asks which observed statistical pathway is supported by
island-scale data. A typical model compares associations such as:

```text
distance -> Bombus unsuitability -> self-compatibility -> floral simplification
```

or partial mediation:

```text
Bombus unsuitability -> floral simplification
Bombus unsuitability -> self-compatibility -> floral simplification
```

That is an observational path-model question.

The target for `microdonta` is different. It asks whether a proposed causal
mechanism can generate observed ecological, reproductive, and genetic patterns
through individual-level processes:

```text
candidate causal pathway
+ hidden benefit/cost/fitness parameters
+ individual-level reproduction and inheritance
-> generated ecological / reproductive / genetic patterns
-> comparison with observed patterns
```

## Why This Is Not Just SEM or a Path Model

A path model can estimate whether observed variables covary in a way that is
consistent with direct, mediated, or partial mediation pathways. It does not by
itself show that the pathway can generate next-generation trait states through
fitness, reproduction, inheritance, and drift.

`microdonta` treats candidate causal hypotheses as mechanisms. Each hypothesis
is translated into pathway switches that control how the biological generator
uses latent benefits, costs, and fitness components.

For example:

```text
Bombus loss
-> outcrossing opportunity declines
-> selfing increases
-> outcrossing-signal benefit declines
-> nectar-guide maintenance becomes disadvantageous
-> next generations show guide reduction, high selfing, low herkogamy, and high Fis
```

This is a generative causal model, not only a comparison of observed paths.

## Three Layers

```text
1. causal_model/
   defines causal hypotheses and pathway switches

2. attraction_trait_model/
   generates biological outcomes using reproduction, fitness, inheritance, and drift

3. constraint_abm/
   compares generated outputs with observed field/literature patterns
```

## Pathway Switches

Pathway switches are the bridge from causal hypothesis to model mechanics. They
state which mechanism is active, and with what strength:

- `direct_pollinator_to_guide`
- `selfing_mediation`
- `island_common_cause`
- `drift_null`
- `small_pollinator_pathway`

The initial implementation uses 0/1 or weak/strong defaults. Later versions can
make these continuous parameters that are filtered by CAPOM pattern matching.

## Manuscript Framing

Whereas the island-scale path models compare statistical associations among
observed variables, the microdonta model asks whether alternative causal
mechanisms can generate the observed pattern through individual-level
reproduction, fitness, inheritance, and drift. The central innovation is the
explicit translation of causal hypotheses into pathway switches that control
hidden benefits, costs, and fitness components in a generative population model.

Japanese:

island解析が観察変数間の統計的経路を比較するのに対し、microdontaモデルは、
候補因果メカニズムが個体レベルの繁殖・適応度・遺伝・漂流を通じて観察パターンを
生成できるかを検証する。中心的な新規性は、因果仮説を経路スイッチとして明示し、
それによって観察困難な利益・コスト・適応度成分を制御する生成個体群モデルへ
変換する点にある。
