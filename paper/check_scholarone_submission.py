"""Validate the MEE ScholarOne upload contract without pretending human metadata is complete."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT / "paper" / "scholarone_upload_manifest.json"
READINESS = ROOT / "paper" / "release_readiness.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_text(relative: str) -> str:
    path = ROOT / relative
    if not path.exists():
        fail(f"ScholarOne source file missing: {relative}")
    return path.read_text(encoding="utf-8")


def assert_anonymous(label: str, text: str) -> None:
    forbidden = ("Ruiqi Zhang", "Kyoto University", "rachelzhang0223", "github.com/zuizui0223")
    hits = [token for token in forbidden if token.casefold() in text.casefold()]
    if hits:
        fail(f"{label} is not anonymous: {', '.join(hits)}")
    if re.search(r"(?<![0-9a-f])\b[0-9a-f]{40}\b(?![0-9a-f])", text, flags=re.I):
        fail(f"{label} contains a public commit-like SHA")


def main() -> None:
    upload = load_json(UPLOAD)
    readiness = load_json(READINESS)

    if upload.get("journal") != "Methods in Ecology and Evolution":
        fail("ScholarOne manifest targets the wrong journal")
    if upload.get("article_type") != "Research Article":
        fail("ScholarOne manifest must use Research Article")
    if upload.get("submission_system") != "ScholarOne Manuscripts":
        fail("submission system is not ScholarOne Manuscripts")
    if upload.get("submission_url") != "https://mc.manuscriptcentral.com/mee-besjournals":
        fail("MEE ScholarOne URL drifted")
    if upload.get("validated_artifact_sha") != readiness.get("artifact_validation_sha"):
        fail("ScholarOne contract does not point to the validated artifact SHA")

    uploads = {entry["slot"]: entry for entry in upload.get("uploads", [])}
    required_slots = {
        "main_document", "title_page", "supporting_information",
        "anonymous_code_for_peer_review", "cover_letter",
    }
    if set(uploads) != required_slots:
        fail(f"ScholarOne upload slots drifted: {sorted(set(uploads))}")

    main_doc = uploads["main_document"]
    title_page = uploads["title_page"]
    supp = uploads["supporting_information"]
    code = uploads["anonymous_code_for_peer_review"]
    cover = uploads["cover_letter"]

    if main_doc.get("scholarone_designation") != "Main Document":
        fail("main document must use ScholarOne designation Main Document")
    if not main_doc.get("reviewer_visible") or not main_doc.get("anonymous"):
        fail("main document must be anonymous and reviewer-visible")
    if title_page.get("scholarone_designation") != "Supplemental Document Not for Review":
        fail("title page must be Supplemental Document Not for Review")
    if title_page.get("reviewer_visible") or title_page.get("anonymous"):
        fail("title page visibility/anonymity contract is wrong")
    if not supp.get("reviewer_visible") or not supp.get("anonymous"):
        fail("Supporting Information must remain anonymous and reviewer-visible")
    if not code.get("reviewer_visible") or not code.get("anonymous"):
        fail("peer-review code bundle must remain anonymous and reviewer-visible")
    if cover.get("required"):
        fail("cover letter is optional under current MEE guidance")

    main_text = source_text(main_doc["source"])
    title_text = source_text(title_page["source"])
    supp_text = source_text(supp["source"])
    source_text(cover["source"])
    assert_anonymous("Main Document source", main_text)
    assert_anonymous("Supporting Information source", supp_text)

    frozen_figures = readiness["g5"]["figures"]
    expected_main_figures = {
        "figure1_controlled_confounding.png",
        "figure2_g2_frozen_v2.png",
        "figure3_information_value_calibration.png",
    }
    expected_supp_figures = {"figureS1_known_truth.png"}
    main_figures = set(main_doc["assembly"]["figures_embedded_or_appended"])
    supp_figures = set(supp["assembly"]["figures_embedded_or_appended"])
    if main_figures != expected_main_figures:
        fail(f"Main Document figure assembly drifted: {sorted(main_figures)}")
    if supp_figures != expected_supp_figures:
        fail(f"Supporting Information figure assembly drifted: {sorted(supp_figures)}")
    if not (expected_main_figures | expected_supp_figures).issubset(frozen_figures):
        fail("ScholarOne figure assembly is not covered by frozen G5 hashes")

    reviewer = readiness["reviewer_bundle"]
    for key in ("artifact_id", "artifact_name", "artifact_digest", "internal_bundle_sha256"):
        if code.get(key) != reviewer.get(key):
            fail(f"peer-review code artifact mismatch for {key}")

    blockers: list[str] = []
    for blocker in upload.get("human_blockers", []):
        blocker_id = blocker["id"]
        source = blocker.get("source")
        marker = blocker.get("marker")
        if marker and marker in source_text(source):
            blockers.append(blocker_id)

    ai_section = main_text.split("### 2.4 AI-assisted development disclosure", 1)[1].split(
        "### 2.5 Controlled validation design", 1
    )[0]
    if "OpenAI ChatGPT" not in ai_section:
        fail("AI disclosure no longer names OpenAI ChatGPT")
    if not re.search(r"(?:GPT[-\s]?\d|model version|application version)", ai_section, flags=re.I):
        if "chatgpt_application_version" not in blockers:
            blockers.append("chatgpt_application_version")

    declared_blockers = {item["id"] for item in upload.get("human_blockers", [])}
    if set(blockers) - declared_blockers:
        fail("undeclared ScholarOne blocker detected: " + ", ".join(sorted(set(blockers) - declared_blockers)))

    status = upload.get("status")
    if blockers and status != "pre_export_blocked_on_human_metadata":
        fail("ScholarOne status must remain blocked while human metadata placeholders remain")
    if not blockers and status != "ready_for_final_export":
        fail("all blockers are resolved but ScholarOne status was not advanced to ready_for_final_export")

    confirmations = upload.get("submission_confirmations", [])
    if len(confirmations) != 6:
        fail("ScholarOne submission confirmation checklist is incomplete")

    print("ScholarOne upload contract OK")
    print("journal: Methods in Ecology and Evolution")
    print("system: ScholarOne Manuscripts")
    print("validated artifact SHA: " + upload["validated_artifact_sha"])
    print("required reviewer-visible uploads: Main Document, Supporting Information, anonymous code bundle")
    print("title page: Supplemental Document Not for Review")
    print("frozen Figure 1-3/S1 coverage: pass")
    print("anonymous reviewer artifact identity: pass")
    print("human blockers: " + (", ".join(sorted(blockers)) if blockers else "none"))
    print("submission status: " + status)


if __name__ == "__main__":
    main()
