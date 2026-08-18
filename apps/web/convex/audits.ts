import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    sourceType: v.union(v.literal("url"), v.literal("screenshot")),
    sourceUrl: v.optional(v.string()),
    screenshotStorageId: v.optional(v.id("_storage")),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("audits", {
      sourceType: args.sourceType,
      sourceUrl: args.sourceUrl,
      screenshotStorageId: args.screenshotStorageId,
      status: "pending",
    });
  },
});

export const get = query({
  args: { id: v.id("audits") },
  handler: async (ctx, args) => {
    const audit = await ctx.db.get(args.id);
    if (!audit) return null;
    const screenshotUrl = audit.screenshotStorageId
      ? await ctx.storage.getUrl(audit.screenshotStorageId)
      : null;
    return { ...audit, screenshotUrl };
  },
});

// Called by the GitHub Actions pipeline job (apps/agent/ci_run_audit.py) to
// report progress as it works through the lenses. Kept as a regular public
// mutation rather than an internal one requiring admin-key auth from Python
// -- accepted tradeoff for a free, no-signup public demo tool with no
// sensitive data, not a multi-tenant product.
export const setProgress = mutation({
  args: {
    id: v.id("audits"),
    status: v.string(),
    stage: v.optional(v.string()),
    percent: v.optional(v.number()),
    log: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: args.status,
      progress: { stage: args.stage, percent: args.percent, log: args.log },
    });
  },
});

export const markDone = mutation({
  args: { id: v.id("audits") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { status: "done", completedAt: Date.now() });
  },
});

export const markError = mutation({
  args: { id: v.id("audits"), message: v.string() },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, {
      status: "error",
      progress: { stage: args.message, percent: 100 },
    });
  },
});
