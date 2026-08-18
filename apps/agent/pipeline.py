"""
Orchestrates a full audit run: capture (if URL) -> OCR/accessibility ->
readability -> saliency -> vision critique -> copy suggestions -> score ->
annotate -> persist. Bounded AI calls: exactly one OpenRouter vision call
and one Groq call per audit, per the plan.
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
from lenses.attention_utils import box_attention_overlap, heatmap_overlay
from lenses.capture import capture_screenshot
from lenses.copy_editor import run_copy_editor_lens
from lenses.readability import score_text_blocks
from lenses.scoring import compute_overall_score, find_cta_candidate
from lenses.vision import run_design_eye_lens

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))


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

TOTAL_STAGES = 6


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

        _report_progress(client, audit_id, "Copy Editor: readability scoring", 2, log)
        readability_results = score_text_blocks(texts)
        flagged_texts = [r["text"] for r in readability_results if r["flagged_low_readability"]]
        copy_suggestions = run_copy_editor_lens(flagged_texts) if flagged_texts else []

        _report_progress(client, audit_id, "Psychologist: saliency prediction", 3, log)
        heatmap = _predict_saliency_isolated(screenshot_path, tmp)
        cta = find_cta_candidate(rule_book["size_issues"])
        if cta is not None:
            b = cta["box"]
            overlap = box_attention_overlap(heatmap, b["x0"], b["y0"], b["x1"], b["y1"])
            log.append(f"Attention on likely CTA ({cta['text']!r}): {overlap:.1%} of total focus")

        _report_progress(client, audit_id, "Design Eye: layout critique", 4, log)
        layout_critique = run_design_eye_lens(screenshot_path)

        _report_progress(client, audit_id, "Scoring + rendering overlays", 5, log)
        overall_score = compute_overall_score(
            rule_book["contrast_issues"], rule_book["size_issues"], readability_results
        )

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
                "layoutCritique": layout_critique,
                "copySuggestions": copy_suggestions,
                "contrastIssues": rule_book["contrast_issues"],
                "sizeIssues": rule_book["size_issues"],
                "readability": readability_results,
                "saliencyHeatmapStorageId": heatmap_storage_id,
                "annotatedImageStorageId": annotated_storage_id,
            },
        )
        client.mutation("audits:markDone", {"id": audit_id})
