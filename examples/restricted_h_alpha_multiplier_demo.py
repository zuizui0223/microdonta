"""Demonstrate a conditional expected H-alpha contraction certificate."""
from causal_model.multipatch_criticality_dynamics import DynamicsParameters
from causal_model.restricted_h_alpha_multiplier_theory import restricted_h_alpha_multiplier


def main() -> None:
    parameters = DynamicsParameters(
        patch_areas=(1.0, 1.0),
        high_base=2.0,
        high_interaction_benefit=0.0,
        viability_threshold=1.0,
        selection_strength=0.5,
        effective_fraction=1.0,
        migration_rate=0.8,
    )
    certificate = restricted_h_alpha_multiplier(
        parameters,
        allele_lower_bound=0.60,
        allele_upper_bound=0.62,
        interaction_lower_bound=0.0,
        population_upper_bound=1000,
    )
    print("Restricted H-alpha multiplier")
    print(f"  f_min: {certificate.high_allele_fitness_lower_bound:.6f}")
    print(f"  selected p_min: {certificate.selected_allele_lower_bound:.6f}")
    print(f"  lambda_bar: {certificate.expected_h_alpha_multiplier_upper_bound:.6f}")
    print(f"  contraction certified: {certificate.contraction_certified}")


if __name__ == "__main__":
    main()
