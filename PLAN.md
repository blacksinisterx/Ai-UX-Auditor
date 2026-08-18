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
6. `.github/workflows/audit.yml` + `ci_run_audit.py` tying the whole pipeline together; run once manually via `workflow_dispatch`, confirm Convex ends up with a correct, complete result row. **Not started** — needs the GitHub repo (deferred by user).
7. Next.js scaffold done (`apps/web`, Convex wired in); full design-system pass and actual pages **not started**.
8. Upload/URL input flow → live audit view → Report Card UI. **Not started**.
9. Deploy (Vercel + GitHub Actions), real Playwright smoke test against the deployed site. **Not started**.
10. README with real screenshots, written note, demo recording. **Not started**.

## Verification plan

- Standalone: OCR + contrast + target-size against a real screenshot, hand-verify a few numbers directly.
- Standalone: saliency heatmap sanity-check — does the peak roughly match where a human would actually look on the fixture?
- Fixture-level (the load-bearing correctness check, same role as the false-positive/contradiction checks in the prior two builds): confirm the heatmap-vs-CTA overlap check and the WCAG contrast check both land on the *correct* side of "looks like X but isn't."
- Production: real Playwright script against the deployed site (submit → watch live progress → open report → verify overlays and scores render correctly), screenshotted and recorded.

## Open items for the user before/while building

- ~~New Supabase project credentials~~ — resolved: using Convex instead (project details above).
- ~~OpenRouter API key, Groq API key~~ — resolved: both provided.
- Repo name / GitHub account details for the new repo — deferred, user will create it a bit later; not blocking steps 1-3.
- Exact fixture screenshot/page — I'll draft one and share it before wiring the pipeline to it, so the two "looks like X but isn't" cases land the way we want narratively.
- Both API keys were pasted directly in chat, so they're in this session's transcript in plaintext — worth regenerating both once the project is live, as routine hygiene (not blocking).
