import { describe, expect, it } from "vitest";
import { pierEntityId, pierSlug, verdictEntityId } from "../src/entity";

describe("verdictEntityId", () => {
  it.each([
    ["backyard", "sensor.pierpressure_backyard_verdict"],
    ["Back-Yard", "sensor.pierpressure_back_yard_verdict"],
    ["Côte Nord", "sensor.pierpressure_cote_nord_verdict"],
  ])("maps the pier %j to %s", (pier, entityId) => {
    expect(verdictEntityId(pier)).toBe(entityId);
  });
});

describe("pierEntityId", () => {
  it.each([
    ["Back-Yard", "cloud_cover", "sensor.pierpressure_back_yard_cloud_cover"],
    ["Côte Nord", "cloud_high", "sensor.pierpressure_cote_nord_cloud_high"],
  ])("maps the pier %j and key %s to %s", (pier, key, entityId) => {
    expect(pierEntityId(pier, key)).toBe(entityId);
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
