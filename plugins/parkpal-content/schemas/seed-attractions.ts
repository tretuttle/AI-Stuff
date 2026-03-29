// schemas/seed-attractions.ts
//
// Reference Convex mutation for seeding attraction data from the JSON files.
// Copy into your ParkPal Convex project's convex/ directory.
//
// Usage from CLI:
//   npx convex run seedAttractions:seed --file data/json/magic_kingdom.json

import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const seed = mutation({
  args: {
    attractions: v.array(
      v.object({
        park: v.string(),
        land: v.string(),
        name: v.string(),
        leadImagineer: v.string(),
        opened: v.string(),
        precededBy: v.optional(v.string()),
        theme: v.string(),
        sponsor: v.string(),
        rideSystem: v.string(),
        duration: v.string(),
        facts: v.array(v.string()),
        trivia: v.array(
          v.object({
            difficulty: v.string(),
            question: v.string(),
            answers: v.array(v.string()),
            correct: v.string(),
            funFact: v.string(),
          })
        ),
      })
    ),
  },
  handler: async (ctx, args) => {
    let inserted = 0;
    let skipped = 0;

    for (const attraction of args.attractions) {
      // Check for existing entry by name + park
      const existing = await ctx.db
        .query("attractions")
        .filter((q) =>
          q.and(
            q.eq(q.field("name"), attraction.name),
            q.eq(q.field("park"), attraction.park)
          )
        )
        .first();

      if (existing) {
        // Update existing
        await ctx.db.patch(existing._id, attraction);
        skipped++;
      } else {
        await ctx.db.insert("attractions", attraction);
        inserted++;
      }
    }

    return { inserted, updated: skipped, total: args.attractions.length };
  },
});

// Delete all attractions for a park (useful for re-seeding)
export const clearPark = mutation({
  args: { park: v.string() },
  handler: async (ctx, args) => {
    const attractions = await ctx.db
      .query("attractions")
      .withIndex("by_park", (q) => q.eq("park", args.park))
      .collect();

    for (const attr of attractions) {
      await ctx.db.delete(attr._id);
    }

    return { deleted: attractions.length };
  },
});
