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

const MOON_FIELDS = ["moon-phase", "moon-illumination", "moon-rise", "moon-set"];

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

describe("the Moon section's dashes", () => {
  it("writes the phase with a capital first letter", async () => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, phase: "last quarter" }));

    expect(field(card, "moon-phase")).toBe("Last quarter");
  });

  it("shows a dash for a phase that is not one of the eight", async () => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, phase: "blue" }));

    expect(field(card, "moon-phase")).toBe("—");
  });

  it("shows a dash for a missing phase", async () => {
    const card = await mountCard(withMoon({ illumination: 0.78 }));

    expect(field(card, "moon-phase")).toBe("—");
  });

  it("shows an illumination of zero", async () => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, illumination: 0 }));

    expect(field(card, "moon-illumination")).toBe("0%");
  });

  it("rounds the illumination to a whole percent", async () => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, illumination: 0.996 }));

    expect(field(card, "moon-illumination")).toBe("100%");
  });

  it.each([
    ["above 1", 1.5],
    ["below 0", -0.1],
    ["not a number", "0.78"],
    ["null", null],
  ])("shows a dash for an illumination %s", async (_, illumination) => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, illumination }));

    expect(field(card, "moon-illumination")).toBe("—");
  });

  it("shows a dash for a missing illumination", async () => {
    const card = await mountCard(withMoon({ phase: "full" }));

    expect(field(card, "moon-illumination")).toBe("—");
  });

  it("shows the moonrise in Tokyo", async () => {
    const card = await mountCard(
      withMoon({ ...WAXING_GIBBOUS, rise: "2026-10-31T12:14:00Z" }),
      "backyard",
      "Asia/Tokyo",
    );

    expect(field(card, "moon-rise")).toBe("21:14");
  });

  it.each([
    ["missing", undefined],
    ["not a time", "after dark"],
    ["not a string", 1730409240000],
  ])("shows a dash for a moonset that is %s", async (_, set) => {
    const card = await mountCard(withMoon({ ...WAXING_GIBBOUS, set }));

    expect(field(card, "moon-set")).toBe("—");
  });

  it("shows four dashes before the first verdict", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown") });

    expect(MOON_FIELDS.map((name) => field(card, name))).toEqual(["—", "—", "—", "—"]);
  });

  it("shows four dashes for a moon attribute that is not an object", async () => {
    const card = await mountCard(withMoon("full"));

    expect(MOON_FIELDS.map((name) => field(card, name))).toEqual(["—", "—", "—", "—"]);
  });
});
