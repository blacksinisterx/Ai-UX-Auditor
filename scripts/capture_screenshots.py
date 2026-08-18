"""
Real Playwright screenshots against the live deployed site, for the
README. Not mockups -- every screenshot here is the actual production
app, driven the same way a real visitor would use it.

Run with: apps/agent/.venv/Scripts/python.exe scripts/capture_screenshots.py
"""
import os
import time

from playwright.sync_api import sync_playwright

BASE_URL = "https://ai-ux-auditor-inky.vercel.app"
COMPLETED_AUDIT_ID = "j97fd3yjb96za9nwcjrxgr38x18cpv96"  # real linear.app audit, already run
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)


def shot(page, name: str) -> None:
    path = os.path.join(OUT_DIR, name)
    page.screenshot(path=path)
    print(f"saved {name}")


def wait_for_image(page, selector: str = "img") -> None:
    """Convex-hosted screenshots are full-page captures (10,000+ px tall in
    this real dataset) -- naturalHeight becomes available as soon as the
    response headers are in, well before the browser finishes decoding
    the actual bitmap for an image this large, so a naturalHeight check
    alone still screenshots as blank. img.decode() explicitly waits for a
    full, paint-ready decode. Targeting a specific selector also matters:
    a dialog's own image mounts after other images already loaded, so a
    blanket "every image on the page is ready" check passes vacuously
    against the old ones while the new one is still decoding."""
    page.locator(selector).first.wait_for(state="attached")
    page.eval_on_selector(selector, "el => el.decode()")


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(500)
        shot(page, "01-home.png")

        page.goto(f"{BASE_URL}/audit/new", wait_until="networkidle")
        page.get_by_role("tab", name="URL").click()
        page.get_by_placeholder("https://example.com").fill("https://linear.app")
        page.wait_for_timeout(300)
        shot(page, "02-new-audit.png")

        page.goto(f"{BASE_URL}/audit/{COMPLETED_AUDIT_ID}", wait_until="networkidle")
        wait_for_image(page, 'img[alt="Annotated screenshot"]')
        page.wait_for_timeout(1200)  # let the report card's entrance animations + score count-up settle
        shot(page, "03-report-card-headline.png")

        # "See it fixed" dialog -- the deterministic contrast-fix preview
        fix_button = page.get_by_role("button", name="See the")
        fix_button.click()
        wait_for_image(page, 'img[alt*="fixed" i]')
        page.wait_for_timeout(300)
        shot(page, "04-see-it-fixed.png")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        # Design Eye tab (default) -- scroll it into view
        page.get_by_text("Layout & structure").scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        shot(page, "05-design-eye-tab.png")

        # Psychologist tab -- real attention-vs-CTA stat cards
        page.get_by_role("tab", name="Psychologist").click()
        page.wait_for_timeout(400)
        shot(page, "06-psychologist-tab.png")

        browser.close()


if __name__ == "__main__":
    main()
