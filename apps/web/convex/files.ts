import { mutation } from "./_generated/server";

// Standard Convex direct-upload pattern: the client asks for a short-lived
// upload URL, PUTs the file straight to Convex storage, then calls
// audits:create with the resulting storageId. Mirrors the prior builds'
// Supabase Storage direct-upload shape, just Convex's native equivalent.
export const generateUploadUrl = mutation({
  args: {},
  handler: async (ctx) => {
    return await ctx.storage.generateUploadUrl();
  },
});
