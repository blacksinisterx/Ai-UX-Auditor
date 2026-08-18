import { query } from "./_generated/server";
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
