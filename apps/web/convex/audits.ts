import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    sourceType: v.union(v.literal("url"), v.literal("screenshot")),
    sourceUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("audits", {
      sourceType: args.sourceType,
      sourceUrl: args.sourceUrl,
      status: "pending",
    });
  },
});

export const get = query({
  args: { id: v.id("audits") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});
