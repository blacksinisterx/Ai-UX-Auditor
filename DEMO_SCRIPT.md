# Demo Script — Aura, AI UX Auditor

One narration track, aligned to `docs/aura-demo.webm` / `.mp4` (video-only — read this over it, or feed both into the AI Video Narrator project to render a narrated cut). Recorded for real against the live deployed app: a real URL submitted through the actual UI, a real GitHub Actions job dispatched and run to completion, no staged data, no cuts. Every timecode, number, and quote below is taken directly from `scripts/record_demo.py`'s own timestamped log and a direct Convex query against this exact audit run (`j977edvcnbemh9nww9j5byw1518cq1e9`) — not guessed from watching the footage after the fact.

**Pacing note:** each section's narration is word-budgeted against that section's *real* on-screen duration (from the recording script's own timestamps), not written first and timed after. The two moments with almost no real screen time (New Audit's URL submit, and the closing four-tab walkthrough) carry only a few words each on purpose; nearly all of the explanatory detail lives in the 4:27 the actual pipeline is genuinely running, because that's where nearly all of the video's real duration is.

---

**[0:00–0:08] Home**
"This is Aura — a UX audit agent with four lenses, most of them real deterministic code."

**[0:08–0:11] New audit**
"Submitting a real, live URL."

**[0:11–4:38] Live pipeline**
"That single click creates a record in Convex and dispatches a real GitHub Actions job — nothing here is staged or pre-computed for a demo. Here's what's actually happening on GitHub's own infrastructure right now, in order. First, a headless browser captures the entire page, not just what fits in one screen. Then a real OCR model reads every visible string and its exact pixel position. From those positions, the deterministic Rule Book lens samples the actual pixel colors around each piece of text and runs the real WCAG relative-luminance formula — the contrast ratio you'll see in a minute isn't an LLM's guess, it's the same math a browser's own accessibility inspector would compute. Those same OCR boxes also get checked against the forty-four by forty-four pixel minimum tap-target size WCAG requires for anything clickable. Next, a real saliency model — a neural network trained specifically to predict where a human's eyes would actually land — generates an attention heatmap, which gets compared against wherever the page's most likely call-to-action sits, producing a real overlap ratio: is this button getting more visual attention than its size would predict, less, or about what you'd expect? Only after all of that deterministic work is done does an AI model get involved at all — one call to Gemini, asked to make the kind of qualitative judgment code genuinely can't: does the hierarchy read correctly, is the whitespace generous or cramped, does the primary button actually look dominant, or does something else compete with it? And finally, one call to Groq synthesizes everything — the score, the contrast failures, the saliency number, the AI's layout critique, and every piece of genuinely hard-to-read copy on the page — into one specific, quantified headline finding, and rewrites each of those copy snippets into something clearer. Two AI calls total, both bounded, both doing real synthesis work, not being asked one more time each for a vague opinion."

**[4:38–4:43] Score and headline finding**
"53 out of 100 — a real, synthesized headline, not a template."

**[4:43–4:50] See it fixed**
"And here's the fix — real recolored pixels, not an AI-generated mockup."

**[4:50–5:00] The other three lenses**
"Rule Book, Psychologist, Copy Editor, Design Eye — the same real numbers, individually, provable, checkable."
