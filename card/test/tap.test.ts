import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  CLOUD_COVER_MIN,
  DEW_POINT,
  MOON_ALTITUDE,
  SEEING,
  TEMPERATURE,
  VERDICT,
  catalogTarget,
  forecastEntity,
  mountCard,
  target,
  verdictEntity,
} from "./harness";
import type { HassEntity, PierPressureCard } from "../src/pierpressure-card";
import { readMoon } from "../src/moon";
import { buildStrip, clock } from "../src/strip";
import { placeTip, tipText } from "../src/tap";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

// The axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z.
const MOON = { phase: "waxing gibbous", illumination: 0.78 };
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
  moon: MOON,
});

// A card with an item of every kind.
const EVERY_ITEM: Record<string, HassEntity> = {
  [VERDICT]: NIGHT,
  [CLOUD_COVER]: forecastEntity([["2026-11-01T04:00:00Z", 52]]),
  [SEEING]: forecastEntity([["2026-10-31T21:00:00Z", 0.62]]),
  [CLOUD_COVER_MIN]: forecastEntity([["2026-10-31T21:00:00Z", 40]]),
  [CLOUD_COVER_MAX]: forecastEntity([["2026-10-31T21:00:00Z", 70.5]]),
  [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4.2]]),
  [DEW_POINT]: forecastEntity([["2026-10-31T21:00:00Z", 1.0]]),
  [MOON_ALTITUDE]: forecastEntity([
    ["2026-10-31T16:00:00Z", 4],
    ["2026-10-31T17:00:00Z", 6],
  ]),
  [target(1)]: catalogTarget("M31", "Andromeda Galaxy", {
    start: "2026-10-31T21:00:00Z",
    end: "2026-11-01T02:00:00Z",
  }),
};

// A card with a message of every kind.
const EVERY_MESSAGE: Record<string, HassEntity> = {
  [VERDICT]: NIGHT,
  [SEEING]: { state: "unavailable", attributes: {} },
  [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4.2]]),
  [CLOUD_COVER_MIN]: forecastEntity([["2026-10-31T21:00:00Z", 40]]),
};

function tappable(card: PierPressureCard, key: string): Element | null {
  return card.shadowRoot?.querySelector(`[data-tip="${key}"]`) ?? null;
}

// The strip as the card draws it, on the clock mountCard pins.
function shown(states: Record<string, HassEntity>) {
  const strip = buildStrip(states, "backyard", Date.parse("2026-10-31T12:00:00Z"), "UTC");
  const moon = readMoon(states[VERDICT]?.attributes["moon"], clock("UTC"), undefined).drawing;
  return { strip, moon };
}

describe("the key on each tappable item", () => {
  it.each([
    [
      "a Cloud cover cell",
      "cell:cloud_cover:2026-11-01T04:00:00.000Z",
      '[data-row="cloud_cover"] .cell',
    ],
    ["a Cloud range column", "column:2026-10-31T21:00:00.000Z", '[data-row="cloud_range"] .column'],
    [
      "a Temperature chart hour",
      "hour:2026-10-31T21:00:00.000Z",
      '[data-chart="temperature"] .hour',
    ],
    ["a Moon up bar", "moon-up:2026-10-31T16:00:00.000Z", '[data-lane="moon_up"] .bar'],
    ["a target bar", "target:1", '[data-lane="target_1"] .bar'],
    ["the dusk line", "line:dusk", '.line[data-line="dusk"]'],
    ["the moon drawing", "moon", "section.moon svg"],
  ])("names %s", async (_, key, selector) => {
    const card = await mountCard(EVERY_ITEM);

    expect(tappable(card, key)).toBe(card.shadowRoot?.querySelector(selector));
  });

  it.each([
    ["the Seeing row's message", "missing:seeing", '[data-row="seeing"] .missing'],
    ["the Moon up lane's message", "missing:moon_up", '[data-lane="moon_up"] .missing'],
    [
      "the Dew point message in the chart's key",
      "missing:chart:dew_point",
      '[data-chart="temperature"] [data-series="dew_point"] .missing',
    ],
    ["the Cloud range row's message", "missing:cloud_range", '[data-row="cloud_range"] .missing'],
  ])("names %s", async (_, key, selector) => {
    const card = await mountCard(EVERY_MESSAGE);

    expect(tappable(card, key)).toBe(card.shadowRoot?.querySelector(selector));
  });
});

describe("the text a key names", () => {
  it.each([
    ["an item", EVERY_ITEM],
    ["a message", EVERY_MESSAGE],
  ])("is the hover text of each %s", async (_, states) => {
    const card = await mountCard(states);
    const { strip, moon } = shown(states);
    const elements = [...(card.shadowRoot?.querySelectorAll("[data-tip]") ?? [])];

    expect(elements).not.toHaveLength(0);
    expect(
      elements.map((element) => tipText(strip, moon, element.getAttribute("data-tip") ?? "")),
    ).toEqual(elements.map((element) => element.getAttribute("aria-label")));
  });

  it.each([
    ["an hour off the axis", "cell:cloud_cover:2026-11-02T04:00:00.000Z"],
    ["a run that starts in another hour", "moon-up:2026-10-31T17:00:00.000Z"],
    ["a target lane with no bar", "target:2"],
    ["a row with no message", "missing:cloud_cover"],
  ])("is none for %s", async (_, key) => {
    const { strip, moon } = shown(EVERY_ITEM);

    expect(tipText(strip, moon, key)).toBeUndefined();
  });

  it("is none when the strip is not drawn", () => {
    expect(tipText(undefined, undefined, "line:dusk")).toBeUndefined();
  });
});

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
