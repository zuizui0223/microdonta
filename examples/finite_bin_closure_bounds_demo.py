"""Demonstrate L4 ingredients derived from a declared finite-bin region."""
from causal_model.finite_bin_closure_bounds import (
    InvariantRegion,
    finite_bin_closure_bound_certificate,
)
from causal_model.multipatch_criticality_dynamics import DynamicsParameters


def main() -> None:
    parameters = DynamicsParameters(
        patch_areas=(1.0,),
        trait_occupancy_mode="finite_trait_bin_recruitment",
        genotype_trait_recruitment="two_kernel_recruitment",
        inheritance_weight=0.5,
        trait_grid_size=21,
    )
    region = InvariantRegion(
        interaction_lower_bound=0.4,
        allele_frequency_lower_bound=0.4,
        resident_high_trait_mass_lower_bound=0.2,
        population_lower_bound=10,
        population_upper_bound=20,
        next_interaction_lower_bound=0.3,
        selected_allele_frequency_lower_bound=0.2,
    )
    certificate = finite_bin_closure_bound_certificate(
        parameters,
        patch_area=1.0,
        region=region,
        pre_sampling_diversity_expansion_upper_bound=0.9,
    )
    print("Finite-bin closure bound certificate")
    print(f"  pi_min: {certificate.trait_recruitment.selected_high_trait_probability_lower_bound:.6f}")
    print(f"  n_min: {certificate.cohort_size.next_population_lower_bound}")
    print(f"  lambda_bar upper bound: {certificate.sampling.combined_diversity_multiplier_upper_bound:.6f}")
    print(f"  L4-ready under declared region: {certificate.l4_ready}")


if __name__ == "__main__":
    main()
