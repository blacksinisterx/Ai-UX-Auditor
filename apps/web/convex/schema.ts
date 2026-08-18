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
    layoutCritique: v.string(),
    copySuggestions: v.any(),
    contrastIssues: v.any(),
    sizeIssues: v.any(),
    readability: v.any(),
    saliencyHeatmapStorageId: v.id("_storage"),
    annotatedImageStorageId: v.id("_storage"),
  }).index("by_audit", ["auditId"]),
});
