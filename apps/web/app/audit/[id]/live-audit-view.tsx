"use client";

import { Loader2, Clock, AlertTriangle, Check, Eye, ShieldCheck, PenLine, Brain } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

type Progress = { stage?: string; percent?: number; log?: string[] } | null | undefined;

type AuditDoc = {
  status: string;
  sourceType: "url" | "screenshot";
  sourceUrl?: string;
  screenshotUrl?: string | null;
  progress?: Progress;
};

const STAGE_LABELS: Record<string, string> = {
  pending: "Queued",
  running: "Running the audit pipeline…",
  error: "Audit failed",
};

const LENSES = [
  { key: "design-eye", name: "Design Eye", icon: Eye },
  { key: "rule-book", name: "Rule Book", icon: ShieldCheck },
  { key: "copy-editor", name: "Copy Editor", icon: PenLine },
  { key: "psychologist", name: "Psychologist", icon: Brain },
] as const;

export function LiveAuditView({ audit }: { audit: AuditDoc }) {
  const isError = audit.status === "error";
  const isRunning = audit.status === "running";
  const percent = audit.progress?.percent ?? (isError ? 100 : 0);
  const stageLabel = audit.progress?.stage ?? STAGE_LABELS[audit.status] ?? audit.status;

  return (
    <div className="relative flex min-h-[calc(100vh-53px)] items-center">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-96"
        style={{
          background:
            "radial-gradient(60% 100% at 50% 0%, color-mix(in oklch, var(--primary) 12%, transparent), transparent)",
        }}
      />
      <div className="relative mx-auto flex w-full max-w-2xl flex-col gap-(--space-xl) px-(--space-lg) py-(--space-2xl)">
        <div className="flex flex-col items-center gap-(--space-sm) text-center">
          {isError ? (
            <AlertTriangle className="size-8 text-destructive" />
          ) : (
            <Loader2 className="size-8 animate-spin text-primary" />
          )}
          <h1 className="text-2xl font-semibold">
            {isError ? "Something went wrong" : "Auditing your UI"}
          </h1>
          <p className="max-w-md break-all text-muted-foreground">
            {audit.sourceType === "url"
              ? audit.sourceUrl
              : "Reviewing your uploaded screenshot across all four lenses."}
          </p>
        </div>

        {audit.screenshotUrl && (
          // eslint-disable-next-line @next/next/no-img-element -- user-uploaded, arbitrary-origin image
          <img
            src={audit.screenshotUrl}
            alt="Uploaded screenshot"
            className="w-full rounded-(--radius-lg) border border-border"
          />
        )}

        <Card>
          <CardContent className="flex flex-col gap-(--space-md)">
            <div className="flex items-center justify-between gap-(--space-sm)">
              <span className="flex items-center gap-(--space-xs) text-sm font-medium">
                <Clock className="size-4 text-muted-foreground" />
                {stageLabel}
              </span>
              <Badge variant={isError ? "destructive" : "secondary"}>{audit.status}</Badge>
            </div>
            <Progress value={percent} />
            {audit.progress?.log && audit.progress.log.length > 0 && (
              <div className="flex max-h-40 flex-col gap-1 overflow-y-auto rounded-(--radius-md) border border-border bg-muted/30 p-(--space-sm) font-mono text-xs text-muted-foreground">
                {audit.progress.log.map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-(--space-sm)">
            {LENSES.map((lens) => {
              const done = isRunning && (audit.progress?.percent ?? 0) >= 100;
              return (
                <div key={lens.key} className="flex items-center gap-(--space-sm) text-sm">
                  <span
                    className={`flex size-7 shrink-0 items-center justify-center rounded-full border ${
                      done
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-border bg-muted/40 text-muted-foreground"
                    }`}
                  >
                    {done ? <Check className="size-3.5" /> : <lens.icon className="size-3.5" />}
                  </span>
                  <span className={done ? "text-foreground" : "text-muted-foreground"}>
                    {lens.name}
                  </span>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {!isError && !audit.progress && (
          <p className="text-center text-xs text-muted-foreground">
            Waiting for the audit pipeline to pick this up.
          </p>
        )}
      </div>
    </div>
  );
}
