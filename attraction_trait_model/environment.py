"""Environment definitions for attraction-trait simulations."""

from dataclasses import dataclass


@dataclass
class Environment:
    """Population or island environment used by the generative model.

    Pollinator variables capture three distinct functional roles:

    primary_pollinator_frequency
        Frequency of the *trait-responsive, high-efficiency* pollinator guild
        in the local community.  These pollinators strongly track floral
        attraction traits (nectar guides, flower size) and have high per-visit
        pollen-transfer efficiency.  In the Izu Island system this corresponds
        to Bombus (bumblebees).

    background_pollinator_frequency
        Frequency of the *trait-non-responsive, lower-efficiency* pollinator
        guild.  These pollinators contribute to outcrossing but are largely
        independent of floral attraction traits.  Flower *size* may still
        affect their physical access, but guide expression has minimal
        influence.  In the Izu system this corresponds to halictid bees.

    community_pollinator_abundance
        Overall pollinator activity level / community richness.  Acts as a
        multiplicative scalar on both pollinator channels.  Encodes landscape-
        scale variation in pollinator service (e.g. total insect abundance,
        habitat quality, floral resource competition) that is independent of
        which functional types are present.

    effective_population_size
        Proxy for effective population size, normalised to [0, 1].
        Pass -1.0 (the default) to derive this automatically from
        ``island_distance`` via the fitted relationship:
            Ne_proxy ≈ 1.0 − 0.765 × isolation  (R²=0.93)
        Ecological rationale: Ne decreases with isolation because smaller,
        more isolated islands support smaller populations and receive less
        demographic rescue via gene flow.  Ne is a consequence of isolation,
        not an independent variable.  Pass an explicit value ≥ 0 only when
        you need to override the derived value (backward compatibility).

    Values can start as ordinal or literature-derived proxies and later be
    replaced by field estimates.  They are environmental conditions, not
    latent trade-off parameters.
    """

    name: str
    primary_pollinator_frequency: float    # trait-responsive, high-efficiency guild
    background_pollinator_frequency: float  # trait-non-responsive, lower-efficiency guild
    community_pollinator_abundance: float   # overall pollinator activity scalar
    migration_rate: float
    island_distance: float = 0.0
    effective_population_size: float = -1.0  # -1 = derive from island_distance
    ne_isolation_slope: float = 0.765        # θ: inferred slope; default=0.765 (Izu fit)

    def __post_init__(self) -> None:
        """Derive effective_population_size from island_distance if not explicitly set.

        Epistemic taxonomy
        ------------------
        DIRECTION (普遍的原理 — universal ecological principle):
            Ne decreases with isolation.  Applies to all island populations:
            more isolated islands are smaller and receive less gene flow.
            This is a general biogeographic principle, not system-specific.
            The sign of the relationship is fixed (always negative).

        COEFFICIENT ne_isolation_slope (推論対象 θ — latent parameter):
            The linear slope is a LATENT PARAMETER inferred via ABC.
            The default value 0.765 is fitted to Izu Island data (R²=0.93)
            and serves as the centre of the prior, but is NOT treated as a
            known constant.  Pass an explicit slope when constructing the
            Environment during simulation to propagate θ correctly.

        Formula:
            Ne_proxy = max(0.05, 1.0 − ne_isolation_slope × island_distance)

        Mathematical note:
            ne_isolation_slope must be positive (direction principle) and
            bounded above so Ne_proxy stays in (0, 1].  Prior range is
            enforced in parameter_constraints.py (C5_ne_slope_direction).
        """
        if self.effective_population_size < 0:
            self.effective_population_size = max(
                0.05, 1.0 - self.ne_isolation_slope * self.island_distance
            )
