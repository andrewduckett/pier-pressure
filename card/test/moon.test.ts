import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, cardStyles, field, mountCard, verdictEntity } from "./harness";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

const WAXING_GIBBOUS = {
  illumination: 0.78,
  phase: "waxing gibbous",
  rise: "2026-10-31T21:14:00Z",
  set: null,
};

function withMoon(moon: unknown, state = "GO") {
  return { [VERDICT]: verdictEntity(state, { moon }) };
}

function moonSection(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>("section.moon") ?? null;
}

describe("the Moon section", () => {
  it("shows the phase", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    expect(field(card, "moon-phase")).toBe("Waxing gibbous");
  });

  it("shows the illumination as a percent", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    expect(field(card, "moon-illumination")).toBe("78%");
  });

  it("shows the moonrise in Home Assistant's time zone", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    expect(field(card, "moon-rise")).toBe("21:14");
  });

  it("shows a dash for a null moonset", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    expect(field(card, "moon-set")).toBe("—");
  });

  it("sits beside the verdict lines", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    const section = moonSection(card);
    expect([section?.parentElement?.className, section?.previousElementSibling?.tagName]).toEqual([
      "summary",
      "DL",
    ]);
  });

  it("is named Moon for a screen reader", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS));

    expect(moonSection(card)?.getAttribute("aria-label")).toBe("Moon");
  });

  it("is not shown before Home Assistant gives the card its state", async () => {
    const card = await mountCard();

    expect(moonSection(card)).toBeNull();
  });

  it("is not shown while PierPressure is offline", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS, "unavailable"));

    expect(moonSection(card)).toBeNull();
  });

  it("is not shown when the Verdict sensor is missing", async () => {
    const card = await mountCard(withMoon(WAXING_GIBBOUS), "frontyard");

    expect(moonSection(card)).toBeNull();
  });

  // The test DOM does not lay out, so the layout is checked in the stylesheet.
  it("wraps under the verdict lines on a narrow card", () => {
    expect(cardStyles().replace(/\s+/g, " ")).toMatch(
      /\.summary \{ display: flex; flex-wrap: wrap; gap: 16px;/,
    );
  });

  it("puts its texts beside the drawing", () => {
    expect(cardStyles().replace(/\s+/g, " ")).toMatch(
      /\.moon \{ display: flex; align-items: center; gap: 12px;/,
    );
  });
});
