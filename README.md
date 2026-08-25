# RACH: Causal Admissibility and Degeneracy Framework

[![CI](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml/badge.svg)](https://github.com/zuizui0223/microdonta/actions/workflows/ci.yml)

## Canonical publication path

The active submission is the MEE methods paper defined in [`paper/README.md`](paper/README.md). Its theorem-first spine is:

```text
N1–N4
→ RACH
→ NOV / RACH-SEQ
→ controlled benchmarks
→ exact one-step projection
→ prospective observation design
```

The machine-readable paper boundary is [`paper/submission_manifest.json`](paper/submission_manifest.json). The broader repository-program boundary is defined in [`repository_programs.json`](repository_programs.json) and [`docs/repository_map.md`](docs/repository_map.md).

Run these checks before manuscript or repository-structure changes:

```bash
python paper/check_submission_bundle.py
python scripts/check_repository_boundaries.py
pytest -q
```

## What RACH is

**RACH** means **Restricted Admissible Causal Hypotheses**. It retains every causal explanation that remains compatible with a declared model family, biological constraints and observed pattern, then identifies what is still unresolved and what observation would reduce that uncertainty.

```text
A_epsilon(y_obs, x_obs)
= { (theta, s) in Theta x S :
    G(theta) = 1
    and d(P_sim(f(x_obs; theta, s)), P_obs(y_obs)) <= epsilon
  }
```

RACH is not a best-model selector and does not convert simulation compatibility into empirical proof.

## Mathematical identifiability boundary

The theorem layer starts from a positive factorisation:

```text
W(z) = F(z) E(z)
```

where `F` is a local fecundity/survival channel and `E` is an establishment/reachability channel.

### N1 — net-only observations are structurally non-identifying

For any positive trait-dependent multiplier `a(z)`, both

```text
(F, E) -> (aF, E)
(F, E) -> (F, aE)
```

produce the same net performance. Observations that depend only on `W` therefore cannot generally identify which vital-rate channel changed.

### N2 — net performance plus one exact channel is sufficient

With positive factors, observing `W` and either one factor reconstructs the other:

```text
E = W / F
F = W / E
```

### N3/N4 — proxies require calibration

For a proxy `X_i(z)=q_i(z)F_i(z)`, relative channel change is identified only when the proxy conversion is stable or independently calibrated. A visit count, pollen-load index or connectivity index is not automatically a direct channel measurement.

## Exact life-cycle bridge

The repository exposes an exact one-step expected retained juvenile-recruitment factorisation:

```text
W_recruit(z) = F_local(z) E_settlement(z)

F_local = survival_probability * conception_probability
E_settlement = (1-extinction_rate)
               * [dispersal_probability * connectivity * expected_target_room
                  + (1-dispersal_probability) * local_room]
```

This exact bridge does not automatically extend to multistep `lambda`, population persistence or endpoint trait-space geometry. Applicability is tracked in `causal_model.theorem_projection_ledger`.

## Standalone island-pollination empirical programme

microdonta owns a separate empirical observation-design programme under:

[`examples/island_pollination_empirical_tracks/`](examples/island_pollination_empirical_tracks/)

It is **not a companion or validation layer for another paper or repository**. Its three independent tracks are:

| Track | Target | RACH role |
|---|---|---|
| signed functional starting position | `signed_position = plant_trait - pollinator_functional_center`, fixed before outcome inspection | next observation + proxy calibration |
| network context → effective service | `effective_service = sum_k(visitor_rate_k * direct_effectiveness_k)` | channel measurement + proxy calibration |
| complete causal chain | pollinator change → service → dependency/assurance → response | RACH-SEQ observation package |

Readiness is conjunctive. Unsigned matching cannot replace signed position; visitor rate, identity, richness or network degree cannot replace direct effectiveness; and a missing causal link cannot be inferred from neighbouring observations.

The programme has no external manuscript dependency and no external repository dependency. Its state and completion rules are governed entirely inside microdonta.

## Repository structure

```text
causal_model/
  causal_admissibility.py
  causal_replaceability.py
  rach_seq.py
  abm_family_adapter.py
  channel_identifiability_theory.py
  proxy_calibration_theory.py
  theorem_projection_ledger.py
  colonization_recruitment_factorization.py
  spatial_metapopulation_abm.py
  defense_metapopulation_abm.py
  colonization_metapopulation_abm.py
  campanula_real_data.py

paper/                                  canonical MEE submission workspace
attraction_trait_model/                 optional simulator backend
apps/                                   interactive applications; not evidence

examples/
  channel_identifiability_demo.py
  proxy_calibration_demo.py
  spatial_metapopulation_demo.py
  endpoint_sensitivity_report.py
  campanula_izu/                        prospective observation-design example
  island_pollination_empirical_tracks/  standalone empirical programme
```

## Campanula microdonta empirical layer

The Campanula workflow separates published observations from planned field data and theory-derived predictions. Existing patterns do not by themselves provide trait-specific total performance `W`, an explicit `F/E` factorisation, and a direct channel or stably calibrated proxy. Their correct role is therefore to retain competing explanations and specify the missing next observation.

```bash
python -m causal_model.campanula_real_data
```

## Rule-transition ABMs

The ABM layer asks a conditional question: after an ecological relation changes, how does the set of trait values able to invade and persist change?

```text
Omega_inv(Z*) = { z' : lambda(z' | Z*) > 0 }
```

The current mechanistically distinct backends include fecundity-mediated pollination loss, survival-mediated predator loss and establishment-mediated connectivity loss. Endpoint claims remain conditional on the declared model family, stationarity criterion, sampled region and acceptance rule.

Program assumptions and simulated outcomes are kept separate. Outcome labels such as trait-space contraction or shift are derived from simulator metadata and are never treated as fixed assumptions.

## Pattern-oriented modelling and classification

A run is accepted only when its multivariate POM is within the declared tolerance and its focal endpoint satisfies the backend criterion. Sweep records are classified as:

```text
robust
fragile
rejected
insufficient
```

`no_common_rule` is a valid result when robust systems do not share a supported minimal causal clause.

## Running the repository

```bash
pip install -e ".[dev]"
python scripts/check_repository_boundaries.py
pytest -q

python -m examples.channel_identifiability_demo
python -m examples.proxy_calibration_demo
python -m examples.spatial_metapopulation_demo
python -m examples.rule_transition_demo
```

## Documentation

- `paper/README.md` — canonical MEE submission
- `docs/repository_map.md` — physical and program boundaries
- `docs/publication_claim_graph.md` — claim–evidence graph
- `docs/channel_identifiability_theorem.md` — N1/N2
- `docs/proxy_calibration_theorem.md` — N3/N4
- `docs/colonization_recruitment_factorization.md` — exact life-cycle bridge
- `docs/theorem_projection_ledger.md` — theorem applicability
- `docs/rule_transition_hardening.md` — provenance and intervention boundaries
- `examples/island_pollination_empirical_tracks/README.md` — standalone island-pollination empirical programme

## Interpretation boundary

Results must be reported at their actual layer:

> **Theorem layer:** identification or non-identification follows under the stated factorisation and observation map.
>
> **ABM layer:** causal programmes remain compatible within a specified simulator family and acceptance design.
>
> **Empirical layer:** a causal channel claim requires measurements that satisfy the declared mapping and calibration conditions; otherwise the output is a next-observation design rather than empirical identification.
