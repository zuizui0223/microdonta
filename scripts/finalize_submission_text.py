"""Integrate already-frozen submission results into the active RACH text.

This script does not run or tune any benchmark. It performs deterministic text
replacements after G2 v2, known-truth, and NOV calibration have been frozen.
Every replacement is guarded so unexpected manuscript drift fails loudly.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, found {count}")
    return updated


def update_manuscript() -> None:
    path = ROOT / "paper" / "mee_manuscript_draft.md"
    text = path.read_text(encoding="utf-8")

    text = regex_once(
        text,
        r"> \*\*Working draft for Methods in Ecology and Evolution\.\*\* This theorem-first\n> draft supersedes the pre-theorem manuscript archived under\n> `paper/archive/`\. Numerical benchmark statements remain subject to the final\n> frozen submission run and table; pre-fix generality percentages are deliberately\n> absent from this draft until replaced by protocol-tagged frozen outputs\.",
        "> **Submission-track draft for Methods in Ecology and Evolution.** This theorem-first\n> draft supersedes the pre-theorem manuscript archived under `paper/archive/`.\n> Frozen G2 v2 results below come only from the protocol/code-tagged result bundle\n> `paper/results/g2_frozen_v2_summary.json`; the pre-fix generality percentages\n> remain excluded from the active manuscript.",
        "manuscript status note",
    )

    abstract_old = (
        "A preregistered synthetic selection benchmark challenges\n"
        "RACH-SEQ with mechanism-uninformative distractor measurements and compares its\n"
        "observation choices with a matched random candidate-order baseline while tracking\n"
        "hidden-truth false exclusion."
    )
    abstract_new = abstract_old + (
        " At an observation budget of two, RACH-SEQ resolved all initial confounding\n"
        "edges on average and fully converged in 99.0% of systems, versus 60.45% edge\n"
        "resolution and 43.5% convergence under random order; no hidden true explanation\n"
        "was excluded in any frozen policy-by-budget cell."
    )
    text = replace_once(text, abstract_old, abstract_new, "abstract G2 result")

    text = regex_once(
        text,
        r"\*\*Closing the loop \(RACH-SEQ\)\.\*\* Single-shot RACH evaluates what is worth\nmeasuring \*now\*; RACH-SEQ iterates after observations arrive\..*?Hidden synthetic truth is used only \*after\* candidate ranking to materialise a\nbenchmark outcome\.",
        "**Closing the loop (RACH-SEQ).** Single-shot RACH evaluates what is worth\n"
        "measuring *now*; RACH-SEQ iterates the same information objective after each\n"
        "observation arrives. At step `t`, every remaining candidate whose outcome map\n"
        "forms a verified partition of the current admissible region is scored by\n"
        "`NOV_t(Q)=I(S;Q|A_{ε,t})/K`; the candidate with the largest positive current NOV\n"
        "is selected, the realised outcome conditions `A_{ε,t}`, and all predictive\n"
        "distributions and NOV values are recomputed. The mechanism-equivalence graph and\n"
        "confounding-edge cuts are structural diagnostics and validation outcomes, not a\n"
        "second primary utility. If a candidate lacks a verified predictive partition,\n"
        "RACH-SEQ may use the explicit compatibility score `expected_edge_cuts /\n"
        "current_edge_count`, recorded as `normalized_edge_cut_fallback`; that score is\n"
        "never called validated NOV. A declared outcome prior can be used only to\n"
        "materialise an otherwise unavailable outcome in this fallback path, with its\n"
        "probability source reported. Hidden synthetic truth is used only *after* candidate\n"
        "selection to materialise a benchmark outcome.",
        "RACH-SEQ closing-loop definition",
    )

    text = replace_once(
        text,
        "RACH-SEQ      choose the remaining candidate with maximum expected confounding-edge cuts\nrandom_order  choose uniformly among remaining candidates",
        "RACH-SEQ      choose the remaining candidate with maximum current validated NOV\nrandom_order  choose uniformly among remaining candidates",
        "G2 policy block",
    )

    text = replace_once(
        text,
        "candidate has been chosen is its hidden benchmark outcome materialised and the\ncurrent admissible region conditioned on that observation. RACH-SEQ recomputes\ncandidate outcome probabilities from current `A_ε` whenever a verified partition\nis available. Random-order selection is an uninformed **selection baseline**, not\nan alternative causal model.",
        "candidate has been chosen is its hidden benchmark outcome materialised and the\ncurrent admissible region conditioned on that observation. RACH-SEQ recomputes\n`NOV(Q)=I(S;Q|A_ε)/K` from the current region at every step and selects the\nhighest-valued verified candidate; the normalized edge-cut fallback is used only\nwhen a predictive partition is not estimable. Random-order selection is an\nuninformed **selection baseline**, not an alternative causal model.",
        "G2 policy semantics",
    )

    result_paragraph = (
        "Frozen v2 results were decisive without any performance acceptance threshold. "
        "At budget 2 (mean ± sample SD across five predeclared seeds; 1,000 systems per "
        "policy), RACH-SEQ resolved 1.000 ± 0.000 of initial confounding edges, fully "
        "converged in 0.990 ± 0.0079 of systems, used 1.505 ± 0.030 observations, and "
        "selected only 0.001 ± 0.0022 distractors. Under the matched random-order policy, "
        "the corresponding values were 0.6045 ± 0.0231 edge resolution, 0.435 ± 0.0355 "
        "convergence, 1.821 ± 0.024 observations, and 0.974 ± 0.0277 distractors. The "
        "within-seed RACH-SEQ minus random contrast was therefore +0.3955 ± 0.0231 for "
        "edge resolution and +0.555 ± 0.0417 for convergence, while using 0.316 ± 0.020 "
        "fewer observations. Hidden-truth false exclusion was 0 in every policy × budget "
        "cell, and all 10,000 system-policy-budget records retained the hidden true "
        "explanation. At budget 1, convergence was 0.495 for RACH-SEQ versus 0.179 for "
        "random order; by budget 4 both policies resolved all initial edges on average, "
        "but RACH-SEQ still converged in 0.999 versus 0.940 of systems while using 1.518 "
        "versus 2.673 observations. These values come exclusively from the frozen result "
        "bundle `paper/results/g2_frozen_v2_summary.json` (protocol SHA-256 "
        "`3568025f98a671b232e5d6b865063f37baa5bec319a594f831d6b5b953428cb7`; execution "
        "commit `f343c2361db28c0b3e528b882b3370eda5abf5ed`).\n\n"
    )
    marker = "The comparison is deliberately **not an acceptance criterion**."
    if result_paragraph.strip() not in text:
        text = replace_once(text, marker, result_paragraph + marker, "frozen G2 result insertion")

    text = replace_once(
        text,
        "whether a sequential structural observation policy reduces\nmechanism ambiguity",
        "whether a sequential information-theoretic observation policy reduces\nmechanism ambiguity",
        "G2 claim wording",
    )

    path.write_text(text, encoding="utf-8")


def update_theory() -> None:
    path = ROOT / "docs" / "rach_theory.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    rank candidates by expected confounding-edge cuts\n    take the highest-ranked available observation",
        "    rank verified candidates by current NOV = I(S;Q | A_{t-1}) / K\n    use normalized edge-cut fallback only when NOV is not estimable\n    take the highest-valued available observation",
        "theory sequence pseudocode",
    )
    text = replace_once(
        text,
        "RACH-SEQ is intentionally broader than validated single-shot EVSI. A field-design candidate whose outcome map does not form a verified stored-region partition may still be ranked using a **predeclared outcome prior as an explicit fallback**. That probability source is recorded in each sequence step. Such a fallback ranking is not relabelled as the validated `I(S;Q|A)/K` quantity.",
        "For every candidate with a verified stored-region outcome partition, RACH-SEQ uses exactly the same validated objective as single-shot NOV: `I(S;Q|A)/K`. A field-design candidate whose outcome map does not identify that quantity may still be ranked by the explicit compatibility score `expected_edge_cuts / current_edge_count`. The score source is recorded in each sequence step. A predeclared outcome prior may be used only to materialise an otherwise unavailable outcome in that fallback path; neither the fallback score nor its prior is relabelled as validated NOV.",
        "theory fallback boundary",
    )
    path.write_text(text, encoding="utf-8")


def update_mainline() -> None:
    path = ROOT / "docs" / "mainline.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "RACH-SEQ is slightly broader because it must still be able to rank a declared\nfield-design candidate set. At each sequential step it uses\n`Pr(q | current A_epsilon)` when a partition is verified; otherwise it may use a\npredeclared outcome prior as an explicit fallback. Every step records which\nprobability source was used. Thus fallback ranking is transparent and is never\nconfused with the validated single-shot `I(S;Q|A_epsilon)/K` quantity.",
        "RACH-SEQ is the sequential closure of validated NOV. At each step, every\ncandidate whose outcomes form a verified partition of current `A_epsilon` is\nranked by `I(S;Q | current A_epsilon)/K`, and the largest positive current NOV is\nselected. Candidates whose predictive maps are not estimable may use only the\nexplicit compatibility score `expected_edge_cuts / current_edge_count`, recorded\nas `normalized_edge_cut_fallback`; a declared prior may materialise a fallback\noutcome but does not become the ranking utility. Every step records score and\nprobability provenance.",
        "mainline sequence boundary",
    )
    text = replace_once(
        text,
        "rach_seq      choose by expected confounding-edge cuts\nrandom_order  choose uniformly among remaining candidates",
        "rach_seq      choose maximum current validated NOV; explicit fallback only if NOV is not estimable\nrandom_order  choose uniformly among remaining candidates",
        "mainline G2 policy block",
    )
    path.write_text(text, encoding="utf-8")


def update_readme() -> None:
    path = ROOT / "paper" / "README.md"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "RACH-SEQ      expected confounding-edge-cut selection\nrandom_order  uniform random remaining-candidate selection",
        "RACH-SEQ      maximum current validated NOV; explicit fallback only if NOV is not estimable\nrandom_order  uniform random remaining-candidate selection",
        "README G2 policies",
    )
    text = regex_once(
        text,
        r"\| G2 benchmark validity \| \*\*Partial\*\* \| .*? \|",
        "| G2 benchmark validity | **Pass** | frozen v2 executed with protocol/code provenance; known-truth and NOV defaults rerun; final numbers fixed in `paper/results/` |",
        "README G2 status",
    )
    text = replace_once(
        text,
        "**G2 numerical quarantine.** The pre-fix 99.2%/98.5% generality values are not\nsubmission evidence and CI forbids them from re-entering the active manuscript.\nThe frozen v2 runner has no favourable performance threshold. Whatever the\nprotocol-tagged result returns is the result to report.",
        "**G2 numerical provenance.** The pre-fix 99.2%/98.5% generality values are not\nsubmission evidence and CI forbids them from re-entering the active manuscript.\nThe accepted values are only those in `paper/results/g2_frozen_v2_summary.json`,\nwhich are tied to the frozen protocol SHA and execution commit. The protocol had\nno favourable performance threshold; the observed favourable policy contrast is\na result, not a software acceptance condition.",
        "README G2 provenance",
    )
    path.write_text(text, encoding="utf-8")


def update_checker() -> None:
    path = ROOT / "paper" / "check_submission_bundle.py"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '        "Numerical benchmark statements remain subject",',
        '        "Frozen G2 v2 results below come only",\n        "        \\\"maximum current validated NOV\\\",",\n        "        \\\"0.990 ± 0.0079\\\",",\n        "        \\\"paper/results/g2_frozen_v2_summary.json\\\",",',
        "checker frozen markers",
    )
    text = replace_once(
        text,
        '        "98.5% of systems fully converging",',
        '        "98.5% of systems fully converging",\n        "        \\\"maximum expected confounding-edge cuts\\\",",\n        "        \\\"rank candidates by expected confounding-edge cuts\\\",",',
        "checker old objective ban",
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    update_manuscript()
    update_theory()
    update_mainline()
    update_readme()
    update_checker()
    print("submission text integration complete")


if __name__ == "__main__":
    main()
