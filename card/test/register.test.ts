import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PierPressureCard } from "../src/pierpressure-card";
import { verdictEntity } from "./harness";

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

  it("asks the card picker for a preview", async () => {
    await loadCard();

    expect(window.customCards?.[0]?.preview).toBe(true);
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

  // Fifteen strip rows of 16 px with 2 px gaps, under the verdict lines.
  it("is ten rows high in a masonry view", async () => {
    expect((await card()).getCardSize()).toBe(10);
  });

  // The strip's time labels need the room.
  it("takes the full width of a sections view", async () => {
    expect((await card()).getGridOptions()).toEqual({ columns: "full" });
  });
});

describe("the starting configuration", () => {
  async function cardClass(): Promise<typeof PierPressureCard> {
    vi.spyOn(console, "info").mockImplementation(() => {});
    return (await import("../src/pierpressure-card")).PierPressureCard;
  }

  it("picks the first listed pier", async () => {
    const states = {
      "sensor.pierpressure_frontyard_verdict": verdictEntity("GO", { pier: "frontyard" }),
      "sensor.pierpressure_backyard_verdict": verdictEntity("GO", { pier: "backyard" }),
    };

    expect((await cardClass()).getStubConfig({ states })).toEqual({
      type: "custom:pierpressure-card",
      pier: "backyard",
    });
  });

  it("has no pier when Home Assistant has no PierPressure verdict", async () => {
    expect((await cardClass()).getStubConfig({ states: {} })).toEqual({
      type: "custom:pierpressure-card",
    });
  });
});
