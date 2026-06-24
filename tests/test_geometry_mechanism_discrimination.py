from causal_model.abm_family_adapter import RobustnessPolicy
from causal_model.geometry_mechanism_discrimination import (
    CoarsePOMTarget,
    run_geometry_mechanism_discrimination,
)


_POLICY = RobustnessPolicy(
    min_replicates=12,
    min_match_fraction=0.80,
    fragile_max_fraction=0.10,
)


def _report():
    return run_geometry_mechanism_discrimination(
        target=CoarsePOMTarget(),
        policy=_POLICY,
        n_regions=6,
        seeds=(0, 1),
        grid_points=101,
        base_seed=17,
    )


def test_coarse_pom_retains_all_competing_mechanisms():
    report = _report()
    assert set(report.coarse_survivors) == {
        "relationship_benefit_loss",
        "optimum_displacement",
        "connectivity_fragmentation",
        "directional_connectivity_pruning",
        "compensated_frequency_reweighting",
    }
    assert all(
        report.target.matches(trial.coarse_pom)
        for trial in report.trials
    )


def test_geometry_uniquely_identifies_shift_fragmentation_and_conserved_support():
    report = _report()
    assert report.resolution_for("shift").status == "unique"
    assert report.resolution_for("shift").survivors == ("optimum_displacement",)

    assert report.resolution_for("fragmentation").status == "unique"
    assert report.resolution_for("fragmentation").survivors == (
        "connectivity_fragmentation",
    )

    assert report.resolution_for("conserved").status == "unique"
    assert report.resolution_for("conserved").survivors == (
        "compensated_frequency_reweighting",
    )


def test_upper_edge_contraction_remains_an_explicit_nonidentifiability():
    report = _report()
    resolution = report.resolution_for("upper_edge_contraction")
    assert resolution.status == "ambiguous"
    assert set(resolution.survivors) == {
        "relationship_benefit_loss",
        "directional_connectivity_pruning",
    }


def test_geometry_labels_are_outcomes_not_program_motifs():
    report = _report()
    outcome_labels = {
        "upper_edge_contraction",
        "shift",
        "fragmentation",
        "conserved",
    }
    for trial in report.trials:
        assert trial.geometry.label in outcome_labels
        assert not (set(trial.motifs) & outcome_labels)
