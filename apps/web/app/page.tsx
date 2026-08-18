import Link from "next/link";
import { ArrowRight, Eye, ShieldCheck, PenLine, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const LENSES = [
  {
    icon: Eye,
    name: "Design Eye",
    subtitle: "Layout & structure",
    description:
      "A vision model reviews hierarchy, whitespace, and call-to-action clarity, the way a senior designer would.",
  },
  {
    icon: ShieldCheck,
    name: "Rule Book",
    subtitle: "Accessibility & readability",
    description:
      "Real WCAG contrast math on sampled pixel colors, plus target-size checks. Deterministic, not a guess.",
  },
  {
    icon: PenLine,
    name: "Copy Editor",
    subtitle: "Text & content",
    description:
      "OCR pulls every visible string; flagged low-readability copy gets a clearer rewrite suggestion.",
  },
  {
    icon: Brain,
    name: "Psychologist",
    subtitle: "User attention",
    description:
      "A real saliency model predicts where eyes actually go, so you can check it against where you want them to go.",
  },
] as const;

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <section className="relative overflow-hidden border-b border-border">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, color-mix(in oklch, var(--primary) 18%, transparent), transparent)",
          }}
        />
        <div className="relative mx-auto flex max-w-4xl flex-col items-center gap-(--space-lg) px-(--space-lg) py-(--space-3xl) text-center">
          <div className="inline-flex items-center gap-(--space-xs) rounded-full border border-border bg-card px-(--space-md) py-1.5 text-xs font-medium text-muted-foreground">
            <span className="size-1.5 rounded-full bg-primary" />
            Free, real UX audits — no signup
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-6xl">
            An actionable UX audit,
            <br />
            not a vibe check.
          </h1>
          <p className="max-w-2xl text-lg text-muted-foreground text-balance">
            Upload a screenshot or paste a URL. Aura runs four independent lenses — layout,
            accessibility, copy, and attention — and hands back a scored report card with real
            citations, not generic advice.
          </p>
          <div className="flex flex-col gap-(--space-sm) sm:flex-row">
            <Button
              render={<Link href="/audit/new" />}
              nativeButton={false}
              size="lg"
              className="cursor-pointer"
            >
              Start a free audit
              <ArrowRight className="size-4" />
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-(--space-lg) py-(--space-3xl)">
        <div className="mb-(--space-2xl) flex flex-col gap-(--space-xs) text-center">
          <h2 className="text-2xl font-semibold sm:text-3xl">Four lenses, one report</h2>
          <p className="text-muted-foreground">
            Each one is a real, independently-checkable tool — not four calls to the same LLM.
          </p>
        </div>
        <div className="grid gap-(--space-lg) sm:grid-cols-2 lg:grid-cols-4">
          {LENSES.map((lens) => (
            <Card key={lens.name} className="border-border bg-card/60">
              <CardHeader>
                <div className="mb-(--space-sm) flex size-10 items-center justify-center rounded-(--radius-md) bg-primary/15 text-primary">
                  <lens.icon className="size-5" />
                </div>
                <CardTitle className="text-base">{lens.name}</CardTitle>
                <CardDescription className="text-xs font-medium uppercase tracking-wide text-muted-foreground/80">
                  {lens.subtitle}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{lens.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-card/30">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-(--space-md) px-(--space-lg) py-(--space-2xl) text-center">
          <h2 className="text-2xl font-semibold sm:text-3xl">See it for yourself</h2>
          <p className="max-w-xl text-muted-foreground">
            Every finding in the report traces back to something checkable — a contrast ratio, a
            pixel region, a specific sentence. Nothing in the score is a guess.
          </p>
          <Button
            render={<Link href="/audit/new" />}
            nativeButton={false}
            variant="outline"
            className="cursor-pointer"
          >
            Try it now
            <ArrowRight className="size-4" />
          </Button>
        </div>
      </section>
    </div>
  );
}
