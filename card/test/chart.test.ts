import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  DEW_POINT,
  TEMPERATURE,
  VERDICT,
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
