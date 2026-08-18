"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LENSES } from "@/lib/lenses";

const EASE = [0.22, 1, 0.36, 1] as const;

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <section className="relative overflow-hidden border-b border-border">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 0%, color-mix(in oklch, var(--primary) 20%, transparent), transparent), radial-gradient(40% 35% at 15% 15%, color-mix(in oklch, var(--chart-2) 14%, transparent), transparent), radial-gradient(40% 35% at 85% 10%, color-mix(in oklch, var(--chart-4) 12%, transparent), transparent)",
          }}
        />
        <div className="relative mx-auto flex max-w-4xl flex-col items-center gap-(--space-lg) px-(--space-lg) py-(--space-3xl) text-center">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: EASE }}
            className="inline-flex items-center gap-(--space-xs) rounded-full border border-border bg-card px-(--space-md) py-1.5 text-xs font-medium text-muted-foreground"
          >
            <span className="size-1.5 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
            Free, real UX audits — no signup
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE, delay: 0.05 }}
            className="text-4xl font-semibold tracking-tight text-balance sm:text-6xl"
          >
            An actionable UX audit,
            <br />
            not a vibe check.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE, delay: 0.1 }}
            className="max-w-2xl text-lg text-muted-foreground text-balance"
          >
            Upload a screenshot or paste a URL. Aura runs four independent lenses — layout,
            accessibility, copy, and attention — and hands back a scored report card with real
            citations, not generic advice.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: EASE, delay: 0.15 }}
            className="flex flex-col gap-(--space-sm) sm:flex-row"
          >
            <Button
              render={<Link href="/audit/new" />}
              nativeButton={false}
              size="lg"
              className="cursor-pointer"
            >
              Start a free audit
              <ArrowRight className="size-4" />
            </Button>
          </motion.div>
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
          {LENSES.map((lens, i) => (
            <motion.div
              key={lens.name}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.4 }}
              transition={{ duration: 0.5, ease: EASE, delay: i * 0.08 }}
              whileHover={{ y: -6 }}
            >
              <Card
                className="h-full border-border bg-card/60 transition-shadow hover:shadow-[0_12px_32px_-12px_var(--lens-color)]"
                style={{ "--lens-color": lens.color } as React.CSSProperties}
              >
                <CardHeader>
                  <div
                    className="mb-(--space-sm) flex size-10 items-center justify-center rounded-(--radius-md)"
                    style={{
                      backgroundColor: "color-mix(in oklch, var(--lens-color) 18%, transparent)",
                      color: lens.color,
                    }}
                  >
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
            </motion.div>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-card/30">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.6, ease: EASE }}
          className="mx-auto flex max-w-4xl flex-col items-center gap-(--space-md) px-(--space-lg) py-(--space-2xl) text-center"
        >
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
        </motion.div>
      </section>
    </div>
  );
}
