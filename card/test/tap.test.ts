import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  CLOUD_COVER_MIN,
  DEW_POINT,
  MOON_ALTITUDE,
  SEEING,
  TEMPERATURE,
  VERDICT,
  cardStyles,
  catalogTarget,
  forecastEntity,
  mountCard,
  pointer,
  tap,
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
  reasons: ["Cloud cover 52% at its worst"],
});

// A card with an item of every kind.
const EVERY_ITEM: Record<string, HassEntity> = {
  [VERDICT]: NIGHT,
  [CLOUD_COVER]: forecastEntity([["2026-11-01T04:00:00Z", 52]]),
  [SEEING]: forecastEntity([["2026-10-31T21:00:00Z", 0.62]]),
  [CLOUD_COVER_MIN]: forecastEntity([["2026-10-31T21:00:00Z", 40]]),
  [CLOUD_COVER_MAX]: forecastEntity([["2026-10-31T21:00:00Z", 70.5]]),
  [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4.2]]),
  [DEW_POINT]: forecastEntity([["2026-10-31T21:00:00Z", 1.5]]),
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

function tip(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(".tip") ?? null;
}

function tips(card: PierPressureCard): string[] {
  return [...(card.shadowRoot?.querySelectorAll(".tip") ?? [])].map(
    (box) => box.textContent?.trim() ?? "",
  );
}

async function tapOn(card: PierPressureCard, key: string, pointerType?: string): Promise<void> {
  tap(tappable(card, key), pointerType);
  await card.updateComplete;
}

const COVER_04 = "cell:cloud_cover:2026-11-01T04:00:00.000Z";

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

describe("a tap on a strip item", () => {
  it.each([
    ["a Cloud cover cell", COVER_04, "Cloud cover, the hour from 04:00: 52%"],
    [
      "a Cloud range column",
      "column:2026-10-31T21:00:00.000Z",
      "Cloud range, the hour from 21:00: 40% to 70.5%",
    ],
    [
      "a Temperature chart hour",
      "hour:2026-10-31T21:00:00.000Z",
      "The hour from 21:00: Temperature 4.2 °C, Dew point 1.5 °C",
    ],
    ["a target bar", "target:1", "Andromeda Galaxy (M31) from 21:00 to 02:00"],
    ["the dusk line", "line:dusk", "Dusk, 20:30"],
  ])("on %s shows the item's hover text in one box", async (_, key, text) => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, key, "touch");

    expect(tips(card)).toEqual([text]);
  });

  it("on a Cloud range column where the forecasts disagree says so", async () => {
    const card = await mountCard({
      ...EVERY_ITEM,
      [CLOUD_COVER_MIN]: forecastEntity([["2026-10-31T21:00:00Z", 20]]),
      [CLOUD_COVER_MAX]: forecastEntity([["2026-10-31T21:00:00Z", 70]]),
    });

    await tapOn(card, "column:2026-10-31T21:00:00.000Z", "touch");

    expect(tips(card)).toEqual([
      "Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree",
    ]);
  });

  it("puts the box last in the card", async () => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, COVER_04, "touch");

    expect(card.shadowRoot?.querySelector("ha-card")?.lastElementChild).toBe(tip(card));
  });

  it("hides the box from screen readers, which read the item's own label", async () => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, COVER_04, "touch");

    expect(tip(card)?.getAttribute("aria-hidden")).toBe("true");
  });

  it("leaves the item's hover text as it was", async () => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, COVER_04, "touch");

    expect(tappable(card, COVER_04)?.getAttribute("title")).toBe(
      "Cloud cover, the hour from 04:00: 52%",
    );
  });

  it("shows no box before a tap", async () => {
    const card = await mountCard(EVERY_ITEM);

    expect(tip(card)).toBeNull();
  });
});

describe("a tap on a message", () => {
  it.each([
    ["the Seeing row's", "missing:seeing", "sensor.pierpressure_backyard_seeing is unavailable"],
    [
      "the Moon up lane's",
      "missing:moon_up",
      "sensor.pierpressure_backyard_moon_altitude is not in Home Assistant",
    ],
    [
      "the Dew point one in the Temperature chart's key",
      "missing:chart:dew_point",
      "sensor.pierpressure_backyard_dew_point is not in Home Assistant",
    ],
    [
      "the Cloud range row's",
      "missing:cloud_range",
      "sensor.pierpressure_backyard_cloud_cover_max is not in Home Assistant",
    ],
  ])("on %s shows its hover text", async (_, key, text) => {
    const card = await mountCard(EVERY_MESSAGE);

    await tapOn(card, key, "touch");

    expect(tips(card)).toEqual([text]);
  });
});

describe("a tap on the moon drawing", () => {
  it("shows the drawing's text", async () => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, "moon", "touch");

    expect(tips(card)).toEqual(["Moon: waxing gibbous, 78% lit"]);
  });

  it("shows the drawing's text from a shape inside it", async () => {
    const card = await mountCard(EVERY_ITEM);

    tap(tappable(card, "moon")?.querySelector("circle"), "touch");
    await card.updateComplete;

    expect(tips(card)).toEqual(["Moon: waxing gibbous, 78% lit"]);
  });
});

describe("a tap with a box showing", () => {
  const SEEING_21 = "cell:seeing:2026-10-31T21:00:00.000Z";

  function at(card: PierPressureCard, selector: string): Element | null {
    return card.shadowRoot?.querySelector(selector) ?? null;
  }

  it("on the same item closes the box", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, COVER_04, "touch");

    await tapOn(card, COVER_04, "touch");

    expect(tip(card)).toBeNull();
  });

  it("on another item shows that item's text in the one box", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, COVER_04, "touch");

    await tapOn(card, SEEING_21, "touch");

    expect(tips(card)).toEqual(["Seeing, the hour from 21:00: 0.62"]);
  });

  it.each([
    ["a row's label", '[data-row="seeing"] .label'],
    ["an empty part of a track", '[data-row="cloud_cover"] .track'],
    ["the verdict", '[data-field="verdict"]'],
    ["the reasons", ".reasons li"],
  ])("on %s closes the box", async (_, selector) => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, COVER_04, "touch");

    tap(at(card, selector), "touch");
    await card.updateComplete;

    expect([at(card, selector), tip(card)]).toEqual([expect.any(Element), null]);
  });
});

// A press on an element, the moves from there, and how the gesture ends.
async function gesture(
  card: PierPressureCard,
  key: string,
  moves: Array<[number, number]>,
  end = "pointerup",
  pointerType = "touch",
): Promise<void> {
  const element = tappable(card, key);
  element?.dispatchEvent(pointer("pointerdown", 100, 100, 1, pointerType));
  for (const [x, y] of moves) element?.dispatchEvent(pointer("pointermove", x, y, 1, pointerType));
  const [x, y] = moves.at(-1) ?? [100, 100];
  element?.dispatchEvent(pointer(end, x, y, 1, pointerType));
  await card.updateComplete;
}

function axisStart(card: PierPressureCard): string | undefined {
  return card.shadowRoot?.querySelector<HTMLElement>(".strip")?.dataset["axisStart"];
}

describe("what counts as a tap", () => {
  it.each(["mouse", "pen"])("opens a box from a %s", async (pointerType) => {
    const card = await mountCard(EVERY_ITEM);

    await tapOn(card, COVER_04, pointerType);

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });

  it("opens a box from a press that slips 5 px", async () => {
    const card = await mountCard(EVERY_ITEM);

    await gesture(card, COVER_04, [[95, 100]]);

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });

  it.each([
    ["9 px sideways", [[109, 100]]],
    ["9 px up", [[100, 91]]],
    [
      "30 px down and back",
      [
        [100, 130],
        [100, 100],
      ],
    ],
  ] as Array<[string, Array<[number, number]>]>)(
    "opens no box from a press that moves %s",
    async (_, moves) => {
      const card = await mountCard(EVERY_ITEM);

      await gesture(card, COVER_04, moves, "pointerup", "mouse");

      expect(tip(card)).toBeNull();
    },
  );

  it("opens no box from a gesture the browser cancels to scroll the page", async () => {
    const card = await mountCard(EVERY_ITEM);

    await gesture(card, COVER_04, [[96, 88]], "pointercancel");

    expect(tip(card)).toBeNull();
  });

  it("opens a box from the next tap after a gesture the browser cancels", async () => {
    const card = await mountCard(EVERY_ITEM);

    await gesture(card, COVER_04, [[96, 88]], "pointercancel");
    await tapOn(card, COVER_04, "touch");

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });

  it("opens no box from a mouse's other button", async () => {
    const card = await mountCard(EVERY_ITEM);
    const cell = tappable(card, COVER_04);

    cell?.dispatchEvent(pointer("pointerdown", 100, 100, 1, "mouse", 2));
    cell?.dispatchEvent(pointer("pointerup", 100, 100, 1, "mouse", 2));
    await card.updateComplete;

    expect(tip(card)).toBeNull();
  });

  it("ignores a second finger tapped while the first is down", async () => {
    const card = await mountCard(EVERY_ITEM);
    const seeing = tappable(card, "cell:seeing:2026-10-31T21:00:00.000Z");

    tappable(card, COVER_04)?.dispatchEvent(pointer("pointerdown", 100, 100, 1, "touch"));
    seeing?.dispatchEvent(pointer("pointerdown", 300, 100, 2, "touch"));
    seeing?.dispatchEvent(pointer("pointerup", 300, 100, 2, "touch"));
    tappable(card, COVER_04)?.dispatchEvent(pointer("pointerup", 100, 100, 1, "touch"));
    await card.updateComplete;

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });

  it("recovers when a press outside the strip is released outside the card", async () => {
    const card = await mountCard(EVERY_ITEM);

    tappable(card, "moon")?.dispatchEvent(pointer("pointerdown", 100, 100, 1, "mouse"));
    document.body.dispatchEvent(pointer("pointerup", 100, 100, 1, "mouse"));
    await tapOn(card, COVER_04, "mouse");

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });

  it("counts moves outside the card against the tap threshold", async () => {
    const card = await mountCard(EVERY_ITEM);

    tappable(card, "moon")?.dispatchEvent(pointer("pointerdown", 100, 100, 1, "mouse"));
    document.body.dispatchEvent(pointer("pointermove", 120, 100, 1, "mouse"));
    tappable(card, "moon")?.dispatchEvent(pointer("pointerup", 100, 100, 1, "mouse"));
    await card.updateComplete;

    expect(tip(card)).toBeNull();
  });

  it("recovers when the pressed element is removed before a release arrives", async () => {
    const card = await mountCard(EVERY_ITEM);

    tappable(card, "moon")?.dispatchEvent(pointer("pointerdown", 100, 100, 1, "touch"));
    card.hass = {
      states: { ...EVERY_ITEM, [VERDICT]: verdictEntity("GO", { dark_window: NIGHT.attributes["dark_window"] }) },
      config: { time_zone: "UTC" },
    };
    await card.updateComplete;

    const cell = tappable(card, COVER_04);
    for (const type of ["pointerdown", "pointerup"]) {
      cell?.dispatchEvent(
        new PointerEvent(type, {
          bubbles: true,
          composed: true,
          cancelable: true,
          clientX: 100,
          clientY: 100,
          pointerId: 3,
          isPrimary: true,
          button: 0,
          pointerType: "touch",
        }),
      );
    }
    await card.updateComplete;

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 52%"]);
  });
});

// A 24-hour opening axis from 06:00 to 06:00 with forecast hours either side of
// it, drawn across 400 px, so a drag can pan; happy-dom lays nothing out.
const DAY_AROUND_NOW = {
  [VERDICT]: verdictEntity("GO", { dark_window: { start: null, end: null } }),
  [CLOUD_COVER]: forecastEntity(
    Array.from({ length: 60 }, (_, index): [string, unknown] => [
      new Date(Date.parse("2026-11-01T00:00:00Z") + index * 3600_000).toISOString(),
      40,
    ]),
  ),
};

const COVER_14 = "cell:cloud_cover:2026-11-01T14:00:00.000Z";

function layOutDayAroundNow(): void {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-01T12:00:00Z"));
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue(
    new DOMRect(0, 0, 400, 16),
  );
}

describe("a tap on a strip that can pan", () => {
  beforeEach(layOutDayAroundNow);
  afterEach(() => vi.restoreAllMocks());

  it("leaves the axis where it was after a tap that slips", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await gesture(card, COVER_14, [[95, 100]]);

    expect([axisStart(card), tips(card)]).toEqual([
      "2026-11-01T06:00:00.000Z",
      ["Cloud cover, the hour from 14:00: 40%"],
    ]);
  });

  it("opens no box from a drag that pans", async () => {
    const card = await mountCard(DAY_AROUND_NOW);

    await gesture(card, COVER_14, [[60, 100]]);

    expect([axisStart(card), tip(card)]).toEqual(["2026-11-01T08:24:00.000Z", null]);
  });
});

describe("a pan with a box showing", () => {
  beforeEach(layOutDayAroundNow);
  afterEach(() => vi.restoreAllMocks());

  function strip(card: PierPressureCard): HTMLElement | null {
    return card.shadowRoot?.querySelector<HTMLElement>(".strip") ?? null;
  }

  async function press(card: PierPressureCard, key: string, times = 1): Promise<void> {
    for (let index = 0; index < times; index += 1) {
      strip(card)?.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
      await card.updateComplete;
    }
  }

  function backButton(card: PierPressureCard): HTMLButtonElement | null {
    return card.shadowRoot?.querySelector<HTMLButtonElement>(".back button") ?? null;
  }

  it("closes the box after a drag", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await tapOn(card, COVER_14, "touch");

    await gesture(card, COVER_14, [[60, 100]]);

    expect(tip(card)).toBeNull();
  });

  it("closes the box after a sideways wheel movement", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await tapOn(card, COVER_14, "touch");

    strip(card)?.dispatchEvent(
      new WheelEvent("wheel", { bubbles: true, cancelable: true, deltaX: 100 }),
    );
    await card.updateComplete;

    expect(tip(card)).toBeNull();
  });

  it("closes the box after the Right arrow key", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await tapOn(card, COVER_14, "touch");

    await press(card, "ArrowRight");

    expect([axisStart(card), tip(card)]).toEqual(["2026-11-01T07:00:00.000Z", null]);
  });

  it("keeps the box after the Right arrow key at the end of the reach", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await press(card, "ArrowRight", 40);
    await tapOn(card, "cell:cloud_cover:2026-11-03T04:00:00.000Z", "touch");

    await press(card, "ArrowRight");

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 40%"]);
  });

  it("closes the box after Back to tonight is clicked", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await press(card, "ArrowRight", 24);
    await tapOn(card, "cell:cloud_cover:2026-11-02T14:00:00.000Z", "touch");

    tap(backButton(card));
    backButton(card)?.click();
    await card.updateComplete;

    expect([axisStart(card), tip(card)]).toEqual(["2026-11-01T06:00:00.000Z", null]);
  });

  // The browser sends a click with no pointer events for the Enter or Space key.
  it("closes the box after Back to tonight is selected with the keyboard", async () => {
    const card = await mountCard(DAY_AROUND_NOW);
    await press(card, "ArrowRight", 24);
    await tapOn(card, "cell:cloud_cover:2026-11-02T14:00:00.000Z", "touch");

    backButton(card)?.focus();
    backButton(card)?.click();
    await card.updateComplete;

    expect([axisStart(card), tip(card)]).toEqual(["2026-11-01T06:00:00.000Z", null]);
  });

  it("closes the box when the card changes pier", async () => {
    const card = await mountCard({
      ...DAY_AROUND_NOW,
      "sensor.pierpressure_frontyard_verdict": DAY_AROUND_NOW[VERDICT],
      "sensor.pierpressure_frontyard_cloud_cover": DAY_AROUND_NOW[CLOUD_COVER],
    });
    await tapOn(card, COVER_14, "touch");

    card.setConfig({ type: "custom:pierpressure-card", pier: "frontyard" });
    await card.updateComplete;

    expect(tip(card)).toBeNull();
  });
});

describe("an open box when the card redraws", () => {
  async function update(card: PierPressureCard, states: Record<string, HassEntity>) {
    card.hass = { states, config: { time_zone: "UTC" } };
    await card.updateComplete;
  }

  it("shows the now line's latest time after the minute timer", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    vi.setSystemTime(new Date("2026-10-31T21:00:00Z"));
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, "line:now", "touch");

    vi.advanceTimersByTime(60_000);
    await card.updateComplete;

    expect(tips(card)).toEqual(["Now, 21:01"]);
  });

  it("shows a cell's new value after Home Assistant updates its hour", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, COVER_04, "touch");

    await update(card, {
      ...EVERY_ITEM,
      [CLOUD_COVER]: forecastEntity([["2026-11-01T04:00:00Z", 60]]),
    });

    expect(tips(card)).toEqual(["Cloud cover, the hour from 04:00: 60%"]);
  });

  it("shows the new target in a target lane", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, "target:1", "touch");

    await update(card, {
      ...EVERY_ITEM,
      [target(1)]: catalogTarget("M42", "Orion Nebula", {
        start: "2026-11-01T06:00:00Z",
        end: "2026-11-01T10:00:00Z",
      }),
    });

    expect(tips(card)).toEqual(["Orion Nebula (M42) from 06:00 to 10:00"]);
  });

  it("shows a row's new message", async () => {
    const card = await mountCard(EVERY_MESSAGE);
    await tapOn(card, "missing:seeing", "touch");

    await update(card, { ...EVERY_MESSAGE, [SEEING]: { state: "unknown", attributes: {} } });

    expect(tips(card)).toEqual([
      "sensor.pierpressure_backyard_seeing has no forecast for these hours",
    ]);
  });

  it("closes when its hour leaves the axis", async () => {
    const states = {
      ...EVERY_ITEM,
      [CLOUD_COVER]: forecastEntity([["2026-10-31T16:00:00Z", 52]]),
    };
    const card = await mountCard(states);
    await tapOn(card, "cell:cloud_cover:2026-10-31T16:00:00.000Z", "touch");

    vi.setSystemTime(new Date("2026-10-31T21:00:00Z"));
    await update(card, states);

    expect(tip(card)).toBeNull();
  });

  it("closes when its Moon up run starts in another hour", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, "moon-up:2026-10-31T16:00:00.000Z", "touch");

    await update(card, {
      ...EVERY_ITEM,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-10-31T16:00:00Z", -2],
        ["2026-10-31T17:00:00Z", 6],
      ]),
    });

    expect(tip(card)).toBeNull();
  });

  it("closes when the Verdict sensor turns unavailable", async () => {
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, COVER_04, "touch");

    await update(card, { ...EVERY_ITEM, [VERDICT]: verdictEntity("unavailable") });

    expect([card.shadowRoot?.textContent?.includes("PierPressure is offline"), tip(card)]).toEqual([
      true,
      null,
    ]);
  });

  it("keeps the box and the strip on the same clock tick during one redraw", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-31T21:00:59.999Z"));
    const card = await mountCard(EVERY_ITEM);
    await tapOn(card, "line:now", "touch");

    let ticks = 0;
    const base = Date.parse("2026-10-31T21:00:59.999Z");
    const spy = vi.spyOn(Date, "now").mockImplementation(() => base + ticks++ * 60_000);
    card.requestUpdate();
    await card.updateComplete;
    spy.mockRestore();

    expect([tips(card), tappable(card, "line:now")?.getAttribute("aria-label")]).toEqual([
      ["Now, 21:00"],
      "Now, 21:00",
    ]);
  });
});

describe("the box on the card", () => {
  function rule(selector: string): string {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`(?:^|[}\\s])${escaped}\\s*\\{([^}]*)\\}`).exec(cardStyles())?.[1] ?? "";
  }

  it("is taken out of the card's flow, so showing it moves nothing", () => {
    expect([rule("ha-card"), rule(".tip")]).toEqual([
      expect.stringMatching(/position:\s*relative/),
      expect.stringMatching(/position:\s*absolute/),
    ]);
  });

  it("sits above the dusk, dawn and now lines", () => {
    expect(rule(".tip")).toMatch(/z-index:\s*2;/);
  });

  it("lets a tap through to the item under it", () => {
    expect(rule(".tip")).toMatch(/pointer-events:\s*none/);
  });

  it("wraps a long text inside the card", () => {
    expect(rule(".tip")).toMatch(
      /max-width:\s*min\(280px, calc\(100% - 16px\)\);[^}]*overflow-wrap:\s*anywhere/,
    );
  });

  it("leaves the strip as it was", async () => {
    const card = await mountCard(EVERY_ITEM);
    const before = card.shadowRoot?.querySelector(".strip")?.innerHTML;

    await tapOn(card, COVER_04, "touch");

    expect([tip(card), card.shadowRoot?.querySelector(".strip")?.innerHTML]).toEqual([
      expect.any(HTMLElement),
      before,
    ]);
  });

  describe("with a laid-out card", () => {
    let item = new DOMRect(180, 100, 40, 16);

    // The card 400 px wide, the box 100 by 20 px, and the tapped cell at `item`.
    beforeEach(() => {
      item = new DOMRect(180, 100, 40, 16);
      vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (
        this: HTMLElement,
      ) {
        if (this.localName === "ha-card") return new DOMRect(0, 0, 400, 300);
        if (this.classList.contains("tip")) return new DOMRect(0, 0, 100, 20);
        if (this.dataset["tip"] === COVER_04) return item;
        return new DOMRect(0, 0, 0, 0);
      });
    });
    afterEach(() => vi.restoreAllMocks());

    it("places the box above its item", async () => {
      const card = await mountCard(EVERY_ITEM);

      await tapOn(card, COVER_04, "touch");

      expect([tip(card)?.style.left, tip(card)?.style.top]).toEqual(["150px", "76px"]);
    });

    it("moves the box with its item when the card redraws", async () => {
      const card = await mountCard(EVERY_ITEM);
      await tapOn(card, COVER_04, "touch");

      item = new DOMRect(300, 150, 40, 16);
      card.requestUpdate();
      await card.updateComplete;

      expect([tip(card)?.style.left, tip(card)?.style.top]).toEqual(["270px", "126px"]);
    });
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
