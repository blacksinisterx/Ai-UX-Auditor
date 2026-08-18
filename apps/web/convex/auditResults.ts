import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const getByAuditId = query({
  args: { auditId: v.id("audits") },
  handler: async (ctx, args) => {
    const result = await ctx.db
      .query("auditResults")
      .withIndex("by_audit", (q) => q.eq("auditId", args.auditId))
      .unique();
    if (!result) return null;
    const [saliencyHeatmapUrl, annotatedImageUrl] = await Promise.all([
      ctx.storage.getUrl(result.saliencyHeatmapStorageId),
      ctx.storage.getUrl(result.annotatedImageStorageId),
    ]);
    return { ...result, saliencyHeatmapUrl, annotatedImageUrl };
  },
});

// Called once by the pipeline job at the end of a successful run.
export const submit = mutation({
  args: {
    auditId: v.id("audits"),
    overallScore: v.number(),
    executiveSummary: v.string(),
    layoutCritique: v.any(),
    copySuggestions: v.any(),
    contrastIssues: v.any(),
    sizeIssues: v.any(),
    readability: v.any(),
    attentionInsight: v.optional(v.any()),
    saliencyHeatmapStorageId: v.id("_storage"),
    annotatedImageStorageId: v.id("_storage"),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("auditResults", args);
  },
});
