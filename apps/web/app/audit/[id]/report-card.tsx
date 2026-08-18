"use client";

import { useEffect, useState } from "react";
import { useQuery } from "convex/react";
import { motion } from "motion/react";
import { animate } from "motion";
import { Loader2 } from "lucide-react";
import { api } from "@/convex/_generated/api";
import type { Id } from "@/convex/_generated/dataModel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { LENSES } from "@/lib/lenses";

const EASE = [0.22, 1, 0.36, 1] as const;

type AuditDoc = {
  _id: Id<"audits">;
  sourceType: "url" | "screenshot";
  sourceUrl?: string;
};

type ContrastIssue = {
  text: string;
  contrast_ratio: number;
  threshold: number;
  passes_wcag_aa: boolean;
};

type SizeIssue = {
  text: string;
  width: number;
  height: number;
  passes_min_target_size: boolean;
};

type CopySuggestion = { original: string; suggestion: string };

function scoreColor(score: number) {
  if (score >= 80) return "text-primary";
  if (score >= 50) return "text-chart-3";
  return "text-destructive";
}

function AnimatedScore({ score }: { score: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1,
      ease: EASE,
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return () => controls.stop();
  }, [score]);

  return (
    <span className={`text-6xl font-bold tabular-nums ${scoreColor(score)}`}>
      {display}
      <span className="text-2xl text-muted-foreground">/100</span>
    </span>
  );
}

export function ReportCard({ audit }: { audit: AuditDoc }) {
  const result = useQuery(api.auditResults.getByAuditId, { auditId: audit._id });
  const [imageMode, setImageMode] = useState<"issues" | "attention">("issues");

  if (result === undefined) {
    return (
      <div className="flex flex-1 items-center justify-center gap-(--space-sm) text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading report…
      </div>
    );
  }

  if (result === null) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        This audit finished but no result was saved.
      </div>
    );
  }

  const contrastIssues = (result.contrastIssues ?? []) as ContrastIssue[];
  const sizeIssues = (result.sizeIssues ?? []) as SizeIssue[];
  const copySuggestions = (result.copySuggestions ?? []) as CopySuggestion[];
  const contrastFailCount = contrastIssues.filter((i) => !i.passes_wcag_aa).length;
  const sizeFailCount = sizeIssues.filter((i) => !i.passes_min_target_size).length;

  return (
    <div className="relative">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-96"
        style={{
          background:
            "radial-gradient(50% 100% at 50% 0%, color-mix(in oklch, var(--primary) 10%, transparent), transparent)",
        }}
      />
      <div className="relative mx-auto flex w-full max-w-4xl flex-col gap-(--space-xl) px-(--space-lg) py-(--space-2xl)">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE }}
          className="flex flex-col items-center gap-(--space-sm) text-center"
        >
          <span className="text-sm font-medium text-muted-foreground">Overall UX Score</span>
          <AnimatedScore score={result.overallScore} />
          {audit.sourceType === "url" && audit.sourceUrl && (
            <span className="text-sm text-muted-foreground">{audit.sourceUrl}</span>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.08 }}
        >
          <Card className="overflow-hidden p-0">
            <div className="flex items-center justify-between gap-(--space-sm) border-b border-border px-(--space-md) py-(--space-sm)">
              <span className="text-sm font-medium">Screenshot</span>
              <div className="flex gap-(--space-xs)">
                <button
                  type="button"
                  onClick={() => setImageMode("issues")}
                  className={`cursor-pointer rounded-(--radius-md) px-(--space-sm) py-1 text-xs font-medium transition-colors ${
                    imageMode === "issues"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Issues
                </button>
                <button
                  type="button"
                  onClick={() => setImageMode("attention")}
                  className={`cursor-pointer rounded-(--radius-md) px-(--space-sm) py-1 text-xs font-medium transition-colors ${
                    imageMode === "attention"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Attention heatmap
                </button>
              </div>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element -- Convex-hosted, arbitrary-origin image */}
            <img
              src={imageMode === "issues" ? result.annotatedImageUrl! : result.saliencyHeatmapUrl!}
              alt={imageMode === "issues" ? "Annotated screenshot" : "Attention heatmap"}
              className="w-full"
            />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: EASE, delay: 0.14 }}
        >
          <Tabs defaultValue="design-eye">
            <TabsList className="grid w-full grid-cols-4">
              {LENSES.map((lens) => (
                <TabsTrigger
                  key={lens.key}
                  value={lens.key}
                  className="cursor-pointer gap-1.5"
                  style={{ "--lens-color": lens.color } as React.CSSProperties}
                >
                  <lens.icon
                    className="size-4 [[data-active]_&]:text-[var(--lens-color)]"
                    style={{ color: "var(--lens-color)" }}
                  />
                  <span className="hidden sm:inline">{lens.name}</span>
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value="design-eye" className="mt-(--space-md)">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Layout & structure</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {result.layoutCritique}
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="rule-book" className="mt-(--space-md) flex flex-col gap-(--space-md)">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base">Contrast</CardTitle>
                  <Badge variant={contrastFailCount > 0 ? "destructive" : "secondary"}>
                    {contrastFailCount} failing
                  </Badge>
                </CardHeader>
                <CardContent className="flex flex-col gap-(--space-sm)">
                  {contrastIssues.map((issue, i) => (
                    <div key={i}>
                      {i > 0 && <Separator className="mb-(--space-sm)" />}
                      <div className="flex items-center justify-between gap-(--space-sm) text-sm">
                        <span className="truncate text-muted-foreground">
                          &quot;{issue.text}&quot;
                        </span>
                        <Badge variant={issue.passes_wcag_aa ? "secondary" : "destructive"}>
                          {issue.contrast_ratio}:1 (need {issue.threshold}:1)
                        </Badge>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base">Target size</CardTitle>
                  <Badge variant={sizeFailCount > 0 ? "destructive" : "secondary"}>
                    {sizeFailCount} failing
                  </Badge>
                </CardHeader>
                <CardContent className="flex flex-col gap-(--space-sm)">
                  {sizeIssues.map((issue, i) => (
                    <div key={i}>
                      {i > 0 && <Separator className="mb-(--space-sm)" />}
                      <div className="flex items-center justify-between gap-(--space-sm) text-sm">
                        <span className="truncate text-muted-foreground">
                          &quot;{issue.text}&quot;
                        </span>
                        <Badge variant={issue.passes_min_target_size ? "secondary" : "destructive"}>
                          {issue.width}×{issue.height}px
                        </Badge>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="copy-editor" className="mt-(--space-md)">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Clarity suggestions</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-(--space-md)">
                  {copySuggestions.length === 0 && (
                    <p className="text-sm text-muted-foreground">No low-readability copy flagged.</p>
                  )}
                  {copySuggestions.map((s, i) => (
                    <div key={i} className="flex flex-col gap-(--space-xs)">
                      {i > 0 && <Separator className="mb-(--space-xs)" />}
                      <p className="text-sm text-muted-foreground line-through decoration-destructive/50">
                        {s.original}
                      </p>
                      <p className="text-sm text-foreground">{s.suggestion}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="psychologist" className="mt-(--space-md)">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Where attention actually goes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    A real saliency model predicted the heatmap above — toggle &quot;Attention
                    heatmap&quot; on the screenshot to see exactly where a viewer&apos;s eyes are
                    drawn first, and check it against where your call-to-action actually is.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
