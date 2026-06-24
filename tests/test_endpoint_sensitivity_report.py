from causal_model.abm_family_adapter import RobustnessPolicy, SweepRecord
from examples.endpoint_sensitivity_report import _reference_benchmark


def test_reference_benchmark_records_an_unsupported_setting_instead_of_crashing():
    records = (
        SweepRecord(
            scenario="pollination_loss",
            program_id="fecundity_reward",
            motifs=frozenset({"relation_change"}),
            pattern_matched=False,
            metadata={"P_sim": {}},
            region_id="eco_0",
            seed=0,
        ),
        SweepRecord(
            scenario="pollination_loss",
            program_id="fecundity_reward",
            motifs=frozenset({"relation_change"}),
            pattern_matched=False,
            metadata={"P_sim": {}},
            region_id="eco_1",
            seed=1,
        ),
    )
    report = _reference_benchmark(
        records,
        RobustnessPolicy(min_replicates=2, min_match_fraction=0.5, fragile_max_fraction=0.1),
    )
    assert report["status"] == "no_admissible_program_at_reference_setting"
    assert report["n_matches"] == 0
