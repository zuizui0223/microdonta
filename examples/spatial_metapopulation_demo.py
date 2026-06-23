"""Spatial metapopulation rule-transition RACH demo.

Runs the *real* individual- and patch-based ABM as the rule-transition backend on
three independent relationship-change interventions — pollination loss, predation
loss, dispersal loss — and asks whether trait-space **contraction** robustly
follows the loss, across randomly drawn ecosystems, under the physical-constraint
regime (finite resources, positive trait cost, finite patches, local interaction,
incomplete compensation). A *compensated* counterexample ensemble (low trait cost,
ample dispersal, large connected patches, sufficient compensation) is included to
show when contraction does NOT occur.

Pipeline (the same one the abstract demo uses):
    spatial ABM sweep -> SweepRecord -> robust/fragile -> rule-transition invariants

Run from the repository root:
    python examples/spatial_metapopulation_demo.py
"""
from __future__ import annotations

import json
from random import Random

from causal_model.abm_family_adapter import RobustnessPolicy, summarise_sweep
from causal_model.rule_transition_invariants import explain_result
from causal_model.rule_transition_pipeline import analyse_rule_transitions
from causal_model.spatial_metapopulation_abm import (
    compensated_program_motifs,
    constraint_program_motifs,
    generate_sweep_records,
    make_interventions,
    run_intervention_experiment,
    sample_compensated_ecosystem,
    sample_constrained_ecosystem,
    verify_contraction_robustness,
)
from causal_model.spatial_metapopulation_analysis import (
    contraction_conditions_report,
    decompose_channels,
    verify_persistent_contraction,
)

# Small but real settings so the demo runs in a reasonable time.
EXP = dict(
    equilibration_steps=40, outcome_steps=12, grid_points=9,
    invasion_steps=6, invasion_cohort=12, invasion_replicates=2,
)


def _omega(ts) -> str:
    return (
        f"measure {ts.measure_before:.2f}->{ts.measure_after:.2f}  "
        f"components {ts.n_components_before}->{ts.n_components_after}  "
        f"centroid {ts.centroid_before}->{ts.centroid_after}  [{ts.primary}]"
    )


def main() -> None:
    incomplete = make_interventions(compensation=0.08)   # physical-constraint regime
    sufficient = make_interventions(compensation=0.55)   # compensated counterexample

    # ------------------------------------------------------------------ #
    # 1. One worked before/after experiment per intervention.
    # ------------------------------------------------------------------ #
    print("=== same-initial-condition before/after experiments (constrained) ===")
    rng = Random(7)
    for name, intv in incomplete.items():
        params, patches = sample_constrained_ecosystem(rng)
        res = run_intervention_experiment(params, patches, intv, seed=11, **EXP)
        print(f"\n[{name}]  resident stationarity = {res.stationarity}")
        print(f"  P_sim   = {res.p_sim}")
        print(f"  d(P_sim,P_obs) = {res.distance:.2f}  accepted(contraction) = {res.accepted}")
        print(f"  Omega_inv: {_omega(res.trait_space_change)}")

    # ------------------------------------------------------------------ #
    # 2. Robustness across random ecosystems: constrained vs compensated.
    # ------------------------------------------------------------------ #
    print("\n=== contraction robustness across random ecosystems ===")
    for name in incomplete:
        rc = verify_contraction_robustness(
            incomplete[name], ecosystem_sampler=sample_constrained_ecosystem,
            n_draws=14, base_seed=42, **EXP,
        )
        rk = verify_contraction_robustness(
            sufficient[name], ecosystem_sampler=sample_compensated_ecosystem,
            n_draws=14, base_seed=42, **EXP,
        )
        print(
            f"  {name:16s} constrained: contraction={rc.contraction_fraction:.2f} "
            f"({rc.classification}); stationarity={rc.stationarity_counts}"
        )
        print(
            f"  {'':16s} compensated: contraction={rk.contraction_fraction:.2f} "
            f"({rk.classification})  <- counterexample (no contraction)"
        )

    # ------------------------------------------------------------------ #
    # 3. Full rule-transition pipeline over the spatial ABM sweep.
    # ------------------------------------------------------------------ #
    print("\n=== rule-transition invariants from the spatial ABM sweep ===")
    records = []
    for name, intv in incomplete.items():
        records += generate_sweep_records(
            intv, program_id="physical_constraint",
            program_motifs=constraint_program_motifs(intv),
            ecosystem_sampler=sample_constrained_ecosystem,
            n_regions=6, seeds=(0, 1), base_seed=5, **EXP,
        )
        records += generate_sweep_records(
            sufficient[name], program_id="compensated",
            program_motifs=compensated_program_motifs(intv),
            ecosystem_sampler=sample_compensated_ecosystem,
            n_regions=6, seeds=(0, 1), base_seed=5, **EXP,
        )

    policy = RobustnessPolicy(min_replicates=6, min_match_fraction=0.4, fragile_max_fraction=0.15)
    print("  program classification:")
    for s in summarise_sweep(records, policy):
        print(
            f"    {s.scenario:16s} {s.program_id:18s} {s.classification:11s} "
            f"match={s.match_fraction:.2f} (n={s.n_replicates})"
        )

    analysis = analyse_rule_transitions(records, policy)
    print("\n  cross-system rule-transition invariants:")
    print(json.dumps(explain_result(analysis.invariant_result), indent=2, ensure_ascii=False))

    # ------------------------------------------------------------------ #
    # 4. Channel decomposition (causal-isolation control for peer review).
    #    Each intervention drops the trait-supporting interaction AND a
    #    secondary channel; this isolates which one actually contracts Omega_inv.
    # ------------------------------------------------------------------ #
    print("\n=== channel decomposition: which loss drives contraction? ===")
    for name in incomplete:
        dec = decompose_channels(incomplete[name], n_draws=12, base_seed=100, **EXP)
        print(
            f"  {name:16s} full={dec.full:.2f}  interaction_only={dec.interaction_only:.2f}  "
            f"secondary_only={dec.secondary_only:.2f}  (interaction is driver: {dec.interaction_is_driver})"
        )
    print("  -> trait-support (interaction) loss is the contraction driver;")
    print("     predator removal alone does not contract; dispersal cut is a separate route.")

    # ------------------------------------------------------------------ #
    # 5. Persistence after resident RE-EQUILIBRATION (not transient invasibility)
    #    and the conditions / compensation boundary.
    # ------------------------------------------------------------------ #
    print("\n=== does the contraction persist after the resident re-evolves? ===")
    reeq = dict(equilibration_steps=40, reequilibration_steps=55, grid_points=5,
                invasion_steps=4, invasion_cohort=8, invasion_replicates=1)
    pc = verify_persistent_contraction(
        incomplete["pollination_loss"], ecosystem_sampler=sample_constrained_ecosystem,
        n_draws=14, base_seed=400, **reeq)
    pk = verify_persistent_contraction(
        sufficient["pollination_loss"], ecosystem_sampler=sample_compensated_ecosystem,
        n_draws=14, base_seed=400, **reeq)
    print(f"  incomplete compensation: among re-stabilised systems contraction persists "
          f"{pc.conditional_contraction:.2f}; destabilised {pc.destabilisation_fraction:.2f} "
          f"(cats={pc.after_categories})")
    print(f"  sufficient compensation: contraction {pk.conditional_contraction:.2f}; "
          f"destabilised {pk.destabilisation_fraction:.2f}  <- stable, no contraction")

    print("\n=== contraction CONDITIONS (not a universal law) ===")
    rep = contraction_conditions_report(n_draws=14, base_seed=100, **EXP)
    print(f"  contracts when ({rep['contracts_when']['regime']}):")
    print(f"     fraction = {rep['contracts_when']['instantaneous_contraction_fraction']:.2f}")
    print(f"  does NOT contract when ({rep['does_not_contract_when']['regime']}):")
    print(f"     fraction = {rep['does_not_contract_when']['instantaneous_contraction_fraction']:.2f}")


if __name__ == "__main__":
    main()
