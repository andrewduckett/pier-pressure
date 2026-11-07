import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PierPressureCard } from "../src/pierpressure-card";

async function loadCard(): Promise<string> {
  vi.resetModules();
  const card = await import("../src/pierpressure-card");
  return card.CARD_VERSION;
}

describe("loading the card file", () => {
  beforeEach(() => {
    delete window.customCards;
    vi.spyOn(console, "info").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("defines the pierpressure-card element", async () => {
    await loadCard();

    expect(customElements.get("pierpressure-card")).toBeDefined();
  });

  it("lists the card in the card picker", async () => {
    await loadCard();

    expect(window.customCards).toEqual([
      expect.objectContaining({ type: "pierpressure-card", name: "PierPressure" }),
    ]);
  });

  it("describes the card in the card picker", async () => {
    await loadCard();

    expect(window.customCards?.[0]?.description).toBe(
      "Tonight's verdict and night strip for one pier.",
    );
  });

  // The stamp itself is the build test's job; a release runs these tests with
  // its own version set, so this one must not assume `dev`.
  it("logs the card's version", async () => {
    const version = await loadCard();

    expect(console.info).toHaveBeenCalledWith(`PIERPRESSURE-CARD ${version}`);
  });

  it("keeps one picker entry when the file loads twice", async () => {
    await loadCard();
    await loadCard();

    expect(window.customCards?.filter((card) => card.type === "pierpressure-card")).toHaveLength(1);
  });
});

describe("the card's size", () => {
  async function card(): Promise<PierPressureCard> {
    vi.spyOn(console, "info").mockImplementation(() => {});
    await import("../src/pierpressure-card");
    return document.createElement("pierpressure-card") as PierPressureCard;
  }

  it("is five rows high in a masonry view", async () => {
    expect((await card()).getCardSize()).toBe(5);
  });

  // The strip's time labels need the room, as the YAML strip's grid options give it.
  it("takes the full width of a sections view", async () => {
    expect((await card()).getGridOptions()).toEqual({ columns: "full" });
  });
});
