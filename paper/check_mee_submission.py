"""Validate the active manuscript against current MEE Research Article rules.

This is an initial-submission formatting gate. It does not replace the scientific
submission-bundle, repository-boundary, G2 or G5 checks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "paper" / "mee_manuscript_draft.md"
TITLE_PAGE = ROOT / "paper" / "title_page_draft.md"
MANIFEST = ROOT / "paper" / "submission_manifest.json"
LICENSE = ROOT / "LICENSE"


def word_count(text: str) -> int:
    # Conservative review-manuscript count: prose, references, captions,
    # statements and numeric tokens all count. Markdown punctuation does not.
    return len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[-’'][A-Za-zÀ-ÖØ-öø-ÿ]+)*|\d+(?:\.\d+)?%?", text))


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("manuscript_type") != "Research Article":
        fail("MEE article type must be Research Article")

    text = MANUSCRIPT.read_text(encoding="utf-8")
    title_page = TITLE_PAGE.read_text(encoding="utf-8")

    # Double-anonymous main article.
    for identifying in ("Ruiqi Zhang", "Kyoto University", "rachelzhang0223"):
        if identifying.lower() in text.lower():
            fail(f"identifying text remains in review manuscript: {identifying}")

    if "github.com/zuizui0223" in text.lower():
        fail("public identifying repository URL remains in review manuscript")

    required_title_fields = (
        "Article type: **Research Article**",
        "Ruiqi Zhang",
        "Kyoto University",
        "Corresponding author",
        "Running headline",
        "Acknowledgements",
        "Author contributions",
        "Data availability",
        "Funding",
        "Conflict of interest",
    )
    missing_title = [x for x in required_title_fields if x not in title_page]
    if missing_title:
        fail("title page missing required fields:\n- " + "\n- ".join(missing_title))

    # Abstract must be exactly four numbered paragraphs and <=350 words.
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
    between = text[data_pos:keyword_pos]
    if "anonym" not in between.lower():
        fail("Data/Code peer-review statement must promise an anonymised review bundle")

    keyword_tail = text.split("**Keywords:**", 1)[1].split("---", 1)[0].strip()
    keyword_line = " ".join(keyword_tail.splitlines())
    keywords = [k.strip().rstrip(".") for k in keyword_line.split(";") if k.strip()]
    if not 1 <= len(keywords) <= 8:
        fail(f"MEE requires 1–8 keywords; found {len(keywords)}")
    if keywords != sorted(keywords, key=str.casefold):
        fail("Keywords are not in alphabetical order: " + "; ".join(keywords))

    required_headings = (
        "## 1. Introduction",
        "## 2. Materials and Methods",
        "## 3. Results",
        "## 5. Discussion",
        "## Figure captions",
        "### 2.3 AI-assisted development disclosure",
    )
    missing_headings = [h for h in required_headings if h not in text]
    if missing_headings:
        fail("MEE-standard manuscript headings missing:\n- " + "\n- ".join(missing_headings))

    if "## Author contributions" in text or "## ORCID" in text or "## Funding" in text:
        fail("identity/administrative sections must live on the separate title page")

    words = word_count(text)
    if words > 8000:
        fail(f"Research Article exceeds conservative 8000-word gate: {words}")

    if not LICENSE.exists() or "MIT License" not in LICENSE.read_text(encoding="utf-8"):
        fail("MEE code policy requires an open-source licence; MIT LICENSE not found")

    print("MEE submission format OK")
    print("article type: Research Article")
    print(f"abstract words: {abstract_words}")
    print(f"keywords: {len(keywords)}")
    print(f"conservative manuscript words: {words}")


if __name__ == "__main__":
    main()
