# RACH tutorial — run it, read it, adapt it

A five-minute, copy-pasteable introduction for readers coming from the paper.
RACH's inference layer is **simulator-agnostic**: it consumes a list of accepted
`(θ, s)` draws (the admissible region `A_ε`) plus a list of mechanism switches,
and returns the five RACH quantities. You can drive it from the bundled
Campanula example, or plug in your own system.

## 1. Install

```bash
pip install -e ".[dev]"     # runtime + matplotlib + pytest
# or:  pip install -r requirements.txt -r requirements-dev.txt
pytest -q                   # run the complete regression suite
```

## 2. Reproduce the paper figures (one command each)

```bash
python -m causal_model.confound_demo      --figure outputs/mee/confound_demo.png
python -m causal_model.synthetic_demo     --figure outputs/mee/synthetic_demo.png
python -m causal_model.nov_calibration    --figure outputs/mee/nov_calibration.png
python -m causal_model.known_truth_benchmark \
    --n-attempts 300 --noise-rates 0.0,0.05,0.1,0.15,0.2,0.3 \
    --n-attempts-sweep 50,100,200,400,800 \
    --figure outputs/mee/known_truth_recovery.png
```

Seeds are fixed, so the printed numbers match the manuscript exactly
(confound demo: `seed 7, n = 600`; synthetic: `seed 1, n = 4000`;
calibration: `seed 7, n = 1000`).

## 3. The minimal inference call

Everything downstream of ABC is three functions in
`causal_model.causal_admissibility`:

```python
from causal_model.causal_admissibility import (
    rach_summary,            # CA_j, D_RACH, R_RACH
    observation_contribution,  # OC_k (leave-one-out)
    next_observation_value,    # NOV(q)
)

# accepted_rows: list of dicts, one per accepted (θ, s) draw in A_ε.
#   each row has the switch states (e.g. row["S2"] = True/False) plus any
#   parameters you sampled. switches: a list of BiologicalSwitch.
summary = rach_summary(accepted_rows, switches)
print(summary.summary_dict())
#   {'n_accepted': ..., 'n_switches': 4,
#    'causal_degeneracy_D': 3.56, 'max_degeneracy_K': 4.0,
#    'causal_resolvability_R': 0.11}

for ca in summary.causal_admissibility:
    print(ca.switch_name, round(ca.ca_j, 3))   # P(s_j = 1 | A_ε)
```

Read the result as: **D_RACH near K (here 4) means the data barely resolve
mechanism identity**; switches with `CA_j ≈ 0.5` are unresolved (admissible both
ways). `next_observation_value(accepted_rows, switches)` then ranks candidate
future observations by expected gain in resolvability.

## 4. Adapt it to your own system

The cleanest template is `causal_model/synthetic_demo.py` — a fully transparent,
non-Campanula 4-switch model in ~200 lines. To port RACH to your problem you
supply three things:

1. **Switches `s ∈ {0,1}^K`** — the candidate mechanisms, as `BiologicalSwitch`
   objects (`causal_model.switch_inference`). Each switch is one mechanism that is
   either active or not.
2. **A generative map `f` and pattern map `P_sim`** — your simulator (any backend)
   that turns `(θ, s)` into the same *ordinal pattern* your field data report
   (e.g. the sign of a trend along a gradient, not a raw value).
3. **An acceptance step** — sample `(θ, s)` from the prior, keep the draws whose
   simulated pattern matches your observed pattern within `ε`. Those kept draws
   are `accepted_rows`.

Then call `rach_summary` / `next_observation_value` exactly as above. Nothing in
the inference layer is Campanula-specific; `synthetic_demo.py` is the proof and
the copy-paste starting point.

## 5. Interactive exploration

```bash
streamlit run apps/streamlit_app.py
```

The app walks the Campanula worked example through every step (RACH inference →
CA_j → D·R → OC_k → NOV) and includes a *Generality* step that reproduces
Figures 1–2 with a Campanula/synthetic system selector.
