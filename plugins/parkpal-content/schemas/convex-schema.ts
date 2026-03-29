// schemas/convex-schema.ts
// 
// This is a reference file showing how the attraction JSON maps to a Convex table.
// Copy this into your ParkPal Convex project's schema.ts file.

import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

const triviaQuestion = v.object({
  difficulty: v.union(v.literal("easy"), v.literal("medium"), v.literal("hard")),
  question: v.string(),
  answers: v.array(v.string()),   // exactly 4: "A) ...", "B) ...", "C) ...", "D) ..."
  correct: v.union(v.literal("A"), v.literal("B"), v.literal("C"), v.literal("D")),
  funFact: v.string(),
});

export default defineSchema({
  attractions: defineTable({
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
    trivia: v.array(triviaQuestion),
  })
    .index("by_park", ["park"])
    .index("by_park_land", ["park", "land"])
    .index("by_name", ["name"])
    .searchIndex("search_name", { searchField: "name" }),
});
