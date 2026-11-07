import { beforeAll, describe, expect, it, vi } from "vitest";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

function newCard(): PierPressureCard {
  return document.createElement("pierpressure-card") as PierPressureCard;
}

describe("setConfig", () => {
  it.each([
    ["no pier", {}],
    ["an empty pier", { pier: "" }],
    ["a blank pier", { pier: "   " }],
    ["a pier of punctuation only", { pier: "---" }],
    ["a pier that is not text", { pier: 7 }],
  ])("refuses %s", (_label, fields) => {
    const card = newCard();

    expect(() => card.setConfig({ type: "custom:pierpressure-card", ...fields })).toThrow(
      "pier is required",
    );
  });

  it("accepts a pier id", () => {
    const card = newCard();

    expect(() => card.setConfig({ type: "custom:pierpressure-card", pier: "backyard" })).not.toThrow();
  });
});
