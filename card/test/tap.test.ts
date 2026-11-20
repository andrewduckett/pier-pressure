import { describe, expect, it } from "vitest";
import { placeTip } from "../src/tap";

describe("placing the box", () => {
  const card = { left: 50, top: 20, width: 400, height: 300 };
  const box = { width: 100, height: 20 };

  it("centres the box above an item in the middle of the card", () => {
    const item = { left: 230, top: 120, width: 40, height: 16 };

    expect(placeTip(item, card, box)).toEqual({ left: 150, top: 76 });
  });

  it("keeps the box 8 px inside the card's right edge", () => {
    const item = { left: 430, top: 120, width: 20, height: 16 };

    expect(placeTip(item, card, box)).toEqual({ left: 292, top: 76 });
  });

  it("centres the box on the part of an item the card's left edge cuts off", () => {
    const item = { left: -50, top: 120, width: 200, height: 16 };

    expect(placeTip(item, card, { width: 40, height: 20 })).toEqual({ left: 30, top: 76 });
  });

  it("puts the box 4 px below an item with no room above it", () => {
    const item = { left: 230, top: 30, width: 40, height: 16 };

    expect(placeTip(item, card, box)).toEqual({ left: 150, top: 30 });
  });
});
