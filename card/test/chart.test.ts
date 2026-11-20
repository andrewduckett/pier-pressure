import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  DEW_POINT,
  TEMPERATURE,
  VERDICT,
  contrast,
  forecastEntity,
  moonLane,
  mountCard,
  target,
  targetEntity,
  verdictEntity,
} from "./harness";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

// The axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z.
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

const EVENING = { start: "2026-10-31T21:00:00Z", end: "2026-11-01T02:00:00Z" };

function chart(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>('.strip [data-chart="temperature"]') ?? null;
}

function segments(card: PierPressureCard, series: string): Array<[string?, string?]> {
  return [
    ...(chart(card)?.querySelectorAll<SVGElement>(`svg line[data-series="${series}"]`) ?? []),
  ].map((segment) => [segment.dataset["from"], segment.dataset["to"]]);
}

function dots(card: PierPressureCard, series: string): SVGElement[] {
  return [
    ...(chart(card)?.querySelectorAll<SVGElement>(`svg circle[data-series="${series}"]`) ?? []),
  ];
}

function dotTimes(card: PierPressureCard, series: string): Array<string | undefined> {
  return dots(card, series).map((dot) => dot.dataset["at"]);
}

// Hourly points from `first`, `count` of them, each with the value 5.
function hourly(first: string, count: number): Array<[string, unknown]> {
  const start = Date.parse(first);
  return Array.from({ length: count }, (_, index) => [
    new Date(start + index * 3600_000).toISOString(),
    5,
  ]);
}

function scaleLabels(card: PierPressureCard): Array<string | undefined> {
  return [...(chart(card)?.querySelectorAll(".scale [data-celsius]") ?? [])].map((label) =>
    label.textContent?.trim(),
  );
}

function gridline(card: PierPressureCard, celsius: number): SVGElement | null {
  return chart(card)?.querySelector<SVGElement>(`svg line.grid[data-celsius="${celsius}"]`) ?? null;
}

function trackHeight(card: PierPressureCard): string | undefined {
  return chart(card)?.querySelector<HTMLElement>(".track")?.style.height;
}

// A forecast with `values` an hour apart from 21:00 UTC, inside the axis.
function values(...numbers: unknown[]) {
  return forecastEntity(
    numbers.map((value, n) => [new Date(Date.UTC(2026, 9, 31, 21 + n)).toISOString(), value]),
  );
}

// The colour of a line's sample in the key, as its inline style sets it.
function swatch(card: PierPressureCard, series: string): string | undefined {
  const style = chart(card)
    ?.querySelector(`.key [data-series="${series}"] .swatch`)
    ?.getAttribute("style");
  return /background-color: (#[0-9a-f]{6})/.exec(style ?? "")?.[1];
}

function keyNames(card: PierPressureCard): Array<string | undefined> {
  return [...(chart(card)?.querySelectorAll(".key [data-series] .name") ?? [])].map((name) =>
    name.textContent?.trim(),
  );
}

describe("the Temperature chart", () => {
  it("comes after the last target lane and before the time labels", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
      [target(2)]: targetEntity("Orion Nebula", EVENING),
    });

    const row = chart(card);
    expect([
      (row?.previousElementSibling as HTMLElement | null)?.dataset["lane"],
      row?.nextElementSibling?.nextElementSibling?.classList.contains("times"),
    ]).toEqual(["target_2", true]);
  });

  it("comes straight after the Moon up lane with no target tonight", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(chart(card)?.previousElementSibling).toBe(moonLane(card));
  });

  it("names Temperature, then Dew point, in its key", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(keyNames(card)).toEqual(["Temperature", "Dew point"]);
  });
});

describe("a Temperature chart point", () => {
  it("sits at the middle of its hour", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4]]),
    });

    expect(dotTimes(card, "temperature")).toEqual(["2026-10-31T21:30:00.000Z"]);
  });

  // 21:30 is 300 of the axis's 955 minutes in.
  it("is placed in percent of the axis", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T21:00:00Z", 4]]),
    });

    expect(dots(card, "temperature")[0]?.getAttribute("cx")).toBe("31.4136%");
  });

  it("is placed at the height of its value on the scale", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ["2026-10-31T21:00:00Z", 0],
        ["2026-10-31T23:00:00Z", 10],
      ]),
    });

    expect(dots(card, "temperature").map((dot) => dot.getAttribute("cy"))).toEqual([
      "100.0000%",
      "0.0000%",
    ]);
  });

  // The axis runs from 16:30 to 08:25, so the hours from 16:00 to 08:00 overlap it.
  it.each([
    ["2026-10-31T14:00:00Z", []],
    ["2026-10-31T15:00:00Z", ["2026-10-31T15:30:00.000Z"]],
    ["2026-11-01T09:00:00Z", ["2026-11-01T09:30:00.000Z"]],
    ["2026-11-01T10:00:00Z", []],
  ])("at %s is drawn only next to an hour that overlaps the axis", async (hour, drawn) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([[hour, 4]]),
    });

    expect(dotTimes(card, "temperature")).toEqual(drawn);
  });

  it("is drawn for 0 °C", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T22:00:00Z", 0]]),
    });

    expect(dotTimes(card, "temperature")).toEqual(["2026-10-31T22:30:00.000Z"]);
  });

  it("is skipped without a readable time", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ["soon", 4],
        ["2026-10-31T21:00:00Z", 5],
      ]),
    });

    expect(dotTimes(card, "temperature")).toEqual(["2026-10-31T21:30:00.000Z"]);
  });
});

describe("a Temperature chart line", () => {
  it("joins two neighbouring hours that both hold a number", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ["2026-10-31T21:00:00Z", 4],
        ["2026-10-31T22:00:00Z", 3],
      ]),
    });

    expect(segments(card, "temperature")).toEqual([
      ["2026-10-31T21:30:00.000Z", "2026-10-31T22:30:00.000Z"],
    ]);
  });

  it("breaks at a null hour, leaving a dot for a point with no neighbour", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ["2026-10-31T21:00:00Z", 4],
        ["2026-10-31T22:00:00Z", null],
        ["2026-10-31T23:00:00Z", 3],
        ["2026-11-01T00:00:00Z", 2],
      ]),
    });

    expect([segments(card, "temperature"), dotTimes(card, "temperature")]).toEqual([
      [["2026-10-31T23:30:00.000Z", "2026-11-01T00:30:00.000Z"]],
      ["2026-10-31T21:30:00.000Z"],
    ]);
  });

  it("breaks at an hour with no point", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [DEW_POINT]: forecastEntity([
        ["2026-10-31T21:00:00Z", 1],
        ["2026-10-31T23:00:00Z", 2],
      ]),
    });

    expect([segments(card, "dew_point"), dotTimes(card, "dew_point")]).toEqual([
      [],
      ["2026-10-31T21:30:00.000Z", "2026-10-31T23:30:00.000Z"],
    ]);
  });

  it("runs without a break from the axis start to the axis end", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity(hourly("2026-10-31T15:00:00Z", 19)),
    });

    const drawn = segments(card, "temperature");
    const unbroken = drawn.every(([from], index) => index === 0 || from === drawn[index - 1]?.[1]);
    expect([
      unbroken,
      dotTimes(card, "temperature"),
      Date.parse(drawn[0]?.[0] ?? "") <= Date.parse("2026-10-31T16:30:00Z"),
      Date.parse(drawn.at(-1)?.[1] ?? "") >= Date.parse("2026-11-01T08:25:00Z"),
    ]).toEqual([true, [], true, true]);
  });

  it("hides its drawing from screen readers, which read the hover areas", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(chart(card)?.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("reads the sensors named from the pier", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_temperature": forecastEntity([["2026-10-31T21:00:00Z", 4]]),
        "sensor.pierpressure_back_yard_dew_point": forecastEntity([["2026-10-31T21:00:00Z", 1]]),
      },
      "Back-Yard",
    );

    expect([dots(card, "temperature").length, dots(card, "dew_point").length]).toEqual([1, 1]);
  });
});

describe("the Temperature chart's scale", () => {
  const BOTH = {
    [VERDICT]: NIGHT,
    [TEMPERATURE]: values(3.2, 14.8),
    [DEW_POINT]: values(-1.5, 9),
  };

  it("runs from both lines' lowest number to their highest, in 5 °C steps", async () => {
    const card = await mountCard(BOTH);

    expect(scaleLabels(card)).toEqual(["15 °C", "10 °C", "5 °C", "0 °C", "-5 °C"]);
  });

  it("is 16 px tall for each 5 °C step", async () => {
    const card = await mountCard(BOTH);

    expect(trackHeight(card)).toBe("64px");
  });

  it("is raised to 10 °C above its bottom when the numbers span less", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: values(6, 8),
      [DEW_POINT]: values(7),
    });

    expect(scaleLabels(card)).toEqual(["15 °C", "10 °C", "5 °C"]);
  });

  it("is not widened by numbers that lie on a step", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: values(0, 10),
      [DEW_POINT]: values(5),
    });

    expect(scaleLabels(card)).toEqual(["10 °C", "5 °C", "0 °C"]);
  });

  it("counts a number on a later night, off the axis", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ["2026-10-31T21:00:00Z", 5],
        ["2026-10-31T22:00:00Z", 10],
        ["2026-11-02T22:00:00Z", -3],
      ]),
    });

    expect(scaleLabels(card)).toEqual(["10 °C", "5 °C", "0 °C", "-5 °C"]);
  });

  it("leaves out an unavailable sensor's stale forecast", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: values(5, 10),
      [DEW_POINT]: { ...values(-12), state: "unavailable" },
    });

    expect(scaleLabels(card)).toEqual(["15 °C", "10 °C", "5 °C"]);
  });

  it("puts each label level with its gridline", async () => {
    const card = await mountCard(BOTH);

    const labels = [...(chart(card)?.querySelectorAll<HTMLElement>(".scale [data-celsius]") ?? [])];
    expect(
      labels.map((label) => [
        label.style.top,
        gridline(card, Number(label.dataset["celsius"]))?.getAttribute("y1"),
      ]),
    ).toEqual([
      ["0.0000%", "0.0000%"],
      ["25.0000%", "25.0000%"],
      ["50.0000%", "50.0000%"],
      ["75.0000%", "75.0000%"],
      ["100.0000%", "100.0000%"],
    ]);
  });

  // An end label kept level with a gridline at the chart's edge would stick
  // out into the next row.
  it("keeps its top and bottom labels inside the chart", async () => {
    const card = await mountCard(BOTH);

    const labels = [...(chart(card)?.querySelectorAll<HTMLElement>(".scale [data-celsius]") ?? [])];
    expect(labels.map((label) => label.style.transform)).toEqual([
      "translateY(0)",
      "translateY(-50%)",
      "translateY(-50%)",
      "translateY(-50%)",
      "translateY(-100%)",
    ]);
  });

  it("draws a 0 °C point level with the 0 °C gridline", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T22:00:00Z", 0]]),
    });

    expect(dots(card, "temperature")[0]?.getAttribute("cy")).toBe(
      gridline(card, 0)?.getAttribute("y1"),
    );
  });

  it("keeps its labels while the strip pans", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([
        ...hourly("2026-10-31T12:00:00Z", 72),
        ["2026-11-03T12:00:00Z", 14.8],
      ]),
      [DEW_POINT]: values(-1.5),
    });

    card.heldStart = Date.parse("2026-11-01T16:30:00Z");
    await card.updateComplete;

    expect(scaleLabels(card)).toEqual(["15 °C", "10 °C", "5 °C", "0 °C", "-5 °C"]);
  });

  it("is 32 px tall with no gridline or label when neither forecast has a number", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: { state: "unknown", attributes: {} },
      [DEW_POINT]: { state: "unknown", attributes: {} },
    });

    expect([
      trackHeight(card),
      chart(card)?.querySelectorAll("svg line.grid").length,
      scaleLabels(card),
    ]).toEqual(["32px", 0, []]);
  });
});

describe("the Temperature chart's colours", () => {
  const LINES = {
    [VERDICT]: NIGHT,
    [TEMPERATURE]: values(4, 5, null, 3),
    [DEW_POINT]: values(1, 2, null, 0),
  };

  it.each([
    ["temperature", "#d97706"],
    ["dew_point", "#15803d"],
  ])("draws the %s line, its dots and its key sample in %s", async (series, colour) => {
    const card = await mountCard(LINES);

    const segment = chart(card)?.querySelector(`svg line[data-series="${series}"]`);
    expect([
      segment?.getAttribute("stroke"),
      dots(card, series)[0]?.getAttribute("fill"),
      swatch(card, series),
    ]).toEqual([colour, colour, colour]);
  });

  it.each([
    ["temperature", "light", "#ffffff"],
    ["temperature", "dark", "#1c1c1c"],
    ["dew_point", "light", "#ffffff"],
    ["dew_point", "dark", "#1c1c1c"],
  ])("gives the %s line at least 3:1 against the %s card", async (series, _, card) => {
    const mounted = await mountCard(LINES);

    expect(contrast(swatch(mounted, series) ?? "", card)).toBeGreaterThanOrEqual(3);
  });
});
