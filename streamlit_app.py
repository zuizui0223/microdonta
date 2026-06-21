"""RACH — Causal Admissibility & Degeneracy Framework  (post-publication tool).

Role
----
This app is a post-publication customization companion for the MEE paper
"RACH: A framework for causal admissibility, degeneracy and next-observation
value in ecological systems."

Two entry points:

  1. **Worked Examples** — reproduces the three Tier-A (validated, magnitude-free)
     worked examples from the paper, so you can inspect the live RACH output:
       • Structure discovery (§4.1) — mechanism-free path inference
       • Campanula isolation cline (§4.2) — S2/S3 confound and guide resolution
       • Bergmann's rule (§4.3) — heat conservation vs. fasting endurance

  2. **Custom RACH** — enter your own system (mechanisms, trait effects, observed
     ordinal pattern) and get CA_j, D, R, confound structure, and NOV suggestions
     using the same Tier-A ABC engine.

No field-data magnitudes are assumed; every active edge gets a random positive
magnitude per draw, which is then integrated out (Tier A, VALIDATED).
"""

from __future__ import annotations

import math
import pathlib
import random
import sys
from dataclasses import dataclass

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Core RACH imports (always available)
# ---------------------------------------------------------------------------
from causal_model.causal_admissibility import (
    causal_degeneracy,
    causal_resolvability,
    rach_summary,
)
from causal_model.mechanism_equivalence import mechanism_equivalence_structure
from causal_model.minimal_explanations import minimal_explanations
from causal_model.switch_inference import BiologicalSwitch
from causal_model.simulator import TIER_VALIDATED, evidence_tier

# ---------------------------------------------------------------------------
# App config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RACH — Causal Admissibility Framework",
    layout="wide",
    page_icon="🔬",
)

# ===========================================================================
# Page header
# ===========================================================================
st.title("RACH — Causal Admissibility & Degeneracy Framework")
st.caption(
    "Post-publication customization tool for "
    "*Methods in Ecology and Evolution* (2026). "
    "Run the Tier-A worked examples from the paper, or enter your own system."
)

with st.expander("RACH formal definition", expanded=False):
    st.markdown(r"""
**Core RACH object — admissible causal region:**

```
A_ε(y_obs, x_obs) = { (θ, s) ∈ Θ × S :  G(θ)=1,  d(P_sim(f(x_obs; θ,s)), P_obs(y_obs)) ≤ ε }
```

| Symbol | Name | Meaning |
|--------|------|---------|
| x_obs | Fixed ecological context | gradient environment, Bombus frequency, latitude … |
| θ | Latent parameters | effect magnitudes (randomised in Tier-A) |
| s | Mechanism switch state {0,1}^K | which candidate mechanisms are active |
| G(θ) | Feasibility constraint | biological plausibility filter |
| f | Generative map | structural forward propagation |
| y_obs | Observed ordinal pattern | directional gradients accepted as facts |

**Five core RACH quantities:**

| Quantity | Symbol | Meaning |
|----------|--------|---------|
| Causal admissibility | CA_j = P(s_j=1 \| A_ε) | Probability mechanism j is active in A_ε |
| Causal degeneracy | D = H(S \| A_ε) | Remaining mechanism entropy (bits) |
| Causal resolvability | R = 1 − D/K | Fraction of causal uncertainty resolved |
| Observation contribution | OC_k = R(O) − R(O∖{k}) | Resolvability added by pattern k |
| Next-observation value | NOV(q) = E[R(O∪q) − R(O)] | Expected ΔR from candidate observation q |

**Two-tier evidence policy:**
* **Tier A (VALIDATED)** — randomised-coefficient generic f; conclusions are about the *confound logic*, not assumed magnitudes. ✅ Safe to report as validation of the *method*.
* **Tier B (ILLUSTRATIVE)** — hand-coded phenomenological f; posteriors reflect encoded assumptions. ⚠ Conditional on the encoded f only.
""")

# ===========================================================================
# Top-level navigation
# ===========================================================================
tab_examples, tab_custom, tab_about = st.tabs(
    ["① Tier-A Worked Examples", "② Custom RACH Analysis", "ℹ About"]
)


# ===========================================================================
# Helpers
# ===========================================================================

def _ca_bar(ca: dict[str, float], title: str = "") -> None:
    """Display CA_j as a bar chart + colour-coded metric row."""
    if title:
        st.markdown(f"#### {title}")
    names = list(ca.keys())
    vals  = list(ca.values())
    df = pd.DataFrame({"mechanism": names, "CA_j": vals})
    st.bar_chart(df.set_index("mechanism"))
    cols = st.columns(len(names))
    for i, (n, v) in enumerate(ca.items()):
        label = ("✅ ON" if v > 0.67 else ("❌ OFF" if v < 0.33 else "⚠ ambiguous"))
        cols[i].metric(n[:20], f"CA={v:.3f}", delta=label, delta_color="normal")


def _dr_metrics(D: float, R: float, K: int, n: int) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("D — degeneracy", f"{D:.3f} bits")
    c2.metric("K — max entropy", f"{K} bits")
    c3.metric("R — resolvability", f"{R:.3f}")
    c4.metric("|A_ε| accepted", n)


def _explanation_panel(acc: list[dict], switches: list[BiologicalSwitch]) -> None:
    """Show the minimal-sufficient-explanation summary of A_ε.

    This is the headline summary: it states which inclusion-minimal sets of
    mechanisms reproduce the pattern, and how the posterior mass splits among
    them — far more legible than per-switch marginals when the mechanisms form
    a disjunction confound.
    """
    dec = minimal_explanations(acc, switches)
    if not dec.explanations:
        st.warning("A_ε is empty — minimal explanations are non-estimable.")
        return
    rows = [
        {
            "minimal explanation": ("{" + ", ".join(sorted(e.mechanisms)) + "}"
                                    if e.mechanisms else "{∅ no mechanism}"),
            "posterior mass": round(e.mass, 3),
        }
        for e in dec.explanations
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    c1, c2, c3 = st.columns(3)
    c1.metric("R_expl (explanation-level)", f"{dec.R_expl:.3f}")
    c2.metric("D_expl", f"{dec.D_expl:.3f} bits")
    c3.metric("# minimal explanations", len(dec.explanations))
    if len(dec.explanations) > 1 and dec.R_expl < 0.5:
        st.info(
            "**Reading:** the pattern is explained by *either* of the minimal sets "
            "above — they are confounded. The per-switch CA_j look ambiguous (~0.5–0.7) "
            "precisely because each mechanism is one option in this disjunction, not "
            "because nothing was learned. R_expl reports how concentrated the posterior "
            "is on a *single* explanation."
        )
    elif dec.R_expl >= 0.99:
        st.success(
            "**Reading:** a single minimal explanation carries (almost) all the "
            "posterior mass — the mechanism question is resolved at the explanation level."
        )


def _confound_table(acc: list[dict], switches: list[BiologicalSwitch]) -> None:
    """Show confounding edges from mechanism_equivalence_structure."""
    struct = mechanism_equivalence_structure(acc, switches)
    if struct.edges:
        rows = [
            {
                "confounding edge": e.describe(),
                "MI (bits)": round(e.mutual_information, 3),
                "ϕ correlation": round(e.phi, 3),
                "relation": e.relation,
            }
            for e in struct.edges
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.success("No significant confounding edges detected in A_ε.")
    if struct.pinned_on:
        st.info(f"Pinned ON (CA_j ≥ 0.8): {', '.join(struct.pinned_on)}")
    if struct.pinned_off:
        st.info(f"Pinned OFF (CA_j ≤ 0.2): {', '.join(struct.pinned_off)}")


# ===========================================================================
# ① Worked Examples
# ===========================================================================
with tab_examples:
    st.markdown(
        "All examples use the **Tier-A (VALIDATED)** simulator: "
        "only directional signs are asserted; every effect magnitude is drawn "
        "fresh and integrated out. Results reflect the *confound logic*, not "
        "hand-tuned coefficients."
    )

    ex_choice = st.radio(
        "Select worked example",
        [
            "Adaptation vs. plasticity — common-garden confound (recommended)",
            "Structure Discovery (§4.1) — mechanism-free path inference",
            "Campanula isolation cline (§4.2) — S2/S3 confound",
            "Bergmann's rule (§4.3) — heat conservation vs. fasting endurance",
        ],
        horizontal=False,
    )

    col_n, col_s, col_truth = st.columns(3)
    ex_n    = col_n.slider("ABC draws", 1000, 8000, 3000, 500, key="ex_n")
    ex_seed = col_s.number_input("Seed", value=1, step=1, key="ex_seed")
    if "Bergmann" in ex_choice:
        ex_truth = col_truth.selectbox(
            "Assumed truth (for resolution panel)",
            ["fasting_endurance", "heat_conservation", "both"],
            key="ex_truth_berg",
        )
    elif "Campanula" in ex_choice:
        ex_truth = col_truth.selectbox(
            "Assumed truth (for resolution panel)",
            ["S3", "S2"],
            key="ex_truth_camp",
        )
    elif "Adaptation" in ex_choice:
        ex_truth = col_truth.selectbox(
            "Assumed truth (for resolution panel)",
            ["genetic", "plastic", "maternal"],
            key="ex_truth_adapt",
        )
    else:
        ex_truth = None

    if st.button("▶ Run worked example", type="primary", width="stretch"):

        # ── Adaptation vs. plasticity (recommended lead example) ──────────────
        if "Adaptation" in ex_choice:
            with st.spinner("Running adaptation-vs-plasticity example…"):
                from causal_model.adaptation_plasticity import run_adaptation_plasticity
                res = run_adaptation_plasticity(truth=ex_truth, n_attempts=ex_n, seed=int(ex_seed))
            st.success(
                f"|A_ε| = {res.n_accepted} accepted from {ex_n} draws  "
                f"(tier: {evidence_tier('causal_model.adaptation_plasticity')})"
            )
            st.markdown(
                "**Constraint = sign structure** (which process moves which observable, "
                "and in what direction). **Trade-off = the benign-site cost**: genetic "
                "adaptation raises tolerance *and* lowers benign-site performance. No "
                "magnitude is tuned."
            )

            def _expl_df(expl):
                return pd.DataFrame([
                    {"minimal explanation": ("{" + ", ".join(sorted(m)) + "}" if m else "{∅}"),
                     "posterior mass": round(mass, 3)}
                    for m, mass in expl
                ])

            st.markdown("### Field cline alone — the confound (headline)")
            st.caption(
                "The wild cline (the only y_obs) is reproduced by genetic adaptation, "
                "phenotypic plasticity, *or* maternal effects — a three-way confound."
            )
            st.dataframe(_expl_df(res.explanations), hide_index=True, width="stretch")
            c1, c2, c3 = st.columns(3)
            c1.metric("R_expl (explanation-level)", f"{res.R_expl:.3f}")
            c2.metric("switch-level R", f"{res.R_RACH:.3f}")
            c3.metric("|A_ε|", res.n_accepted)

            st.markdown("### NOV — exact EVSI on explanation resolvability")
            st.caption(
                "Note RACH's non-obvious finding: a *single-generation* common garden "
                "ranks below the second-generation garden and the cost assay, because an "
                "F1 garden alone cannot separate genetic adaptation from maternal effects "
                "(both persist in F1)."
            )
            st.dataframe(
                pd.DataFrame([
                    {"rank": i + 1, "observation": name, "NOV (EVSI on R_expl)": round(val, 4)}
                    for i, (name, val) in enumerate(res.nov_ranking)
                ]),
                hide_index=True, width="stretch",
            )

            st.markdown(f"### Sequential resolution in NOV order (truth = {ex_truth})")
            st.caption(
                "Each row adds the next observation (cheap A_ε filter) and shows the "
                "surviving minimal explanations. R_expl → 1 using only observables — "
                "no idealised switch-readout assay."
            )
            seq_rows = [{"step cline only": "—", "R_expl": res.R_expl,
                         "explanations": "  ".join(
                             ("{" + ", ".join(sorted(m)) + "}") + f"={mass:.2f}"
                             for m, mass in res.explanations)}]
            for cand_name, expl, r in res.seq_steps:
                seq_rows.append({
                    "step cline only": f"+ {cand_name}",
                    "R_expl": round(r, 3),
                    "explanations": "  ".join(
                        ("{" + ", ".join(sorted(m)) + "}") + f"={mass:.2f}" for m, mass in expl),
                })
            st.dataframe(pd.DataFrame(seq_rows), hide_index=True, width="stretch")

        # ── Structure Discovery ──────────────────────────────────────────────
        elif "Structure" in ex_choice:
            with st.spinner("Running structure discovery…"):
                from causal_model.structure_discovery import run_structure_discovery
                res = run_structure_discovery(n_attempts=ex_n, seed=int(ex_seed))
            obs_str = ", ".join(
                f"{t}{'↓' if d < 0 else '↑'}" for t, d in res.observed.items()
            )
            st.success(
                f"|A_ε| = {res.n_accepted} accepted from {res.n_attempts} draws  "
                f"(observed cline: {obs_str}; "
                f"tier: {evidence_tier('causal_model.structure_discovery')})"
            )

            st.markdown("### Edge posterior — P(edge present | A_ε)")
            st.caption(
                "Each candidate directed edge (X→Ma, X→Mb, Ma→Mb, Ma→T1, …) "
                "is a random object; this is how often it is present in the "
                "admissible region given the observed cline."
            )
            ep = res.edge_posterior
            df_ep = pd.DataFrame(
                {"edge": list(ep.keys()), "P(present | A_ε)": list(ep.values())}
            )
            st.bar_chart(df_ep.set_index("edge"))
            st.dataframe(df_ep, hide_index=True, width="stretch")

            st.markdown("### Path support per target trait")
            st.caption(
                "For each target, how often the cline reaches it directly vs. "
                "via mediator Ma / Mb. High direct + low via = the trait responds "
                "to the cline without a mediator."
            )
            path_rows = []
            for trait, ps in res.path_support.items():
                row = {"target": trait}
                row.update({k: round(v, 3) for k, v in ps.items()})
                path_rows.append(row)
            st.dataframe(pd.DataFrame(path_rows), hide_index=True, width="stretch")

            st.markdown("### Structural degeneracy")
            c1, c2, c3 = st.columns(3)
            c1.metric("D structural (bits)", f"{res.D_structural:.3f}")
            c2.metric("R structural", f"{res.R_structural:.3f}")
            c3.metric("|A_ε|", res.n_accepted)

            if res.confounded_edges:
                st.markdown("### Confounded edge pairs")
                for e in res.confounded_edges:
                    st.caption(f"• {e}")

            if res.nov:
                st.markdown("### NOV — which mediator to measure")
                st.caption(
                    "Expected structural-degeneracy reduction from measuring each "
                    "mediator's own cline response."
                )
                nov_rows = [
                    {"rank": i + 1, "measure mediator": name,
                     "NOV (ΔD_structural bits)": round(val, 4)}
                    for i, (name, val) in enumerate(res.nov)
                ]
                st.dataframe(pd.DataFrame(nov_rows), hide_index=True, width="stretch")

            if res.path_support_after:
                st.markdown("### Path support after measuring the top-NOV mediator")
                st.caption(
                    "Conditioning on the top-NOV mediator being silent rules out "
                    "paths routed through it, separating direct from mediated effects."
                )
                pa_rows = []
                for trait, ps in res.path_support_after.items():
                    row = {"target": trait}
                    row.update({k: round(v, 3) for k, v in ps.items()})
                    pa_rows.append(row)
                st.dataframe(pd.DataFrame(pa_rows), hide_index=True, width="stretch")

        # ── Campanula structural ─────────────────────────────────────────────
        elif "Campanula" in ex_choice:
            with st.spinner("Running Campanula Tier-A structural example…"):
                from causal_model.campanula_structural import (
                    run_campanula_structural, CampanulaResult
                )
                res = run_campanula_structural(
                    truth=ex_truth, n_attempts=ex_n, seed=int(ex_seed)
                )
            st.success(
                f"|A_ε| = {res.n_accepted} accepted from {ex_n} draws  "
                f"(tier: {evidence_tier('causal_model.campanula_structural')})"
            )

            def _expl_table(expl):
                return pd.DataFrame([
                    {"minimal explanation": ("{" + ", ".join(sorted(m)) + "}"
                                             if m else "{∅}"),
                     "posterior mass": round(mass, 3)}
                    for m, mass in expl
                ])

            st.markdown("### Minimal sufficient explanations (headline)")
            st.caption(
                "The pattern (selfing↑, flower↓) is reproduced by *either* of these "
                "minimal mechanism sets — that disjunction is the real finding, not "
                "the ~0.7 per-switch marginals below."
            )
            st.dataframe(_expl_table(res.explanations), hide_index=True, width="stretch")
            st.metric("R_expl (explanation-level)", f"{res.R_expl:.3f}")

            st.markdown("### CA_j on published ordinal pattern (selfing↑, flower↓)")
            _ca_bar(res.ca_j, "Before distinguishing observation")
            _dr_metrics(res.D_RACH, res.R_RACH, len(res.ca_j), res.n_accepted)

            st.markdown("### Confound structure")
            st.caption(res.confound_edge)

            if res.nov_ranking:
                st.markdown("### NOV — top candidate observations")
                nov_rows = [
                    {"rank": i + 1, "observation": name, "NOV (ΔR)": round(val, 4)}
                    for i, (name, val) in enumerate(res.nov_ranking)
                ]
                st.dataframe(pd.DataFrame(nov_rows), hide_index=True, width="stretch")

            if res.ca_j_after:
                st.markdown(f"### Resolution after adding distinguishing observation (truth = {ex_truth})")
                if res.explanations_after:
                    st.caption(
                        "Explanation-level resolution: the minimal explanation collapses "
                        "to a single set, so R_expl → 1 — using only the observable cline, "
                        "without any idealised switch-readout assay."
                    )
                    st.dataframe(_expl_table(res.explanations_after), hide_index=True, width="stretch")
                _ca_bar(res.ca_j_after, "After distinguishing observation")
                c1, c2, c3 = st.columns(3)
                c1.metric("R before", f"{res.R_RACH:.3f}")
                c2.metric("R after", f"{res.R_after:.3f}")
                c3.metric("R_expl after", f"{res.R_expl_after:.3f}")

        # ── Bergmann ─────────────────────────────────────────────────────────
        else:
            with st.spinner("Running Bergmann's rule example…"):
                from causal_model.bergmann_worked_example import (
                    run_bergmann_demo, BergmannResult
                )
                res = run_bergmann_demo(
                    truth=ex_truth, n_attempts=ex_n, seed=int(ex_seed)
                )
            st.success(
                f"|A_ε| = {res.n_accepted} accepted from {ex_n} draws  "
                f"(tier: {evidence_tier('causal_model.bergmann_worked_example')})"
            )
            st.info(
                "**Note:** `--truth` is an *illustrative assumed latent truth* used to "
                "demonstrate resolution. The Bergmann mechanism is genuinely unresolved "
                "in the literature (Meiri & Dayan 2003)."
            )

            st.markdown("### CA_j on published body-size cline (size↑ with latitude)")
            _ca_bar(res.ca_j, "Before mechanism-specific assay")
            _dr_metrics(res.D_RACH, res.R_RACH, len(res.ca_j), res.n_accepted)

            st.markdown(f"### Confound structure")
            st.caption(res.confound_edge)
            st.info(f"NOV-recommended next observation: **{res.nov_recommended}**")

            if res.ca_j_after:
                st.markdown(f"### Resolution after mechanism-specific assays (truth = {ex_truth})")
                _ca_bar(res.ca_j_after, "After assays")
                c1, c2 = st.columns(2)
                c1.metric("R before", f"{res.R_RACH:.3f}")
                c2.metric("R after", f"{res.R_after:.3f}")

            with st.expander("RACH-SEQ trace"):
                st.text(res.seq_trace)


# ===========================================================================
# ② Custom RACH Analysis
# ===========================================================================
with tab_custom:
    st.markdown(
        "Define your own biological system — candidate mechanisms, their directional "
        "effects on observable traits, and the ordinal pattern you have observed. "
        "RACH will compute CA_j, D, R, and identify which future observation has the "
        "highest NOV (expected resolvability gain)."
    )
    st.info(
        "**Tier-A engine**: every active mechanism's effect magnitude is drawn "
        "uniformly at random and integrated out. Only the *signs* you specify are "
        "asserted — magnitudes are never hard-coded."
    )

    # ── Step 1: Define traits ────────────────────────────────────────────────
    st.markdown("### Step 1 — Name your observable traits")
    st.caption(
        "Comma-separated list of traits that are observable along your gradient "
        "(e.g. `selfing_rate, flower_size, guide_intensity, body_mass`)."
    )
    trait_str = st.text_input(
        "Trait names",
        value="selfing_rate, flower_size, nectar_guide",
        key="cust_traits",
    )
    traits = [t.strip() for t in trait_str.split(",") if t.strip()]

    # ── Step 2: Define mechanisms ────────────────────────────────────────────
    st.markdown("### Step 2 — Define candidate mechanisms")
    st.caption(
        "Each line: `mechanism_name: trait1+, trait2-, trait3+`  \n"
        "Use `+` for a positive effect (trait increases with gradient) "
        "and `-` for negative. Omit a trait if a mechanism has no direct effect on it."
    )
    default_mechs = (
        "selfing_syndrome: selfing_rate+, flower_size-\n"
        "island_common_cause: selfing_rate+, flower_size-, nectar_guide-\n"
        "guide_attracts_bombus: nectar_guide-"
    )
    mech_text = st.text_area(
        "Mechanisms (one per line)",
        value=default_mechs,
        height=160,
        key="cust_mechs",
    )

    # Parse mechanisms
    def _parse_mechs(text: str) -> list[dict]:
        mechs = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            name, rest = line.split(":", 1)
            name = name.strip()
            effects: dict[str, int] = {}
            for part in rest.split(","):
                part = part.strip()
                if not part:
                    continue
                if part.endswith("+"):
                    effects[part[:-1].strip()] = +1
                elif part.endswith("-"):
                    effects[part[:-1].strip()] = -1
            if name and effects:
                mechs.append({"name": name, "effects": effects})
        return mechs

    parsed_mechs = _parse_mechs(mech_text)

    if parsed_mechs:
        st.markdown("**Parsed mechanism–trait sign table:**")
        all_mech_traits = sorted({t for m in parsed_mechs for t in m["effects"]})
        tbl = []
        for m in parsed_mechs:
            row = {"mechanism": m["name"]}
            for t in all_mech_traits:
                v = m["effects"].get(t, 0)
                row[t] = ("↑" if v > 0 else ("↓" if v < 0 else "—"))
            tbl.append(row)
        st.dataframe(pd.DataFrame(tbl), hide_index=True, width="stretch")
    else:
        st.warning("No mechanisms parsed. Check the format (name: trait+, trait-).")

    # ── Step 3: Define y_obs ─────────────────────────────────────────────────
    st.markdown("### Step 3 — Define your observed ordinal pattern (y_obs)")
    st.caption(
        "Select the direction of each trait along your gradient. "
        "Only the constrained traits participate in ABC acceptance."
    )
    all_traits_union = sorted(
        {t for m in parsed_mechs for t in m["effects"]} | set(traits)
    )
    y_obs: dict[str, int] = {}
    cols_yobs = st.columns(min(len(all_traits_union), 4))
    for i, trait in enumerate(all_traits_union):
        col = cols_yobs[i % len(cols_yobs)]
        direction = col.selectbox(
            trait, ["— (not constrained)", "↑ increases", "↓ decreases"],
            key=f"yobs_{trait}",
        )
        if direction == "↑ increases":
            y_obs[trait] = +1
        elif direction == "↓ decreases":
            y_obs[trait] = -1

    if y_obs:
        st.caption(
            "y_obs: " + ", ".join(f"{t}{'↑' if d > 0 else '↓'}" for t, d in y_obs.items())
        )
    else:
        st.warning("No ordinal constraints set. Set at least one trait direction.")

    # ── Step 4: Settings & run ───────────────────────────────────────────────
    st.markdown("### Step 4 — Run RACH")
    c_n, c_s = st.columns(2)
    cust_n    = c_n.slider("ABC draws", 500, 10000, 3000, 500, key="cust_n")
    cust_seed = c_s.number_input("Seed", value=42, step=1, key="cust_seed")

    run_custom = st.button(
        "▶ Run Custom RACH", type="primary", width="stretch",
        disabled=(not parsed_mechs or not y_obs),
    )

    # ── ABC engine ────────────────────────────────────────────────────────────

    def _custom_abc(
        mechanisms: list[dict],
        y_obs_constraints: dict[str, int],
        n_attempts: int,
        seed: int,
    ) -> list[dict]:
        """Tier-A ABC for a user-defined mechanism system.

        Samples mechanism presence (Bernoulli 0.5) and random magnitudes
        [0.3, 0.8] per active edge, accepts rows whose net trait slopes
        satisfy all y_obs ordinal constraints.
        """
        rng = random.Random(seed)
        accepted = []
        for _ in range(n_attempts):
            s = {m["name"]: (rng.random() < 0.5) for m in mechanisms}
            slopes: dict[str, float] = {}
            for m in mechanisms:
                if not s[m["name"]]:
                    continue
                mag = rng.uniform(0.3, 0.8)
                for trait, sign in m["effects"].items():
                    slopes[trait] = slopes.get(trait, 0.0) + sign * mag

            ok = True
            for trait, direction in y_obs_constraints.items():
                net = slopes.get(trait, 0.0)
                if direction > 0 and net <= 0:
                    ok = False
                    break
                if direction < 0 and net >= 0:
                    ok = False
                    break
            if ok:
                row = {k: v for k, v in s.items()}
                for t, v in slopes.items():
                    row[f"slope_{t}"] = round(v, 4)
                accepted.append(row)
        return accepted

    def _nov_hints(
        acc: list[dict],
        mechanisms: list[dict],
        y_obs_constraints: dict[str, int],
    ) -> list[dict]:
        """Heuristic NOV: for each unobserved trait, estimate expected ΔR if added.

        A trait helps resolve the confound if it is driven differently
        (opposite signs or one drives / other doesn't) by the confounded pair.
        We estimate ΔR as the fraction of A_ε rows that would be filtered out
        by conditioning on the most-informative outcome of adding that trait.
        """
        if len(acc) < 5:
            return []
        mnames = [m["name"] for m in mechanisms]
        all_traits = {t for m in mechanisms for t in m["effects"]}
        candidate_traits = all_traits - set(y_obs_constraints.keys())

        # Compute switches for causal_resolvability
        switches = [
            BiologicalSwitch(
                name=m["name"], pathway_key=m["name"],
                biological_question=m["name"], description=m["name"],
            )
            for m in mechanisms
        ]
        R0 = causal_resolvability(acc, switches)
        hints = []
        for trait in sorted(candidate_traits):
            # Condition on trait > 0 (increases)
            pos_rows = [r for r in acc if r.get(f"slope_{trait}", 0.0) > 0]
            neg_rows = [r for r in acc if r.get(f"slope_{trait}", 0.0) <= 0]
            R_pos = causal_resolvability(pos_rows, switches) if len(pos_rows) >= 5 else R0
            R_neg = causal_resolvability(neg_rows, switches) if len(neg_rows) >= 5 else R0
            # Expected ΔR: weighted by how often each outcome occurs
            p_pos = len(pos_rows) / len(acc)
            p_neg = len(neg_rows) / len(acc)
            delta_R = p_pos * (R_pos - R0) + p_neg * (R_neg - R0)
            # What sign does each mechanism predict for this trait?
            mech_preds = {
                m["name"]: m["effects"].get(trait, 0)
                for m in mechanisms
            }
            hints.append({
                "observation": f"measure {trait} gradient",
                "NOV ΔR (expected)": round(delta_R, 4),
                "mechanism predictions": "  |  ".join(
                    f"{n}: {'↑' if v > 0 else ('↓' if v < 0 else '—')}"
                    for n, v in mech_preds.items()
                ),
                "p(increases)": round(p_pos, 3),
                "p(decreases)": round(p_neg, 3),
            })
        hints.sort(key=lambda x: x["NOV ΔR (expected)"], reverse=True)
        return hints

    if run_custom:
        with st.spinner("Running Tier-A ABC…"):
            acc = _custom_abc(parsed_mechs, y_obs, cust_n, int(cust_seed))

        if not acc:
            st.error(
                f"A_ε is empty — no draws satisfied y_obs after {cust_n} attempts. "
                "Check that your mechanism sign table is compatible with the observed pattern, "
                "or relax the constraints."
            )
        else:
            switches = [
                BiologicalSwitch(
                    name=m["name"], pathway_key=m["name"],
                    biological_question=m["name"], description=m["name"],
                )
                for m in parsed_mechs
            ]
            K   = len(switches)
            D   = causal_degeneracy(acc, switches)
            R   = causal_resolvability(acc, switches)
            n   = len(acc)
            ca  = {
                sw.name: round(sum(1 for r in acc if r.get(sw.name)) / n, 4)
                for sw in switches
            }

            st.session_state["_cust_acc"]      = acc
            st.session_state["_cust_ca"]       = ca
            st.session_state["_cust_D"]        = D
            st.session_state["_cust_R"]        = R
            st.session_state["_cust_K"]        = K
            st.session_state["_cust_switches"] = switches
            st.session_state["_cust_mechs"]    = parsed_mechs
            st.session_state["_cust_yobs"]     = y_obs

    # ── Results ───────────────────────────────────────────────────────────────
    if "_cust_acc" in st.session_state:
        acc      = st.session_state["_cust_acc"]
        ca       = st.session_state["_cust_ca"]
        D        = st.session_state["_cust_D"]
        R        = st.session_state["_cust_R"]
        K        = st.session_state["_cust_K"]
        switches = st.session_state["_cust_switches"]
        mechs    = st.session_state["_cust_mechs"]
        _yobs    = st.session_state["_cust_yobs"]

        st.divider()
        st.success(f"|A_ε| = {len(acc)} accepted from {cust_n} draws")

        st.markdown("### Minimal sufficient explanations (headline)")
        st.caption(
            "Which inclusion-minimal sets of mechanisms reproduce your pattern, "
            "and how the posterior mass splits among them. Read this *before* the "
            "per-switch CA_j."
        )
        _explanation_panel(acc, switches)

        st.markdown("### CA_j — Causal admissibility")
        _ca_bar(ca)
        _dr_metrics(D, R, K, len(acc))

        with st.expander("Confound structure", expanded=True):
            _confound_table(acc, switches)

        with st.expander("NOV — next-observation value (heuristic)", expanded=True):
            nov_h = _nov_hints(acc, mechs, _yobs)
            if nov_h:
                df_nov = pd.DataFrame(nov_h)
                st.bar_chart(
                    df_nov.set_index("observation")[["NOV ΔR (expected)"]],
                    width="stretch",
                )
                st.dataframe(df_nov, hide_index=True, width="stretch")
                st.caption(
                    "NOV is heuristic: expected ΔR from conditioning A_ε on each "
                    "unobserved trait's direction. The highest-NOV trait is the one "
                    "whose gradient measurement would most reduce causal degeneracy."
                )
            else:
                st.info(
                    "All traits in y_obs are already constrained, or too few "
                    "accepted rows. Add more traits to the mechanism definitions "
                    "beyond those in y_obs to see NOV suggestions."
                )

        with st.expander("Download accepted A_ε rows (CSV)"):
            df_acc = pd.DataFrame(acc)
            st.download_button(
                "⬇ accepted_rows.csv",
                df_acc.to_csv(index=False).encode("utf-8"),
                "rach_custom_accepted_rows.csv",
                "text/csv",
                width="stretch",
            )
            df_ca = pd.DataFrame(
                [{"mechanism": k, "CA_j": v} for k, v in ca.items()]
                + [{"mechanism": "D_bits", "CA_j": round(D, 4)},
                   {"mechanism": "R", "CA_j": round(R, 4)},
                   {"mechanism": "K", "CA_j": K}]
            )
            st.download_button(
                "⬇ rach_summary.csv",
                df_ca.to_csv(index=False).encode("utf-8"),
                "rach_custom_summary.csv",
                "text/csv",
                width="stretch",
            )


# ===========================================================================
# ℹ About
# ===========================================================================
with tab_about:
    st.markdown(r"""
## About RACH

**RACH** (*Restricted Admissible Causal Hypotheses*) is a simulation-based
framework for diagnosing and quantifying causal degeneracy — the situation in
which multiple mechanistic hypotheses each predict the same observed ordinal
pattern and are therefore indistinguishable from that pattern alone.

### How to cite

> Authors (2026). RACH: A framework for causal admissibility, degeneracy and
> next-observation value in ecological systems. *Methods in Ecology and
> Evolution*.

### Worked examples in the paper

| Section | System | Tier | Key finding |
|---------|--------|------|-------------|
| §4.1 | Mechanism-free path inference | A | D = 8.10/9 bits from ordinal cline; direct path most supported |
| §4.2 | *Campanula* isolation cline | A | S2 (selfing syndrome) ≡ S3 (common cause) on selfing↑/flower↓; nectar guide gradient separates them |
| §4.3 | Bergmann's rule | A | Heat conservation ≡ fasting endurance on size cline; mechanism assay resolves |

### Two-tier evidence policy

| Tier | Simulator f | What the posterior means | Use |
|------|------------|--------------------------|-----|
| **A — VALIDATED** | Randomised-coefficient linear f | Confound logic under arbitrary magnitudes | Publication-grade; conclusions about the *method* |
| **B — ILLUSTRATIVE** | Hand-coded phenomenological f | Researcher's encoded assumptions | Pipeline illustration only; conditional on f |

### Glossary

| Term | Definition |
|------|-----------|
| A_ε | Admissible causal region: accepted (θ,s) draws |
| CA_j | P(s_j=1 ∣ A_ε) — posterior prob. mechanism j active |
| D | H(S ∣ A_ε) — joint mechanism entropy (bits) |
| R | 1 − D/K — fraction of causal uncertainty resolved |
| OC_k | R(O) − R(O∖{k}) — contribution of pattern k |
| NOV(q) | E[R(O∪q) − R(O)] — expected gain from obs. q |
| confounding edge | (A,B) pair with high MI in A_ε; data cannot separate A from B |
| disjunction confound | A ∨ B required; either alone or both together explain y_obs |

### Repository

Source code: [github.com/zuizui0223/microdonta](https://github.com/zuizui0223/microdonta)

CLI equivalents:

```bash
python -m causal_model.structure_discovery --figure outputs/fig4a.png
python -m causal_model.campanula_structural --truth S3 --figure outputs/fig4b.png
python -m causal_model.bergmann_worked_example --truth fasting_endurance
```
""")
