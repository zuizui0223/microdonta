"""Demonstrate a high-probability H-alpha lead certificate."""
from eco_genetic_criticality.probabilistic_h_alpha_lead_theory import (
    finite_bin_h_alpha_lead_certificate,
)


def main() -> None:
    trait, lead = finite_bin_h_alpha_lead_certificate(
        initial_diversity=0.8,
        warning_threshold=0.5,
        multiplier_upper_bound=0.5,
        time=2,
        cohort_size_lower_bound=100,
        high_trait_recruit_probability_lower_bound=0.5,
        occupancy_threshold=20,
    )
    print("Finite-bin trait persistence bound")
    print(f"  E[N_H] lower bound: {trait.expected_high_trait_abundance_lower_bound:.3f}")
    print(f"  one-generation trait-loss risk upper bound: {trait.per_generation_failure_upper_bound:.6f}")
    print("Probabilistic H-alpha lead certificate")
    print(f"  time: {lead.time}")
    print(f"  E[H_t] upper bound: {lead.expected_diversity_upper_bound:.3f}")
    print(f"  P(H_t > warning) upper bound: {lead.diversity_warning_failure_upper_bound:.3f}")
    print(f"  P(trait loss by t) upper bound: {lead.trait_persistence_failure_upper_bound:.6f}")
    print(f"  P(tau_H <= t < tau_trait) lower bound: {lead.lead_probability_lower_bound:.3f}")


if __name__ == "__main__":
    main()
