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
