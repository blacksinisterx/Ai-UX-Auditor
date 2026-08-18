# Demo Script — Aura, AI UX Auditor

One narration track, aligned to `docs/aura-demo.webm` (video-only — read this over it). Recorded for real against the live deployed app: a real URL submitted through the actual UI, a real GitHub Actions job dispatched and run to completion, no staged data, no cuts. Every timecode, number, and quote below is taken directly from `scripts/record_demo.py`'s own timestamped log and a direct Convex query against this exact audit run (`j977edvcnbemh9nww9j5byw1518cq1e9`) — not guessed from watching the footage after the fact.

---

**[0:00–0:08] Home**
"This is Aura, a UX-audit agent. You give it a URL or a screenshot, and instead of one LLM giving you a vibe check, it runs four independent lenses — three of them are real deterministic code, not AI guessing at numbers — and hands back a scored report with findings you can actually check."

**[0:08–0:11] New audit**
"I'm pasting a real URL — linear.app — and submitting it. That single click creates a record in Convex and dispatches a real GitHub Actions job. Nothing here is pre-computed or cached for the demo."

**[0:11–4:38] Live pipeline**
"This is running for real, live, on GitHub's infrastructure — real screenshot capture with Playwright, real OCR, real WCAG contrast math, a real saliency model, and two real AI calls. It takes a few minutes because none of it is simulated. While it runs: the deterministic 'Rule Book' lens samples actual pixel colors at every OCR-detected text box and runs the real WCAG relative-luminance formula — no LLM ever touches that number. A saliency model separately predicts where a real viewer's eyes would actually go, and that gets compared against wherever the page's primary call-to-action sits, as a real overlap ratio. Only after all of that does a single Gemini call add qualitative judgment — hierarchy, whitespace, whether the CTA actually reads as dominant — and one Groq call synthesizes everything into one headline finding."

**[4:38–4:40] Score and headline finding**
"And it's done — 53 out of 100 for linear.app. The headline finding isn't a template; it's synthesized from this run's actual numbers: 26 elements failing WCAG AA contrast, 64 tap targets under the 44-by-44-pixel minimum, and it names the single worst offender specifically — the code-diff preview under 'Review PRs and agent output,' where the line numbers and inline tags are dark-gray on black and effectively unreadable."

**[4:40–4:43] See it fixed**
"Here's the part that matters most: this button doesn't call an AI to imagine a fixed version — I actually tested that route and Gemini's image-generation models all return zero quota on the free tier, so instead this recolors the *actual failing pixels* to a color mathematically computed to just clear WCAG AA."

**[4:43–4:48] Before / After**
"Toggling between before and after on the real screenshot — same page, same layout, only the specific failing text recolored based on real sampled pixel math. Nothing generated, nothing imagined."

**[4:48–5:00] The other three lenses**
"Rule Book is the raw deterministic data behind the headline finding — every contrast ratio and tap-target size, individually. Copy Editor pulled ten genuinely low-readability text snippets straight from the page's real OCR text and rewrote each one — this one turned 'Render Ul before vehicle_state sync when minimum required state is present' into a plain sentence. Psychologist shows the real number behind the attention claim: this page's likely primary CTA, 'Contact sales,' takes up 0.02% of the screen and gets 0.03% of total visual attention — a 1.49x density ratio, meaning it's getting roughly the attention its size would predict, not more, not less. And Design Eye is the one AI-judgment call in the whole report — it independently named the exact same code-diff contrast problem the deterministic math flagged, plus specifics no deterministic check could catch: that the bright testimonial quote actually competes with the real 'Get started' button for attention."
