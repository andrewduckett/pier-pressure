import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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
