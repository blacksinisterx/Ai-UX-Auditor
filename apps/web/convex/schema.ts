import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

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
    executiveSummary: v.string(),
    layoutCritique: v.any(), // { hierarchy, whitespace, cta, flaw }
    copySuggestions: v.any(),
    contrastIssues: v.any(),
    sizeIssues: v.any(),
    readability: v.any(),
    attentionInsight: v.optional(v.any()), // { ctaText, overlapPercent, areaPercent, densityRatio, verdict }
    saliencyHeatmapStorageId: v.id("_storage"),
    annotatedImageStorageId: v.id("_storage"),
    fixedImageStorageId: v.optional(v.id("_storage")), // contrast-issue text pixels recolored to a passing color
  }).index("by_audit", ["auditId"]),
});
