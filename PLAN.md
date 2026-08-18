# Aura — AI UX Auditor: Build Plan

## Context

Aura is a screenshot/URL-in, UX-audit-report-out tool: upload a UI screenshot or paste a URL, and get back a scored report card with concrete, cited feedback across four "lenses" (layout, accessibility, copy, attention). The user has a spec for this from about a year ago, but it leans on infrastructure that doesn't hold up for a real deployed product: Streamlit for the UI, LLaVA + Zephyr-7B self-hosted on Colab GPU. Streamlit isn't a real frontend for a portfolio deliverable, and Colab GPU isn't deployable/automatable — it needs a human babysitting a notebook, which breaks the "agent that actually runs" story this whole series of builds is going for.

This is the fourth in the same "deep agent" portfolio series (Exploit-Path-Tracer, Deposition-Contradiction-Finder, AI Video Narrator), and gets the same treatment: a real deployable frontend, free-tier cloud compute instead of a manual notebook, and the lessons already paid for in the first three builds applied from day one instead of rediscovered.

**Provider decision (confirmed with the user):** Groq for the text lens (reusing the proven, stable pattern from the first two builds) + OpenRouter's free vision models for the image lens, rather than a single Gemini key. Tradeoff accepted: OpenRouter's free vision roster is more volatile (14 free model IDs as of Aug 2026, was 15-20 recently) and rate-limited (~20 req/min, ~200/day) — mitigated below by keeping the vision call's job narrow (qualitative critique only, not precise coordinates) and by naming a documented fallback.

**Data layer pivot (confirmed with the user, mid-build):** Supabase's free tier caps active projects at 2 *per account* across every org that account owns/administers — not per org as initially assumed — and the user's account already has 2 live projects from the first two builds. Rather than pause one of those (would take a live portfolio deliverable offline) or fragment ownership across a second email, this build uses **Convex** instead of Supabase: free tier, no card, 20 projects, and its queries are live-subscribed by default (arguably a better fit for "live audit progress" than wiring a separate Realtime channel). A Convex project already exists: team `storm-creator`, project `ai-ux-auditor`, dev deployment `chatty-emu-813` (Cloud URL `https://chatty-emu-813.convex.cloud`). The official `convex` PyPI package gives the GitHub Actions Python job the same direct-write capability the prior builds got from `supabase-py`. Every other section of this plan that mentions Supabase should be read as Convex; see the Data model and GitHub Actions sections below for the concrete shape.

## Research grounding (Aug 2026, current — see chat for full source links)

- **Groq**: genuinely free tier, no card, no per-token charge, rate-limited only — same deal as the last two builds. Its vision models are explicitly preview-only and get deprecated often (Llama 4 Maverick vision was dropped Feb 2026), so **Groq is text-only in this build**, not used for the vision lens. **Verified directly, not assumed**: `llama-3.3-70b-versatile` (the model the last two builds used) is gone from Groq's lineup entirely as of this build — `GET /models` no longer lists it at all. Switched to **`openai/gpt-oss-120b`** (OpenAI's open-weight model, hosted on Groq, currently listed and working) after confirming it with a real call.
- **OpenRouter free vision models**: **verified directly, not assumed** — the originally-planned pinned model `google/gemma-4-31b-it:free` hit a 429 "temporarily rate-limited upstream" on the very first real request, on a fresh key. Switched the primary choice to **`openrouter/free`** (the auto-router across whatever's currently free), which routed around the rate limit immediately on retry. `google/gemma-4-31b-it:free` is kept as a documented pinned alternative, not the default — check `openrouter.ai/models?fmt=free` if the auto-router itself ever needs bypassing.
- **PaddleOCR**: the 2026-recommended most-accurate free/open OCR, handles layout/tables better than EasyOCR (which multiple 2026 reviews now say to skip). Used for real, pixel-positioned text extraction — this is the deterministic backbone the accessibility lens depends on, not vibes from an LLM.
- **Saliency prediction**: no free API exists for this (it's a specialized pixel-output CV task, not something an LLM does), so it has to be a real local model. MSI-Net is confirmed available pre-trained on HuggingFace Hub/Kaggle Hub with a CPU-inference config — this is the primary pick since it's verifiably obtainable. GreenSaliency (0.038s/image, CPU-only, per its 2024 paper) is a faster stretch alternative if its weights turn out to be easily obtainable during Build Order step 4 below — don't block on it.
- **Playwright + GitHub Actions**: standard, well-documented, works headless on `ubuntu-latest` out of the box — this is how URL input gets turned into a screenshot.

## Lessons carried over from the first three builds

1. **Agent compute goes straight to GitHub Actions `workflow_dispatch`.** This directly replaces the old spec's Colab GPU step — no notebook, no human babysitting, no GPU needed at all (every model below runs fine on a GH Actions CPU runner; see research grounding).
2. **Bound total LLM/VLM calls up front.** Exactly one OpenRouter vision call and one Groq text call per audit (the text call batches *all* flagged copy into one prompt, not one call per snippet) — never O(n) per UI element.
3. **Never name custom Tailwind v4 theme tokens with a `--spacing-*` prefix** — reserved namespace, hijacks `max-w-*`/`w-*`/`gap-*`/`p-*`. Use `--space-*`.
4. **Check which shadcn base this install uses (Radix vs Base UI) before wiring `Button` + `Link`** — the last two projects differed on this (`asChild`+Slot vs `render=`+`nativeButton={false}`); don't assume, check the installed component source on day one.
5. **Full design system pass from day one** — load `ui-ux-pro-max` + `frontend-design-pro` + `motion-dev-animations` during the initial build, not as a redesign afterward. (Extra-relevant here: a UX-audit tool with a mediocre UI would be an unforced irony.)
6. **Any autoscroll/UX-polish effect must be scoped and explicit** — no blanket `useEffect([messages])` calling `scrollIntoView()`.
7. **Verify every tool against real infrastructure before building the next layer on it** — in order: OCR/accessibility math first (step 3 below), then the saliency model (step 4), then the two AI calls (step 5), *then* wire it all into the Actions workflow (step 6). Never assume a library or model behaves as documented without running it against a real screenshot first.
8. **Uploaded files are a trust boundary** — validate uploaded screenshot file type/size before it touches PaddleOCR/Pillow; if URL input is used, the headless browser fetch is itself an SSRF-shaped surface (reject non-http(s) schemes, reject localhost/private-IP targets).
9. **Reuse the proven direct-upload + Vercel-API-dispatches-GitHub-Actions pattern**, copying the shape (not specifics) from the last two builds' `apps/web/app/api/scans/route.ts` + `.github/workflows/scan.yml` — adapted to Convex (see Data layer pivot below) instead of Supabase for this build.
10. **Verification methodology**: real Playwright scripts against the actual deployed site for every README/demo claim — no mockups, no localhost-only claims.
11. **New, fully independent infra** (new GitHub repo, new Supabase project, new Vercel project) — same as every prior build, not shared.

## The core "proof of real reasoning" mechanic

Same narrative device as the false-positive dismissal (Exploit-Path-Tracer) and the "looks contradictory but isn't" case (Deposition-Contradiction-Finder), adapted to UX: the demo fixture needs at least one **objectively checkable disagreement between how a screenshot *looks* and what the real math says**, in both directions:

- A CTA that's styled to look visually dominant (bright, large) by eyeballing, but the saliency heatmap's actual peak lands somewhere else (a competing bright hero image, say) — attention that demonstrably doesn't go where the design implies. This is checkable by literally testing whether the heatmap's peak-intensity region overlaps the CTA's bounding box — a real number, not an LLM opinion.
- A text/background color pair that looks borderline to the eye but is either a real WCAG contrast pass or fail by the numbers — the accessibility lens has to get this right using actual sampled pixel colors and the real contrast formula, not a guess.

Both checks are pure deterministic code (contrast math, heatmap-vs-bbox overlap), which is exactly what makes them a credible "real tool, not an LLM wrapper" proof point, mirroring the `parse_documents`/Semgrep role from the prior two builds.

## Pipeline (one GitHub Actions job per audit, bounded AI calls)

```
input (screenshot upload OR url)
  → if url: Playwright headless screenshot (validated scheme/host first)
  → preprocess (resize/normalize, Pillow)
  → PaddleOCR                                    [deterministic] → text + pixel bounding boxes
  → accessibility checks                         [deterministic] → contrast ratios (sampled pixel colors
                                                                     at OCR boxes vs local background, real
                                                                     WCAG formula) + target-size pass/fail
                                                                     (OCR/CV box dimensions vs 44x44 min)
  → textstat readability scoring                 [deterministic]
  → MSI-Net saliency heatmap                     [real local CV model, CPU] → heatmap image + peak region
  → 1x OpenRouter vision call (openrouter/free)   [AI] → qualitative layout/hierarchy/whitespace/CTA critique
                                                          (text only -- do NOT depend on this model for
                                                          precise bounding-box coordinates, unverified for
                                                          a free/smaller vision model; OCR boxes + simple
                                                          CV contour detection cover the geometry instead)
  → 1x Groq call (openai/gpt-oss-120b)            [AI] → batched copy clarity/rewrite suggestions, given
                                                          all flagged low-readability text at once
  → combine: deterministic UX score formula (contrast pass rate, size pass rate, readability score,
    heatmap-vs-CTA overlap) + the two AI call outputs folded in as narrative sections
  → persist result + annotated images to Convex
```

## Data model (Convex project `ai-ux-auditor`, team `storm-creator`, dev deployment `chatty-emu-813`)

`convex/schema.ts`:

```ts
export default defineSchema({
  audits: defineTable({
    sourceType: v.union(v.literal("url"), v.literal("screenshot")),
    sourceUrl: v.optional(v.string()),
    screenshotStorageId: v.optional(v.id("_storage")),
    status: v.string(),
    progress: v.optional(v.any()),
    completedAt: v.optional(v.number()),
  }),
  auditResults: defineTable({
    auditId: v.id("audits"),
    overallScore: v.number(),
    layoutCritique: v.string(),          // from the OpenRouter vision call
    copySuggestions: v.any(),            // from the Groq call
    contrastIssues: v.any(),
    sizeIssues: v.any(),
    readability: v.any(),
    saliencyHeatmapStorageId: v.id("_storage"),
    annotatedImageStorageId: v.id("_storage"),
  }).index("by_audit", ["auditId"]),
});
```

Simpler than the prior two builds' schemas on purpose — this is a single-report product (one audit → one result), not a multi-finding list product, so there's no separate findings/messages table needed. File storage (screenshot, heatmap, annotated image) uses Convex's built-in file storage (`ctx.storage.generateUploadUrl()` for direct client upload, `ctx.storage.store()`/`ctx.storage.getUrl()` from the Actions job) — same direct-upload shape as the prior builds' Supabase Storage bucket, just Convex's native equivalent. No RLS to configure; Convex functions define their own access rules in code.

## Frontend (new Next.js app: Next.js + Tailwind v4 + shadcn/ui + Motion — no Streamlit)

- **Home** — hero, explains the concept, CTA into a new audit.
- **New audit** — tabbed input: upload a screenshot, or paste a URL. Client-side file type/size validation before submit.
- **Live audit view** — a Convex `useQuery` on the audit's status/progress, live by default (no separate Realtime channel wiring needed, unlike the prior builds' Supabase setup) — same end-user effect as the live-scan/live-analysis pages.
- **Report Card** — overall score hero, the annotated screenshot with a toggle for the saliency heatmap overlay, four lens tabs (Design Eye / Rule Book / Copy Editor / Psychologist) each showing their findings and suggestions, shareable URL.

## GitHub Actions workflow

`.github/workflows/audit.yml` + `ci_run_audit.py` entrypoint, mirroring the shape of `.github/workflows/scan.yml`/`ci_run_scan.py` from the prior builds: Vercel API route (or the Next.js server action) dispatches it via `workflow_dispatch`, the job runs the full pipeline above, and writes status updates + final results directly to Convex using the official `convex` Python package (`ConvexClient(deployment_url).mutation(...)`) with a Convex deploy key stored as a GitHub Actions secret.

## Fixture

One demo screenshot (or a tiny static HTML page rendered via URL input) built to contain, deliberately:
- A visually-loud CTA that the saliency model shows doesn't actually draw attention (competing bright element elsewhere).
- At least one text/background pair whose real WCAG contrast result surprises naive eyeballing, in either direction.
- A couple of genuinely low-readability copy blocks for the Copy Editor lens to meaningfully rewrite.

## Build order

1. ✅ Local repo scaffold, `PLAN.md` (GitHub push deferred — user will create the remote repo a bit later; steps 1-3 needed no GitHub repo at all).
2. ✅ Convex schema (`convex/schema.ts`) + a minimal `audits.ts` (create/get) pushed to the `chatty-emu-813` dev deployment via a deploy key; sanity-checked with a real insert+read through the same `convex` Python client the GitHub Actions job will use, not just the dashboard.
3. ✅ Deterministic core built and verified standalone against a real screenshot: PaddleOCR extraction → contrast checker → target-size checker → textstat readability. Hand-checked — numbers matched what a human would expect (bright heading passes contrast at 12.41, tiny dark-on-dark diagram labels fail at 2.2–3.3).
4. ✅ MSI-Net loaded and run on CPU against the same real screenshot: heatmap peak landed exactly on the main heading (37% of total attention mass vs. 1% on the small diagram labels), ~3.3s inference — comfortably fine for an Actions job.
5. ✅ OpenRouter vision call + Groq call wired and run for real. Both required swapping the originally-planned model (see Research grounding above for what broke and why).
6. ✅ `.github/workflows/audit.yml` + `ci_run_audit.py` + `pipeline.py` built and run for real via `workflow_dispatch` (twice — the first real run surfaced a genuine bug, see below). Confirmed Convex ends up with a correct, complete result row, verified by downloading and visually inspecting both output images.
7. ✅ Next.js scaffold + design pass done: `apps/web` on the ui-ux-pro-max "dark OLED developer tool" system (Fira Sans/Fira Code, dark-only palette, `--space-*` tokens), Convex wired in, Base UI-based shadcn (`render=`+`nativeButton={false}` for Button+Link, confirmed matches Exploit-Path-Tracer's pattern not the Radix one), Motion animations, per-lens accent colors.
8. ✅ Upload/URL input flow → live audit view → Report Card UI, fully verified against a real completed audit end to end: submitted a real URL through the actual site, watched it dispatch to a real GitHub Actions run, and the Report Card correctly rendered the real score, critique, and both overlay images once it finished.
9. Deploy (Vercel + GitHub Actions), real Playwright smoke test against the deployed site. **Not started**.
10. README with real screenshots, written note, demo recording. **Not started**.

**Real bug found on real infrastructure (step 6):** the first live `workflow_dispatch` run segfaulted (SIGSEGV, not a Python exception) partway through, because `pipeline.py` imported both TensorFlow (saliency) and paddlepaddle (OCR) into the same process — their native libraries collide on Linux. This didn't reproduce as a crash locally on Windows (same underlying conflict class, but manifested as a catchable oneDNN exception there instead, already fixed separately). Fixed by isolating the saliency prediction into its own subprocess (`run_saliency_subprocess.py`), so a crash there is now a catchable `subprocess.CalledProcessError` in the parent rather than a silent process-wide kill. Re-ran for real after the fix: completed successfully end to end.

**Post-launch hardening + the real "wow factor" pass**, all from real usage after the pipeline first went live:
- OCR was flagging logo icons as text issues in two different ways (low-confidence garbled reads of logos, and high-confidence reads of letter-shaped logo marks like "M"/"Z") — both root-caused against real screenshots and fixed with a confidence floor + a minimum-length filter, not guessed at.
- One non-compliant AI response (the auto-router landing on a free model that didn't return valid JSON) was crashing the *entire* audit and discarding all the other lenses' already-successful work — both AI-calling lenses now retry once and fall back gracefully instead of raising.
- The single biggest quality issue, found by actually running the tool against a real, well-known site and looking at the captured screenshot: `capture_screenshot` fired before the page's real content had rendered (9 OCR boxes on Linear's homepage instead of the real 36), making every downstream lens work off a near-blank page. Fixed the wait strategy.
- The saliency lens computed its headline number (attention-vs-CTA) but never surfaced it anywhere in the report. Added `compute_attention_insight()` (a real over/under-index ratio, not a raw percentage) and folded it into a new AI-synthesized executive summary (still one bounded Groq call) that ties the score, contrast/size failures, the design critique, and the attention number into one specific, quantified headline finding shown prominently on the Report Card — this is the actual "proof of real reasoning" moment the plan's fixture design was originally aiming for, now genuinely present on real, arbitrary sites, not just a crafted demo fixture.

**Vision model swap + full-page capture**, driven by direct user feedback that the Design Eye critique read as shallow ("as an AI, if I gave you the page directly you'd rate it better"):
- Tested two alternatives against the *real* structured critique prompt (not a toy prompt) before picking one: Groq's only vision-capable model (`qwen/qwen3.6-27b`) produces excellent, specific scene understanding but is a reasoning model — on the real JSON-only prompt it burned its whole response on visible step-by-step "thinking" and never converged to output JSON, a structural mismatch, not a one-off flake. Switched instead to **Gemini 3.6 Flash** (`gemini-2.5-flash` turned out to be deprecated, discovered via Google's own 404 error naming the replacement) via Google's OpenAI-compatible endpoint — a non-reasoning model that reliably returns clean JSON and produces specific, quoted, non-generic critiques.
- `capture_screenshot` switched from viewport-only to `full_page=True`, directly addressing "audit the whole page" — verified end to end on a real 1280×10511px capture of linear.app: PaddleOCR internally downscales tall images past its 4000px side limit but correctly maps detected boxes back to full-image coordinates (confirmed boxes span to y≈10322, not capped at ~4000); the saliency subprocess returns a heatmap matching the full original shape; and the Design Eye critique on the full page surfaced real findings from far below the old viewport crop (a code-editor line-number contrast issue, a testimonial card competing with the CTA) that were structurally invisible before. Added a `max-h-[75vh] overflow-y-auto` scroll container around the Report Card's screenshot panel so a 10k+px-tall capture doesn't blow out the sticky two-column layout.

**Deterministic "see it fixed" preview**, from a user idea (an AI-generated "fixed mockup" on click) that hit a real free-tier wall: tested all three of Gemini's image-generation models directly (`gemini-2.5-flash-image`, `gemini-3-pro-image`, `gemini-3.1-flash-image`) and every one returns a hard 429 with `limit: 0` on the free tier — image generation isn't available at all without enabling billing, confirmed by testing rather than assumed. Built a deterministic alternative instead (`lenses/fix_render.py`): recolors each failing-contrast text box's actual glyph pixels to the already-computed passing color, no AI call, no hallucination risk. Two real bugs found and fixed while verifying this against actual data (not assumed to work from the math alone):
- `suggest_fixed_text_color`'s target-color heuristic picked the blend direction by comparing text vs. background luminance *locally*, which breaks when both colors sit in the same narrow dark cluster — verified directly on a real 1.11:1 "Log in" label where darkening the already-near-black text further could only ever reach ~1.16:1 against a near-black background, mathematically incapable of clearing 4.5:1. Fixed by comparing each pure extreme's *actual achievable* contrast ratio against the background instead of the local direction, which correctly picks white when black is the saturating dead end.
- The glyph-vs-background pixel classification (needed to know *which* pixels to recolor) used a fixed 15th/85th-percentile intensity split, which silently degraded to noise on the same near-invisible cases. Replaced with Otsu adaptive thresholding, verified on both the extreme case and a moderate 3.82:1 case — and since this is the same function `sample_text_and_background_color` uses to *read* colors for every contrast measurement, the fix also corrected the underlying contrast-ratio numbers themselves (the "Log in" issue was being *measured* as 1.11:1 when the real figure is 3.47:1), not just the new render.
- Surfaced via a new, deliberately separate "See the N contrast issues fixed" button + dialog (Before/After toggle) on the Report Card — kept out of the existing screenshot Issues/Attention-heatmap toggle per explicit user direction to avoid cluttering that view.

## Verification plan

- Standalone: OCR + contrast + target-size against a real screenshot, hand-verify a few numbers directly.
- Standalone: saliency heatmap sanity-check — does the peak roughly match where a human would actually look on the fixture?
- Fixture-level (the load-bearing correctness check, same role as the false-positive/contradiction checks in the prior two builds): confirm the heatmap-vs-CTA overlap check and the WCAG contrast check both land on the *correct* side of "looks like X but isn't."
- Production: real Playwright script against the deployed site (submit → watch live progress → open report → verify overlays and scores render correctly), screenshotted and recorded. ✅ Done — see below.

**README + demo, all real assets, no mockups.** `scripts/capture_screenshots.py` and `scripts/record_demo.py` both drive the real deployed app (`ai-ux-auditor-inky.vercel.app`), not localhost. Two real bugs found while building the screenshot script (fixed rather than worked around): Convex-hosted screenshots load asynchronously, so a fixed timeout before capturing screenshotted the panel as blank — `naturalHeight > 0` alone still wasn't enough for the full-page (10,000+px) images, since headers arrive before the full bitmap decodes; fixed with `img.decode()`, targeted at the *specific* image element (a blanket "every image on the page is loaded" check passes vacuously against already-loaded images while a newly-mounted dialog image is still decoding). The demo recording script had a real logic bug too: `wait_for_url("**/audit/*")` matches `/audit/new` itself, so the first attempt "succeeded" instantly without ever navigating and burned its whole 5-minute wait budget watching the stale New Audit page — fixed with an explicit predicate excluding that path. The final recording (`docs/aura-demo.webm`) is a genuine ~5-minute run: real URL submitted through the real UI, a real GitHub Actions job dispatched and watched to completion, real report interactions after. `DEMO_SCRIPT.md`'s timecodes and quoted numbers come directly from the recording script's own timestamped log and a Convex query against that exact audit run, not from watching the footage back.

## Open items for the user before/while building

- ~~New Supabase project credentials~~ — resolved: using Convex instead (project details above).
- ~~OpenRouter API key, Groq API key~~ — resolved: both provided.
- Repo name / GitHub account details for the new repo — deferred, user will create it a bit later; not blocking steps 1-3.
- Exact fixture screenshot/page — I'll draft one and share it before wiring the pipeline to it, so the two "looks like X but isn't" cases land the way we want narratively.
- Both API keys were pasted directly in chat, so they're in this session's transcript in plaintext — worth regenerating both once the project is live, as routine hygiene (not blocking).
