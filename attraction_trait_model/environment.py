"""Environment definitions for attraction-trait simulations."""

from __future__ import annotations

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

    def __post_init__(self) -> None:
        """Derive effective_population_size from island_distance if not explicitly set.

        Epistemic taxonomy
        ------------------
        DIRECTION (普遍的原理 — universal ecological principle):
            Ne decreases with isolation.  Applies to all island populations:
            more isolated islands are smaller and receive less gene flow.
            This is a general biogeographic principle, not system-specific.

        COEFFICIENT 0.765 (観測データ — system-specific empirical input):
            The linear coefficient is fitted to Izu Island data (R²=0.93).
            It is specific to this archipelago and MUST be treated as an
            empirical input, NOT as a universal constant.
            Source: independent population census / allozyme survey data.
            If this coefficient were derived from the same neutral-diversity
            data used in observed_patterns.csv, it would create circularity
            in the neutral_diversity_isolation pattern evaluation.

        Mathematical consequence:
            Ne is a CONSEQUENCE of isolation, not an independent variable.
            It is fixed as an environmental input (like Bombus frequency),
            not sampled as a latent parameter θ.  This is valid ONLY if the
            0.765 coefficient comes from data independent of y_obs.
        """
        if self.effective_population_size < 0:
            self.effective_population_size = max(0.05, 1.0 - 0.765 * self.island_distance)
