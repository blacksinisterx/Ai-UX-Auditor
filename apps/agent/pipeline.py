"""
Orchestrates a full audit run: capture (if URL) -> OCR/accessibility ->
readability -> score -> saliency + attention insight -> vision critique ->
synthesis (executive summary + copy suggestions) -> annotate -> persist.
Bounded AI calls: exactly one OpenRouter vision call and one Groq call per
audit, per the plan -- the Groq call does more work per call (summary +
rewrites together) rather than adding a second call.
"""
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np
import requests
from convex import ConvexClient

from lenses.accessibility import run_rule_book_lens
from lenses.annotate import draw_issue_overlay
from lenses.attention_utils import compute_attention_insight, heatmap_overlay
from lenses.capture import capture_screenshot
from lenses.copy_editor import run_synthesis_lens
from lenses.readability import score_text_blocks
from lenses.scoring import compute_overall_score, find_cta_candidate
from lenses.vision import run_design_eye_lens

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
TOTAL_STAGES = 6


def _predict_saliency_isolated(image_path: str, tmp_dir: str) -> np.ndarray:
    """Runs saliency prediction in a subprocess -- see run_saliency_subprocess.py
    for why this can never be an in-process import."""
    heatmap_path = os.path.join(tmp_dir, "heatmap.npy")
    subprocess.run(
        [sys.executable, os.path.join(AGENT_DIR, "run_saliency_subprocess.py"), image_path, heatmap_path],
        check=True,
        cwd=AGENT_DIR,
    )
    return np.load(heatmap_path)


def _client() -> ConvexClient:
    return ConvexClient(os.environ["CONVEX_URL"])


def _upload_image(client: ConvexClient, image_path: str) -> str:
    upload_url = client.mutation("files:generateUploadUrl", {})
    with open(image_path, "rb") as f:
        res = requests.post(upload_url, headers={"Content-Type": "image/png"}, data=f)
    res.raise_for_status()
    return res.json()["storageId"]


def _report_progress(client: ConvexClient, audit_id: str, stage: str, done: int, log: list[str]) -> None:
    log.append(stage)
    client.mutation(
        "audits:setProgress",
        {
            "id": audit_id,
            "status": "running",
            "stage": stage,
            "percent": round(done / TOTAL_STAGES * 100),
            "log": log[-10:],
        },
    )


def run_audit(audit_id: str) -> None:
    client = _client()
    log: list[str] = []

    audit = client.query("audits:get", {"id": audit_id})
    if audit is None:
        raise ValueError(f"Audit {audit_id} not found")

    with tempfile.TemporaryDirectory() as tmp:
        screenshot_path = os.path.join(tmp, "screenshot.png")

        _report_progress(client, audit_id, "Capturing screenshot", 0, log)
        if audit["sourceType"] == "url":
            capture_screenshot(audit["sourceUrl"], screenshot_path)
        else:
            res = requests.get(audit["screenshotUrl"])
            res.raise_for_status()
            with open(screenshot_path, "wb") as f:
                f.write(res.content)

        _report_progress(client, audit_id, "Rule Book: OCR + contrast + target size", 1, log)
        rule_book = run_rule_book_lens(screenshot_path)
        texts = [b["text"] for b in rule_book["text_boxes"]]

        readability_results = score_text_blocks(texts)
        flagged_texts = [r["text"] for r in readability_results if r["flagged_low_readability"]]
        overall_score = compute_overall_score(
            rule_book["contrast_issues"], rule_book["size_issues"], readability_results
        )

        _report_progress(client, audit_id, "Psychologist: saliency prediction", 2, log)
        heatmap = _predict_saliency_isolated(screenshot_path, tmp)
        cta = find_cta_candidate(rule_book["size_issues"])
        attention_insight = compute_attention_insight(heatmap, cta) if cta is not None else None
        if attention_insight:
            log.append(
                f"Attention on likely CTA ({attention_insight['ctaText']!r}): "
                f"{attention_insight['overlapPercent']}% of total focus, "
                f"{attention_insight['densityRatio']}x density ratio"
            )

        _report_progress(client, audit_id, "Design Eye: layout critique", 3, log)
        layout_critique = run_design_eye_lens(screenshot_path)

        _report_progress(client, audit_id, "Synthesizing findings", 4, log)
        synthesis = run_synthesis_lens(
            flagged_texts=flagged_texts,
            score=overall_score,
            contrast_fail_count=sum(1 for c in rule_book["contrast_issues"] if not c["passes_wcag_aa"]),
            size_fail_count=sum(1 for s in rule_book["size_issues"] if not s["passes_min_target_size"]),
            attention_insight=attention_insight,
            design_flaw=layout_critique.get("flaw", ""),
        )

        _report_progress(client, audit_id, "Rendering overlays", 5, log)
        annotated = draw_issue_overlay(screenshot_path, rule_book["contrast_issues"], rule_book["size_issues"])
        annotated_path = os.path.join(tmp, "annotated.png")
        cv2.imwrite(annotated_path, annotated)

        heatmap_img = heatmap_overlay(screenshot_path, heatmap)
        heatmap_path = os.path.join(tmp, "heatmap.png")
        cv2.imwrite(heatmap_path, heatmap_img)

        annotated_storage_id = _upload_image(client, annotated_path)
        heatmap_storage_id = _upload_image(client, heatmap_path)

        client.mutation(
            "auditResults:submit",
            {
                "auditId": audit_id,
                "overallScore": overall_score,
                "executiveSummary": synthesis["executiveSummary"],
                "layoutCritique": layout_critique,
                "copySuggestions": synthesis["copySuggestions"],
                "contrastIssues": rule_book["contrast_issues"],
                "sizeIssues": rule_book["size_issues"],
                "readability": readability_results,
                "attentionInsight": attention_insight,
                "saliencyHeatmapStorageId": heatmap_storage_id,
                "annotatedImageStorageId": annotated_storage_id,
            },
        )
        client.mutation("audits:markDone", {"id": audit_id})
