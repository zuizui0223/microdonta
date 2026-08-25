"""Apply publication-only formatting required for an MEE Research Article.

Scientific code, frozen benchmark protocols and frozen numerical result files are
out of scope. This script only edits manuscript/submission governance files.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Review manuscript
# ---------------------------------------------------------------------------
mpath = ROOT / "paper" / "mee_manuscript_draft.md"
m = mpath.read_text(encoding="utf-8")

m = replace_once(
    m,
    "**Ruiqi Zhang**\n\nKyoto University, Kyoto, Japan\n\n",
    "",
    "remove author identity from review manuscript",
)

abstract_replacement = """## Abstract

1. Ecological patterns can remain compatible with distinct mechanisms even when
measured without sampling error. We establish an exact identifiability boundary
for positive trait performance, `W(z)=F(z)E(z)`: observations that depend only on
`W` cannot distinguish equivalent changes in `F` and `E` (N1); `W` plus either
channel identifies the other (N2); an unknown proxy calibration permits relative
inference only when stable across regimes (N3), whereas calibration drift
restores non-identifiability (N4).

2. We introduce Restricted Admissible Causal Hypotheses (RACH), which retains
every mechanism program compatible with a declared constraint grammar and
observation set and reports residual causal degeneracy rather than forcing a
model winner. For candidate observations whose predictive outcomes are identified
by the current admissible region, the validated next-observation value is
`NOV(Q)=I(S;Q|A_ε)/K`. RACH-SEQ recomputes this information state after every
observation and selects the candidate with maximum current validated NOV.

3. In a preregistered truth-peek-free synthetic selection benchmark, RACH-SEQ
competed with an uninformed random-order policy while both received identical
systems, hidden truths, candidate sets and budgets. At budget two, RACH-SEQ
resolved all initial confounding edges on average and converged in 99.0% of
systems, compared with 60.45% edge resolution and 43.5% convergence under random
order; hidden-truth false exclusion was zero in every frozen policy-by-budget
cell. Independent checks confirmed the NOV information identity, exact
stored-region conditioning for the deterministic validation model and
reproducible software/figure builds.

4. An exact one-step colonisation-recruitment factorisation shows how the theorem
can be earned for a declared ecological output without extending it to
unfactorised multistep dynamics. Historical Izu Islands *Campanula* records are
used only as a prospective observation-design example because they do not
identify a vital-rate channel. RACH therefore converts structural
non-identifiability into a reportable admissible set, a stopping rule and an
explicit next-measurement design.

**Data/Code for peer review:** An anonymised reviewer bundle containing the
executable Python code, frozen protocol/result summaries, tests and figure
commands required to evaluate the manuscript will be uploaded with the
submission. No new empirical data are reported.

**Keywords:** approximate Bayesian computation; causal admissibility; degeneracy;
mutual information; observation design; structural identifiability; value of
information.

---
"""
new_m, n = re.subn(r"## Abstract\n.*?\n---\n", abstract_replacement, m, count=1, flags=re.S)
if n != 1:
    raise RuntimeError(f"abstract block: expected one match, found {n}")
m = new_m

heading_map = {
    "## 2. Exact channel-identifiability boundary": "## 2. Materials and Methods\n\n### 2.1 Exact channel-identifiability boundary",
    "### 2.1 Observation class": "#### 2.1.1 Observation class",
    "### 2.2 N1: net-only observations cannot identify the changed channel": "#### 2.1.2 N1: net-only observations cannot identify the changed channel",
    "### 2.3 N2: net performance plus one channel is sufficient": "#### 2.1.3 N2: net performance plus one channel is sufficient",
    "### 2.4 N3–N4: proxy calibration is the operational boundary": "#### 2.1.4 N3–N4: proxy calibration is the operational boundary",
    "### 2.5 Scope and executable checks": "#### 2.1.5 Scope and executable checks",
    "## 3. RACH: admissible explanations and next-observation design": "### 2.2 RACH: admissible explanations and next-observation design",
    "### 3.1 Formal object": "#### 2.2.1 Formal object",
    "### 3.2 The five quantities and their guarantees": "#### 2.2.2 The five quantities and their guarantees",
    "### 3.3 NOV as mechanism–observation information": "#### 2.2.3 NOV as mechanism–observation information",
    "### 3.4 Sensitivity to ε and the prior, not rule selection": "#### 2.2.4 Sensitivity to ε and the prior, not rule selection",
    "### 3.5 The RACH algorithm": "#### 2.2.5 The RACH algorithm",
    "## 4. Controlled validation": "## 3. Results\n\n### 3.1 Controlled validation",
    "### 4.1 Known-truth recovery (self-consistency; Fig. S1)": "#### 3.1.1 Known-truth recovery (self-consistency; Fig. S1)",
    "### 4.2 Model selection misleads; RACH exposes the confound (Fig. 1)": "#### 3.1.2 Model selection misleads; RACH exposes the confound (Fig. 1)",
    "### 4.3 Generality and observation-budget error control (Fig. 2)": "#### 3.1.3 Generality and observation-budget error control (Fig. 2)",
    "### 4.4 NOV information identity and calibration (Fig. 3)": "#### 3.1.4 NOV information identity and calibration (Fig. 3)",
    "## 5. Exact ecological projection and ABM boundary": "### 3.2 Exact ecological projection and ABM boundary",
    "## 6. Prospective worked design: Izu Islands *Campanula*": "### 3.3 Prospective worked design: Izu Islands *Campanula*",
    "## 7. Software and reproducibility": "## 4. Software and reproducibility",
    "## 8. Discussion": "## 5. Discussion",
}
for old, new in heading_map.items():
    m = replace_once(m, old, new, f"heading {old}")

ai_disclosure = """

### 2.3 AI-assisted development disclosure

OpenAI ChatGPT (GPT-5.6 Sol; accessed August 2026) was used interactively to
assist with code review, draft editing and repository/documentation maintenance.
The author reviewed and takes responsibility for all generated or edited text and
code. AI outputs were not treated as empirical observations or independent
scientific evidence; frozen benchmark configurations and reported numerical
results were executed and checked through the reproducible workflows described
below.
"""
m = replace_once(
    m,
    "\n## 3. Results\n",
    ai_disclosure + "\n## 3. Results\n",
    "AI disclosure insertion",
)

# Remove review-manuscript administrative/identity sections; they move to title page.
new_m, n = re.subn(
    r"\n## Data accessibility and code availability\n.*?(?=\n## References\n)",
    "\n",
    m,
    count=1,
    flags=re.S,
)
if n != 1:
    raise RuntimeError(f"administrative tail: expected one match, found {n}")
m = new_m

old_figure = """## Figure plan

1. **Figure 1 — Controlled confound.** ABC model ranking versus the admissible
   set, causal degeneracy, NOV ranking, and the resolving quantitative
   observation.
2. **Figure 2 — Sequential selection and error control.** Frozen v2 budget curves
   for RACH-SEQ and the matched random-order baseline: convergence, initial-edge
   resolution, observations used, distractors selected, and seed-level
   uncertainty.
3. **Figure 3 — NOV conditioning and calibration.** Stored-region conditioning
   versus fresh deterministic re-inference and predictive EVSI versus realised
   resolvability gain.
4. **Figure S1 — Known-truth recovery.** Controlled self-consistency across the
   frozen noise strata, retained as Supplementary validation rather than a
   natural-system mechanism claim.

N1–N4 and the earned one-step ecological projection are presented directly as
formal results/equations in the text rather than reserving ungenerated main-figure
numbers. ABM endpoint sweeps and extended sensitivity analyses belong in
Supplementary Information. Ecological-rule panels and structure discovery are not
part of this submission.
"""
new_figure = """## Figure captions

**Figure 1. Controlled confounding and next-observation resolution.** A controlled
proxy-backend example contrasts a single low-mass ABC MAP switch combination with
the full RACH admissible region. Panels report the model-ranking distribution,
causal admissibility/degeneracy, validated NOV ranking for candidate measurements,
and the change in admissibility after a quantitative confound-breaking
observation. The figure is a diagnostic of inferential behaviour, not a
natural-system mechanism claim.

**Figure 2. Sequential observation selection under a limited budget.** Frozen G2
v2 results compare RACH-SEQ, which selects the remaining candidate with maximum
current validated NOV, with a matched uniform random-order policy. Panels show
system convergence, fraction of initial confounding edges resolved, observations
used and mechanism-uninformative distractor observations selected across budgets
0–4. Error bars are sample standard deviations across five predeclared seeds;
hidden-truth false exclusion was zero in every policy-by-budget cell.

**Figure 3. Stored-region NOV conditioning and calibration.** Left, resolvability
gains obtained by filtering the current admissible region are compared with fresh
deterministic re-inference for six quantitative observations. Right, predictive
EVSI/NOV is compared with realised resolvability gain across controlled true
states; grey points show individual truths and the highlighted points show the
mean realised gain for each candidate observation.

**Figure S1. Known-truth recovery self-consistency.** Controlled synthetic
switch-state recovery under the unchanged submission defaults and predeclared
pattern-noise strata. The panel is Supplementary validation of inference
self-consistency; confounded switches are not required to become uniquely
recoverable from non-identifying observations.
"""
m = replace_once(m, old_figure, new_figure, "figure captions")
mpath.write_text(m, encoding="utf-8")

# ---------------------------------------------------------------------------
# Submission manifest and workspace README
# ---------------------------------------------------------------------------
manifest_path = ROOT / "paper" / "submission_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["schema_version"] = max(int(manifest.get("schema_version", 0)), 4)
manifest["manuscript_type"] = "Research Article"
for path in (
    "paper/mee_submission_requirements_2026.md",
    "paper/check_mee_submission.py",
    "paper/title_page_draft.md",
    "paper/campanula_primary_literature_audit.md",
):
    if path not in manifest["governance"]:
        manifest["governance"].append(path)
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

rpath = ROOT / "paper" / "README.md"
r = rpath.read_text(encoding="utf-8")
r = replace_once(r, "canonical publication workspace for the RACH methods\nsubmission.", "canonical publication workspace for the RACH **Research Article**\nsubmission.", "paper README article type")
r = replace_once(
    r,
    "| `release_readiness.json` | v0.1.0 package/release freeze record | active release governance |\n",
    "| `release_readiness.json` | v0.1.0 package/release freeze record | active release governance |\n"
    "| `mee_submission_requirements_2026.md` | current MEE Research Article requirements snapshot | active publication governance |\n"
    "| `check_mee_submission.py` | article-type/abstract/anonymity/word-count gate | active publication gate |\n"
    "| `title_page_draft.md` | separate author/title metadata file | Not for Review; human fields pending |\n"
    "| `campanula_primary_literature_audit.md` | source-bounded audit of the prospective example | completed editorial evidence audit |\n",
    "paper README publication file roles",
)
r = r.replace(
    "| G4 worked-example evidence | **Pass for prospective use** | no empirical channel attribution; final source/reference audit remains editorial work |",
    "| G4 worked-example evidence | **Pass for prospective use** | qualitative main-text claims audited against the primary Inoue series; exact historical tables must be transcribed only if future numeric values are introduced |",
)
r = r.replace(
    "work should be limited to journal formatting, final primary-source/reference\nchecking, and external archive/DOI metadata unless a new version/protocol is\nexplicitly opened.",
    "work should be limited to the anonymous reviewer bundle, human-supplied title-page\nmetadata, final document export/line numbering, and external archive/DOI metadata\nunless a new version/protocol is explicitly opened.",
)
rpath.write_text(r, encoding="utf-8")

root_readme = ROOT / "README.md"
rr = root_readme.read_text(encoding="utf-8")
rr = replace_once(
    rr,
    "The active submission is the MEE methods paper defined in\n",
    "The active submission is the MEE **Research Article** defined in\n",
    "root README article type",
)
root_readme.write_text(rr, encoding="utf-8")

# ---------------------------------------------------------------------------
# Make the scientific bundle checker numbering-format agnostic.
# ---------------------------------------------------------------------------
cpath = ROOT / "paper" / "check_submission_bundle.py"
c = cpath.read_text(encoding="utf-8")
old_required = '''    required = [
        "Frozen G2 v2 results below come only",
        "maximum current validated NOV",
        "0.990 ± 0.0079",
        "paper/results/g2_frozen_v2_summary.json",
        "## 2. Exact channel-identifiability boundary",
        "### 2.2 N1:",
        "### 2.3 N2:",
        "### 2.4 N3–N4:",
        "## 3. RACH:",
        "I(S;Q|A_ε)/K",
        "### 4.3 Generality and observation-budget error control",
        "random_order",
        "## 5. Exact ecological projection and ABM boundary",
        "## 6. Prospective worked design:",
    ]
'''
new_required = '''    required = [
        "Frozen G2 v2 results below come only",
        "maximum current validated NOV",
        "0.990 ± 0.0079",
        "paper/results/g2_frozen_v2_summary.json",
        "Exact channel-identifiability boundary",
        "N1: net-only observations cannot identify the changed channel",
        "N2: net performance plus one channel is sufficient",
        "N3–N4: proxy calibration is the operational boundary",
        "RACH: admissible explanations and next-observation design",
        "I(S;Q|A_ε)/K",
        "Generality and observation-budget error control",
        "random_order",
        "Exact ecological projection and ABM boundary",
        "Prospective worked design: Izu Islands *Campanula*",
    ]
'''
c = replace_once(c, old_required, new_required, "format-neutral submission markers")
cpath.write_text(c, encoding="utf-8")

# ---------------------------------------------------------------------------
# Add the permanent MEE formatting check to normal CI.
# ---------------------------------------------------------------------------
cipath = ROOT / ".github" / "workflows" / "ci.yml"
ci = cipath.read_text(encoding="utf-8")
ci = replace_once(
    ci,
    "      - name: Check submission bundle\n        run: python paper/check_submission_bundle.py\n\n      - name: Check repository program boundaries\n",
    "      - name: Check submission bundle\n        run: python paper/check_submission_bundle.py\n\n"
    "      - name: Check MEE Research Article format\n        run: python paper/check_mee_submission.py\n\n"
    "      - name: Check repository program boundaries\n",
    "CI MEE formatting gate",
)
cipath.write_text(ci, encoding="utf-8")

print("MEE Research Article formatting patch complete")
