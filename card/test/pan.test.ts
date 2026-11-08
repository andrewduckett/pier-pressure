import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  PRECIPITATION_PROBABILITY,
  SEEING,
  VERDICT,
  cardStyles,
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

// Before dusk, so the opening axis is the judged night's.
const NOW = Date.parse("2026-10-31T12:00:00Z");

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

  // At 23:00 the opening axis runs from 19:00, and the pan moves it to 18:00.
  it("keeps an earlier pan's axis when a minute passes during the night", async () => {
    pinClockAndTimers("2026-10-31T23:00:00Z");
    const card = await mountCard(THREE_DAYS);
    await press(card, "ArrowLeft");

    vi.advanceTimersByTime(60_000);
    await card.updateComplete;

    expect([...axisOf(card), backButton(card)?.hidden]).toEqual([
      "2026-10-31T18:00:00.000Z",
      "2026-11-01T09:55:00.000Z",
      false,
    ]);
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

describe("the Back to tonight button", () => {
  afterEach(() => {
    document.body.replaceChildren();
  });

  it("is hidden on the opening axis", async () => {
    const card = await mountCard(THREE_DAYS);

    expect(backButton(card)?.hidden).toBe(true);
  });

  it("shows once the strip is panned", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    expect([backButton(card)?.hidden, backButton(card)?.textContent?.trim()]).toEqual([
      false,
      "Back to tonight",
    ]);
  });

  it("returns the strip to the opening axis", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    backButton(card)?.click();
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  // Panned at 23:00, when the opening axis ran from 19:00; selected an hour later.
  it("returns the strip to the opening axis of the time it is selected", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-31T23:00:00Z"));
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    vi.setSystemTime(new Date("2026-11-01T00:00:00Z"));
    backButton(card)?.click();
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-10-31T20:00:00.000Z", "2026-11-01T11:55:00.000Z"]);
  });

  it("hides once it has returned the strip", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    backButton(card)?.click();
    await card.updateComplete;

    expect(backButton(card)?.hidden).toBe(true);
  });

  it("gives the strip keyboard focus", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);

    backButton(card)?.click();
    await card.updateComplete;

    expect(card.shadowRoot?.activeElement).toBe(stripOf(card));
  });

  it("sits outside the strip", async () => {
    const card = await mountCard(THREE_DAYS);

    expect(backButton(card)?.closest(".strip")).toBeNull();
  });

  it("keeps its place while hidden", () => {
    expect(cardStyles()).toMatch(/\.back button\[hidden\]\s*\{[^}]*visibility:\s*hidden/);
  });

  it("is at least 24 px tall", () => {
    expect(cardStyles()).toMatch(/\.back button\s*\{[^}]*min-height:\s*24px/);
  });

  it("does not pan the strip when pressed with a slip", async () => {
    const card = await mountCard(THREE_DAYS);
    await pressTimes(card, "ArrowRight", 24);
    const button = backButton(card);

    button?.dispatchEvent(pointer("pointerdown", 100));
    button?.dispatchEvent(pointer("pointermove", 88));
    button?.dispatchEvent(pointer("pointerup", 88));
    button?.click();
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });
});

// A 24-hour opening axis from 06:00 to 06:00, with forecast hours either side of it.
const DAY_AROUND_NOW = {
  [VERDICT]: verdictEntity("GO", { dark_window: { start: null, end: null } }),
  [CLOUD_COVER]: forecastEntity(hourly("2026-11-01T00:00:00Z", 60)),
};

// The clock at noon, and the hours drawn across 400 px; happy-dom lays nothing out.
function layOutDayAroundNow(): void {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-01T12:00:00Z"));
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(
    new DOMRect(0, 0, 400, 16),
  );
}

function cleanUp(): void {
  vi.useRealTimers();
  vi.restoreAllMocks();
  document.body.replaceChildren();
}

describe("dragging the strip", () => {
  beforeEach(layOutDayAroundNow);
  afterEach(cleanUp);

  function drag(card: PierPressureCard, moves: Array<[number, number]>, end = "pointerup") {
    const strip = stripOf(card);
    strip?.dispatchEvent(pointer("pointerdown", 200, 100));
    for (const [x, y] of moves) strip?.dispatchEvent(pointer("pointermove", x, y));
    const last = moves.at(-1) ?? [200, 100];
    strip?.dispatchEvent(pointer(end, last[0], last[1]));
    return card.updateComplete;
  }

  it("pans later when dragged to the left", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[100, 100]]);

    expect(axisOf(card)).toEqual(["2026-11-01T12:00:00.000Z", "2026-11-02T12:00:00.000Z"]);
  });

  it("pans earlier when swiped to the right", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    const strip = stripOf(card);

    strip?.dispatchEvent(pointer("pointerdown", 200, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointermove", 300, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointerup", 300, 100, 1, "touch"));
    await card.updateComplete;

    expect(axisOf(card)).toEqual(["2026-11-01T00:00:00.000Z", "2026-11-02T00:00:00.000Z"]);
  });

  it("follows the pointer from where it was pressed", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [
      [150, 100],
      [100, 100],
    ]);

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("does not pan for a tap that slips", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[195, 100]]);

    expect([axisOf(card)[0], backButton(card)?.hidden]).toEqual(["2026-11-01T06:00:00.000Z", true]);
  });

  it("does not pan for a mostly vertical drag", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[190, 130]]);

    expect(axisOf(card)[0]).toBe("2026-11-01T06:00:00.000Z");
  });

  it("puts the axis back when the browser cancels the gesture", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[188, 96]], "pointercancel");

    expect([axisOf(card)[0], backButton(card)?.hidden]).toEqual(["2026-11-01T06:00:00.000Z", true]);
  });

  it("puts a panned axis back where the cancelled gesture began", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await drag(card, [[100, 100]]);

    await drag(card, [[0, 100]], "pointercancel");

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("ignores a second finger", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    const strip = stripOf(card);

    strip?.dispatchEvent(pointer("pointerdown", 200, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointermove", 100, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointerdown", 300, 100, 2, "touch"));
    strip?.dispatchEvent(pointer("pointermove", 50, 100, 2, "touch"));
    await card.updateComplete;

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("ignores a mouse button other than the main one", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    const strip = stripOf(card);

    strip?.dispatchEvent(pointer("pointerdown", 200, 100, 1, "mouse", 2));
    strip?.dispatchEvent(pointer("pointermove", 100, 100));
    await card.updateComplete;

    expect(axisOf(card)[0]).toBe("2026-11-01T06:00:00.000Z");
  });

  it("stops panning once the pointer is released", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await drag(card, [[100, 100]]);

    stripOf(card)?.dispatchEvent(pointer("pointermove", 0, 100));
    await card.updateComplete;

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("stops panning once the pointer capture is lost", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[100, 100]], "lostpointercapture");
    stripOf(card)?.dispatchEvent(pointer("pointermove", 0, 100));
    await card.updateComplete;

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("keeps panning when a cell loses the pointer to the strip", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    const strip = stripOf(card);
    const cell = strip?.querySelector('[data-row="cloud_cover"] .cell');

    // A touch pointer starts captured by the element under the finger; capturing
    // it on the strip makes that element lose it.
    cell?.dispatchEvent(pointer("pointerdown", 200, 100, 1, "touch"));
    cell?.dispatchEvent(pointer("pointermove", 180, 100, 1, "touch"));
    cell?.dispatchEvent(pointer("lostpointercapture", 180, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointermove", 100, 100, 1, "touch"));
    strip?.dispatchEvent(pointer("pointerup", 100, 100, 1, "touch"));
    await card.updateComplete;

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  // A mouse or pen pointer has no capture of its own, so a drag that leaves the
  // strip before it starts to pan would otherwise lose its moves.
  it("captures the pointer as soon as it is pressed", async () => {
    const capture = vi.spyOn(HTMLElement.prototype, "setPointerCapture");
    const card = await mountCard(DAY_AROUND_NOW);

    stripOf(card)?.dispatchEvent(pointer("pointerdown", 200, 100));

    expect(capture).toHaveBeenCalledWith(1);
  });

  it("pans nothing before the strip is laid out", async () => {
    vi.mocked(HTMLElement.prototype.getBoundingClientRect).mockReturnValue(new DOMRect());
    const card = await mountCard(DAY_AROUND_NOW);

    await drag(card, [[100, 100]]);

    expect(axisOf(card)[0]).toBe("2026-11-01T06:00:00.000Z");
  });

  it("leaves vertical swipes to the browser", () => {
    expect(cardStyles()).toMatch(/\.strip\s*\{[^}]*touch-action:\s*pan-y/);
  });

  it("does not select the strip's text", () => {
    expect(cardStyles()).toMatch(/\.strip\s*\{[^}]*user-select:\s*none/);
  });
});

describe("a wheel over the strip", () => {
  beforeEach(layOutDayAroundNow);
  afterEach(cleanUp);

  async function turn(card: PierPressureCard, init: WheelEventInit): Promise<WheelEvent> {
    const event = new WheelEvent("wheel", { bubbles: true, cancelable: true, ...init });
    stripOf(card)?.dispatchEvent(event);
    await card.updateComplete;
    return event;
  }

  it("pans later when it moves right", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await turn(card, { deltaX: 100 });

    expect(axisOf(card)).toEqual(["2026-11-01T12:00:00.000Z", "2026-11-02T12:00:00.000Z"]);
  });

  it("keeps a sideways movement from the browser", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    const event = await turn(card, { deltaX: 100 });

    expect(event.defaultPrevented).toBe(true);
  });

  it("keeps a sideways movement from the browser at the end of the reach", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    const event = await turn(card, { deltaX: -400 });

    expect([axisOf(card)[0], event.defaultPrevented]).toEqual(["2026-11-01T00:00:00.000Z", true]);
  });

  it("leaves a mostly vertical movement to the page", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    const event = await turn(card, { deltaX: 20, deltaY: 100 });

    expect([axisOf(card)[0], event.defaultPrevented]).toEqual(["2026-11-01T06:00:00.000Z", false]);
  });

  it("counts a line as 16 px", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await turn(card, { deltaX: 6.25, deltaMode: 1 });

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("counts a page as the width the hours are drawn across", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await turn(card, { deltaX: 0.25, deltaMode: 2 });

    expect(axisOf(card)[0]).toBe("2026-11-01T12:00:00.000Z");
  });
});

function backButton(card: PierPressureCard): HTMLButtonElement | null {
  return card.shadowRoot?.querySelector<HTMLButtonElement>(".back button") ?? null;
}

// A pointer's event as a browser sends it: pointer 1 is the primary one, and a
// move carries no button.
function pointer(
  type: string,
  clientX: number,
  clientY = 0,
  pointerId = 1,
  pointerType = "mouse",
  button = 0,
): PointerEvent {
  return new PointerEvent(type, {
    bubbles: true,
    composed: true,
    cancelable: true,
    clientX,
    clientY,
    pointerId,
    isPrimary: pointerId === 1,
    button: type === "pointermove" ? -1 : button,
    pointerType,
  });
}

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
