import { describe, expect, it } from "vitest";
import { pierSlug, verdictEntityId } from "../src/entity";

describe("verdictEntityId", () => {
  it.each([
    ["backyard", "sensor.pierpressure_backyard_verdict"],
    ["Back-Yard", "sensor.pierpressure_back_yard_verdict"],
    ["Côte Nord", "sensor.pierpressure_cote_nord_verdict"],
  ])("maps the pier %j to %s", (pier, entityId) => {
    expect(verdictEntityId(pier)).toBe(entityId);
  });
});

describe("pierSlug", () => {
  it("collapses each run of other characters into one underscore", () => {
    expect(pierSlug("north  --  pier")).toBe("north_pier");
  });

  it("drops underscores at either end", () => {
    expect(pierSlug("_roof deck!")).toBe("roof_deck");
  });

  it.each(["", "   ", "---"])("is empty for %j", (pier) => {
    expect(pierSlug(pier)).toBe("");
  });
});
