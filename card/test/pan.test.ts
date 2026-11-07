import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  PRECIPITATION_PROBABILITY,
  SEEING,
  VERDICT,
  forecastEntity,
  mountCard,
  target,
  targetEntity,
  verdictEntity,
} from "./harness";
import type { HassEntity, PierPressureCard } from "../src/pierpressure-card";
import { HOUR, buildStrip, stripReach } from "../src/strip";

// The judged night's opening axis: 4 hours before a 20:30 dusk to 5 hours after a 03:25 dawn.
const OPENING = {
  start: Date.parse("2026-10-31T16:30:00Z"),
  end: Date.parse("2026-11-01T08:25:00Z"),
};

// Hourly points from `first`, `count` of them, each with the value 40.
function hourly(first: string, count: number, value: unknown = 40): Array<[string, unknown]> {
  const start = Date.parse(first);
  return Array.from({ length: count }, (_, index) => [
    new Date(start + index * HOUR).toISOString(),
    value,
  ]);
}

function iso(reach: { start: number; end: number }): [string, string] {
  return [new Date(reach.start).toISOString(), new Date(reach.end).toISOString()];
}

function reach(states: Record<string, HassEntity>): [string, string] {
  return iso(stripReach(states, "backyard", OPENING));
}

describe("the reach", () => {
  it("runs from the first timeline hour to the end of the last", () => {
    const states = { [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)) };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-03T12:00:00.000Z"]);
  });

  it("counts a Cloud range sensor's hours", () => {
    const states = { [CLOUD_COVER_MAX]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)) };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-03T12:00:00.000Z"]);
  });

  it("starts at the hour a Rain chance value fills, the hour before its time", () => {
    const states = {
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-10-31T12:00:00Z", 20]]),
    };

    expect(reach(states)[0]).toBe("2026-10-31T11:00:00.000Z");
  });

  it("leaves out a null Rain chance point", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24)),
      [PRECIPITATION_PROBABILITY]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24, null)),
    };

    expect(reach(states)[0]).toBe("2026-10-31T12:00:00.000Z");
  });

  it("ends at a Rain chance value's own time, not the hour after it", () => {
    const states = {
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-11-02T11:00:00Z", 20]]),
    };

    expect(reach(states)[1]).toBe("2026-11-02T11:00:00.000Z");
  });

  it("counts a null point's hour", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T12:00:00Z", 40],
        ["2026-11-02T11:00:00Z", null],
      ]),
    };

    expect(reach(states)[1]).toBe("2026-11-02T12:00:00.000Z");
  });

  it("leaves out an unavailable sensor's forecast", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24)),
      [SEEING]: { ...forecastEntity(hourly("2026-10-31T12:00:00Z", 72)), state: "unavailable" },
    };

    expect(reach(states)[1]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("skips a point without a readable time", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T12:00:00Z", 40],
        ["tomorrow", 40],
      ]),
    };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it("covers the opening axis when the forecast is shorter", () => {
    const states = { [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T18:00:00Z", 12)) };

    expect(reach(states)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it("is the opening axis with no forecast", () => {
    expect(reach({})).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });
});

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

// Three days of cloud cover around the judged night, so the axis can pan either way.
const THREE_DAYS = {
  [VERDICT]: NIGHT,
  [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)),
};

const NOW = Date.parse("2026-10-31T22:00:00Z");

function held(states: Record<string, HassEntity>, start?: string) {
  return buildStrip(
    states,
    "backyard",
    NOW,
    "UTC",
    start === undefined ? undefined : Date.parse(start),
  );
}

describe("a strip with a held start", () => {
  it("is on the opening axis without one", () => {
    expect(iso(held(THREE_DAYS).axis)).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("starts at the held start, as long as the opening axis", () => {
    expect(iso(held(THREE_DAYS, "2026-11-01T16:30:00Z").axis)).toEqual([
      "2026-11-01T16:30:00.000Z",
      "2026-11-02T08:25:00.000Z",
    ]);
  });

  it("stays inside the reach", () => {
    expect(iso(held(THREE_DAYS, "2026-11-05T00:00:00Z").axis)).toEqual([
      "2026-11-02T20:05:00.000Z",
      "2026-11-03T12:00:00.000Z",
    ]);
  });

  it("carries the opening axis", () => {
    expect(iso(held(THREE_DAYS, "2026-11-01T16:30:00Z").opening)).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("carries the reach", () => {
    expect(iso(held(THREE_DAYS).reach)).toEqual([
      "2026-10-31T12:00:00.000Z",
      "2026-11-03T12:00:00.000Z",
    ]);
  });

  it("drops a dusk line panned off the axis", () => {
    const kinds = held(THREE_DAYS, "2026-10-31T22:30:00Z").lines.map((line) => line.kind);

    expect(kinds).toEqual(["dawn"]);
  });

  it("has no dusk or dawn line on the next night", () => {
    const kinds = held(THREE_DAYS, "2026-11-01T16:30:00Z").lines.map((line) => line.kind);

    expect(kinds).toEqual([]);
  });

  it("keeps a target lane with no bar on the next night", () => {
    const states = {
      ...THREE_DAYS,
      [target(1)]: targetEntity("Andromeda Galaxy", {
        start: "2026-10-31T21:00:00Z",
        end: "2026-11-01T02:00:00Z",
      }),
    };

    const lanes = held(states, "2026-11-01T16:30:00Z").targets;

    expect(lanes.map((lane) => [lane.label, lane.bar])).toEqual([["Target 1", undefined]]);
  });
});

describe("the card's arrow keys", () => {
  beforeAll(async () => {
    vi.spyOn(console, "info").mockImplementation(() => {});
    await import("../src/pierpressure-card");
  });

  afterEach(() => {
    vi.useRealTimers();
    document.body.replaceChildren();
  });

  it("pan the axis an hour later with Right", async () => {
    const card = await mountCard(THREE_DAYS);

    await press(card, "ArrowRight");

    expect(axisOf(card)).toEqual(["2026-10-31T17:30:00.000Z", "2026-11-01T09:25:00.000Z"]);
  });

  it("pan the axis an hour earlier with Left", async () => {
    const card = await mountCard(THREE_DAYS);

    await press(card, "ArrowLeft");

    expect(axisOf(card)).toEqual(["2026-10-31T15:30:00.000Z", "2026-11-01T07:25:00.000Z"]);
  });

  it("keep the page from scrolling sideways", async () => {
    const card = await mountCard(THREE_DAYS);

    const event = await press(card, "ArrowRight");

    expect(event.defaultPrevented).toBe(true);
  });

  it("leave other keys to the page", async () => {
    const card = await mountCard(THREE_DAYS);

    const event = await press(card, "ArrowDown");

    expect([event.defaultPrevented, axisOf(card)[0]]).toEqual([false, "2026-10-31T16:30:00.000Z"]);
  });

  it("stop at the end of the reach", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 21)),
    });

    await press(card, "ArrowRight");
    await press(card, "ArrowRight");

    expect(axisOf(card)).toEqual(["2026-10-31T17:05:00.000Z", "2026-11-01T09:00:00.000Z"]);
  });

  it("reach a strip that takes focus from the Tab key", async () => {
    const card = await mountCard(THREE_DAYS);

    expect(stripOf(card)?.getAttribute("tabindex")).toBe("0");
  });

  it("are named in the strip's accessible name", async () => {
    const card = await mountCard(THREE_DAYS);

    expect([
      stripOf(card)?.getAttribute("role"),
      stripOf(card)?.getAttribute("aria-label"),
    ]).toEqual([
      "group",
      "Night strip. Use the Left and Right arrow keys to move through the forecast.",
    ]);
  });
});

describe("a panned strip", () => {
  afterEach(() => {
    vi.useRealTimers();
    document.body.replaceChildren();
  });

  // The card's minute redraw needs its interval faked as well as the clock.
  function pinClockAndTimers(iso: string): void {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    vi.setSystemTime(new Date(iso));
  }

  const NO_DARKNESS = verdictEntity("GO", { dark_window: { start: null, end: null } });

  it("keeps its axis when Home Assistant sends new state", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    await sendStates(card, { ...THREE_DAYS });

    expect(axisOf(card)).toEqual(["2026-11-01T16:30:00.000Z", "2026-11-02T08:25:00.000Z"]);
  });

  it("keeps its axis when a minute passes", async () => {
    pinClockAndTimers("2026-11-01T12:00:00Z");
    const card = await mountCard({
      [VERDICT]: NO_DARKNESS,
      [CLOUD_COVER]: forecastEntity(hourly("2026-11-01T00:00:00Z", 72)),
    });
    await pressTimes(card, "ArrowRight", 6);

    vi.advanceTimersByTime(60_000);
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-11-01T12:00:00.000Z", "2026-11-02T12:00:00.000Z"]);
  });

  it("moves into the reach when the forecast moves on past it", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowLeft", 5);

    await sendStates(card, {
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T14:00:00Z", 72)),
    });

    expect(axisOf(card)).toEqual(["2026-10-31T14:00:00.000Z", "2026-11-01T05:55:00.000Z"]);
  });

  it("takes the length of a new night", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    await sendStates(card, {
      ...THREE_DAYS,
      [VERDICT]: verdictEntity("GO", {
        dark_window: { start: "2026-11-01T21:00:00Z", end: "2026-11-02T05:00:00Z" },
      }),
    });

    expect(axisOf(card)).toEqual(["2026-11-01T16:30:00.000Z", "2026-11-02T09:30:00.000Z"]);
  });

  it("follows the clock again once panned back by hand", async () => {
    pinClockAndTimers("2026-11-01T12:00:00Z");
    const card = await mountCard({
      [VERDICT]: NO_DARKNESS,
      [CLOUD_COVER]: forecastEntity(hourly("2026-11-01T00:00:00Z", 72)),
    });
    await press(card, "ArrowRight");
    await press(card, "ArrowLeft");

    vi.advanceTimersByTime(60_000);
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-11-01T06:01:00.000Z", "2026-11-02T06:01:00.000Z"]);
  });

  it("follows the clock after a pan the reach stopped", async () => {
    pinClockAndTimers("2026-11-01T12:00:00Z");
    const card = await mountCard({
      [VERDICT]: NO_DARKNESS,
      [CLOUD_COVER]: forecastEntity(hourly("2026-11-01T06:00:00Z", 72)),
    });
    await press(card, "ArrowLeft");

    vi.advanceTimersByTime(60_000);
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-11-01T06:01:00.000Z", "2026-11-02T06:01:00.000Z"]);
  });

  it("opens a new pier on its own opening axis", async () => {
    const card = await mountCard(BOTH_PIERS);
    await pressTimes(card, "ArrowRight", 24);

    card.setConfig({ type: "custom:pierpressure-card", pier: "frontyard" });
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it("keeps its axis when the configuration changes but the pier does not", async () => {
    const card = await mountCard(BOTH_PIERS);
    await pressTimes(card, "ArrowRight", 24);

    card.setConfig({ type: "custom:pierpressure-card", pier: "backyard" });
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-11-01T16:30:00.000Z", "2026-11-02T08:25:00.000Z"]);
  });
});

const BOTH_PIERS = {
  ...THREE_DAYS,
  "sensor.pierpressure_frontyard_verdict": NIGHT,
  "sensor.pierpressure_frontyard_cloud_cover": forecastEntity(hourly("2026-10-31T12:00:00Z", 72)),
};

function stripOf(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(".strip") ?? null;
}

function axisOf(card: PierPressureCard): [string | undefined, string | undefined] {
  const element = stripOf(card);
  return [element?.dataset["axisStart"], element?.dataset["axisEnd"]];
}

async function press(card: PierPressureCard, key: string): Promise<KeyboardEvent> {
  const event = new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true });
  stripOf(card)?.dispatchEvent(event);
  await card.updateComplete;
  return event;
}

async function pressTimes(card: PierPressureCard, key: string, times: number): Promise<void> {
  for (let index = 0; index < times; index += 1) await press(card, key);
}

async function sendStates(card: PierPressureCard, states: Record<string, HassEntity>) {
  card.hass = { states, config: { time_zone: "UTC" } };
  await card.updateComplete;
}
