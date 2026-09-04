"""Validate the active anonymous MEE Research Article submission files."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
SUPPLEMENT = ROOT / "paper" / "supporting_information.md"
TITLE_PAGE = ROOT / "paper" / "title_page_draft.md"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
LICENSE = ROOT / "LICENSE"


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-’'][A-Za-zÀ-ÖØ-öø-ÿ]+)*|\d+(?:\.\d+)?%?", text))


def normalize_prose(text: str) -> str:
    """Collapse Markdown line wrapping before semantic marker checks."""
    return " ".join(text.split()).casefold()


def fail(message: str) -> None:
    raise SystemExit(message)


def assert_anonymous(label: str, text: str) -> None:
    for identifying in ("Ruiqi Zhang", "Kyoto University", "rachelzhang0223", "github.com/zuizui0223"):
        if identifying.lower() in text.lower():
            fail(f"identifying text remains in {label}: {identifying}")
    if re.search(r"(?<![0-9a-f])\b[0-9a-f]{40}\b(?![0-9a-f])", text, flags=re.I):
        fail(f"public Git commit-like SHA remains in {label}")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("manuscript_type") != "Research Article":
        fail("MEE article type must be Research Article")
    if manifest.get("primary_product") != "Mechanism-Resolving Observation Design":
        fail("MEE manifest is not on Mechanism-Resolving Observation Design")

    text = MANUSCRIPT.read_text(encoding="utf-8")
    supplement = SUPPLEMENT.read_text(encoding="utf-8")
    title_page = TITLE_PAGE.read_text(encoding="utf-8")
    assert_anonymous("review manuscript", text)
    assert_anonymous("Supporting Information", supplement)

    required_title_fields = (
        "Article type: **Research Article**", "Ruiqi Zhang", "Kyoto University",
        "Corresponding author", "Running headline", "Acknowledgements",
        "Author contributions", "Statement on inclusion",
        "Ethics and organism/field-study statement", "Data availability", "Funding",
        "Conflict of interest",
    )
    missing_title = [x for x in required_title_fields if x not in title_page]
    if missing_title:
        fail("title page missing required fields:\n- " + "\n- ".join(missing_title))

    inclusion_section = title_page.split("## Statement on inclusion", 1)[1].split(
        "## Ethics and organism/field-study statement", 1
    )[0]
    inclusion_prose = normalize_prose(inclusion_section)
    for marker in ("synthetic benchmark", "does not report place-based empirical research", "not applicable"):
        if marker.casefold() not in inclusion_prose:
            fail(f"Statement on inclusion missing scope marker: {marker}")

    ethics_section = title_page.split("## Ethics and organism/field-study statement", 1)[1].split(
        "## Data availability", 1
    )[0]
    ethics_prose = normalize_prose(ethics_section)
    for marker in ("No new empirical work involving animals, plants or field sites", "synthetic"):
        if marker.casefold() not in ethics_prose:
            fail(f"ethics scope statement missing marker: {marker}")

    if "## Abstract" not in text or "**Data/Code for peer review:**" not in text:
        fail("Abstract or Data/Code for peer review statement missing")
    abstract = text.split("## Abstract", 1)[1].split("**Data/Code for peer review:**", 1)[0].strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", abstract) if p.strip()]
    if len(paragraphs) != 4:
        fail(f"Abstract must contain exactly four numbered paragraphs; found {len(paragraphs)}")
    for i, paragraph in enumerate(paragraphs, start=1):
        if not re.match(rf"^{i}\.\s", paragraph):
            fail(f"Abstract paragraph {i} must start with '{i}.'")
    abstract_words = word_count(abstract)
    if abstract_words > 350:
        fail(f"Abstract exceeds 350 words: {abstract_words}")

    data_pos = text.index("**Data/Code for peer review:**")
    keyword_pos = text.index("**Keywords:**") if "**Keywords:**" in text else -1
    if keyword_pos <= data_pos:
        fail("Keywords must follow the Data/Code for peer review statement")
    if "anonym" not in text[data_pos:keyword_pos].lower():
        fail("Data/Code peer-review statement must promise an anonymised review bundle")

    keyword_tail = text.split("**Keywords:**", 1)[1].split("---", 1)[0].strip()
    keywords = [k.strip().rstrip(".") for k in " ".join(keyword_tail.splitlines()).split(";") if k.strip()]
    if not 1 <= len(keywords) <= 8:
        fail(f"MEE requires 1–8 keywords; found {len(keywords)}")
    if keywords != sorted(keywords, key=str.casefold):
        fail("Keywords are not in alphabetical order: " + "; ".join(keywords))

    required_headings = (
        "## 1. Introduction",
        "## 2. Materials and Methods",
        "## 3. Results",
        "## 4. Software and reproducibility",
        "## 5. Discussion",
        "## Figure captions",
        "### 2.4 AI-assisted development disclosure",
    )
    missing_headings = [h for h in required_headings if h not in text]
    if missing_headings:
        fail("MEE-standard manuscript headings missing:\n- " + "\n- ".join(missing_headings))

    supplement_required = (
        "## S1. Admissible mechanism regions and evidence roles",
        "## S2. Observation information value and sequential design",
        "## S3. Frozen G2 observation-selection benchmark",
        "## S4. Auxiliary controlled checks",
        "## S5. Reproducibility and reviewer bundle",
        "## Figure S1 caption",
    )
    missing_supp = [h for h in supplement_required if h not in supplement]
    if missing_supp:
        fail("Supporting Information sections missing:\n- " + "\n- ".join(missing_supp))

    for retired in ("Restricted Admissible Causal Hypotheses", "RACH-SEQ", "NOV(Q)"):
        if retired in text:
            fail(f"retired active method vocabulary remains in manuscript: {retired}")

    if "## Author contributions" in text or "## ORCID" in text or "## Funding" in text:
        fail("identity/administrative sections must live on the separate title page")

    words = word_count(text)
    if words > 8000:
        fail(f"Research Article exceeds conservative 8000-word gate: {words}")

    if not LICENSE.exists() or "MIT License" not in LICENSE.read_text(encoding="utf-8"):
        fail("MEE code policy requires an open-source licence; MIT LICENSE not found")

    print("MEE submission format OK")
    print("article type: Research Article")
    print("product: Mechanism-Resolving Observation Design")
    print(f"abstract words: {abstract_words}")
    print(f"keywords: {len(keywords)}")
    print(f"conservative manuscript words: {words}")
    print(f"Supporting Information words: {word_count(supplement)}")
    print("title-page inclusion statement: pass")
    print("title-page ethics scope statement: pass")
    print("anonymous manuscript/SI commit-SHA scan: pass")


if __name__ == "__main__":
    main()
