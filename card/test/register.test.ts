import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

async function loadCard(): Promise<void> {
  vi.resetModules();
  await import("../src/pierpressure-card");
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

  it("logs the card's version", async () => {
    await loadCard();

    expect(console.info).toHaveBeenCalledWith("PIERPRESSURE-CARD dev");
  });

  it("keeps one picker entry when the file loads twice", async () => {
    await loadCard();
    await loadCard();

    expect(window.customCards?.filter((card) => card.type === "pierpressure-card")).toHaveLength(1);
  });
});
