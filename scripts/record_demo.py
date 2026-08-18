"""
Real Playwright recording of a full live audit through the actual deployed
UI -- submits a real URL, watches a real GitHub Actions run to completion,
then interacts with the finished report. No staged data, no cuts.

Prints a wall-clock timestamp for every major action so DEMO_SCRIPT.md's
timecodes can be built from what actually happened in the recording, not
guessed after the fact.

Run with: apps/agent/.venv/Scripts/python.exe scripts/record_demo.py
"""
import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "https://ai-ux-auditor-inky.vercel.app"
AUDIT_URL = "https://linear.app"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
VIDEO_SIZE = {"width": 1280, "height": 800}

_t0: float | None = None


def mark(label: str) -> None:
    global _t0
    if _t0 is None:
        _t0 = time.time()
    elapsed = time.time() - _t0
    minutes, seconds = divmod(elapsed, 60)
    print(f"[{int(minutes):02d}:{seconds:04.1f}] {label}", flush=True)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIDEO_SIZE,
            record_video_dir=OUT_DIR,
            record_video_size=VIDEO_SIZE,
        )
        page = context.new_page()
        mark("recording started")

        page.goto(BASE_URL, wait_until="networkidle")
        mark("home loaded")
        page.wait_for_timeout(2500)

        page.get_by_role("button", name="Start a free audit").click()
        page.wait_for_load_state("networkidle")
        mark("new audit page")
        page.wait_for_timeout(800)

        page.get_by_role("tab", name="URL").click()
        page.wait_for_timeout(400)
        url_input = page.get_by_placeholder("https://example.com")
        url_input.click()
        url_input.type(AUDIT_URL, delay=45)
        mark(f"typed {AUDIT_URL!r}")
        page.wait_for_timeout(700)

        page.get_by_role("button", name="Run audit").click()
        mark("submitted -- real GitHub Actions workflow_dispatch fires here")
        # "**/audit/*" would also match the current /audit/new page itself
        # (the "new" segment satisfies the wildcard) -- wait for a path that
        # isn't that one, not just any /audit/* match.
        page.wait_for_url(lambda url: "/audit/" in url and not url.rstrip("/").endswith("/audit/new"), timeout=30_000)
        mark(f"live audit view: {page.url}")

        # Watch the real pipeline run live. No polling shortcuts on our end --
        # the page's own Convex live query updates the DOM as the GitHub
        # Actions job reports progress; we just wait and check.
        for i in range(60):
            page.wait_for_timeout(5000)
            text = page.locator("body").inner_text()
            if "Overall UX Score" in text and "/100" in text:
                mark(f"audit complete (check #{i})")
                break
            stage_line = next((line for line in text.splitlines() if line.strip()), "")
            mark(f"still running (check #{i}): {stage_line[:60]}")
        else:
            raise RuntimeError("Audit did not complete within the wait budget")

        page.wait_for_timeout(2200)  # entrance animations + score count-up

        page.get_by_text("THE HEADLINE FINDING").scroll_into_view_if_needed()
        mark("headline finding visible")
        page.wait_for_timeout(2800)

        fix_button = page.get_by_role("button", name="See the")
        fix_button.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        fix_button.click()
        mark("opened See it fixed dialog")
        page.wait_for_timeout(2200)

        page.get_by_role("button", name="Before", exact=True).click()
        mark("toggled to Before")
        page.wait_for_timeout(1800)
        page.get_by_role("button", name="After", exact=True).click()
        mark("toggled to After")
        page.wait_for_timeout(2000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        for tab_name in ["Rule Book", "Copy Editor", "Psychologist", "Design Eye"]:
            page.get_by_role("tab", name=tab_name).click()
            mark(f"tab: {tab_name}")
            page.wait_for_timeout(2400)

        mark("recording ending")
        video = page.video
        context.close()
        browser.close()

        final_path = os.path.join(OUT_DIR, "aura-demo.webm")
        os.replace(video.path(), final_path)
        print(f"saved {final_path}")


if __name__ == "__main__":
    main()
