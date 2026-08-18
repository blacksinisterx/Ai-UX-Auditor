"use client";

import { use } from "react";
import { useQuery } from "convex/react";
import { api } from "@/convex/_generated/api";
import type { Id } from "@/convex/_generated/dataModel";
import { LiveAuditView } from "./live-audit-view";
import { ReportCard } from "./report-card";

export default function AuditPage({ params }: PageProps<"/audit/[id]">) {
  const { id } = use(params);
  const auditId = id as Id<"audits">;
  const audit = useQuery(api.audits.get, { id: auditId });

  if (audit === undefined) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        Loading audit…
      </div>
    );
  }

  if (audit === null) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-(--space-sm) text-center">
        <p className="text-lg font-medium">Audit not found</p>
        <p className="text-muted-foreground">This audit doesn&apos;t exist or was deleted.</p>
      </div>
    );
  }

  if (audit.status === "done") {
    return <ReportCard audit={audit} />;
  }

  return <LiveAuditView audit={audit} />;
}
