import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER_MAX,
  CLOUD_COVER_MIN,
  VERDICT,
  cells,
  forecastEntity,
  mountCard,
  verdictEntity,
} from "./harness";
import type { HassEntity, PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

// The axis runs from 16:30 to 08:25 UTC the next day.
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

const HOUR_21 = "2026-10-31T21:00:00Z";

function range(min: HassEntity, max: HassEntity): Record<string, HassEntity> {
  return { [VERDICT]: NIGHT, [CLOUD_COVER_MIN]: min, [CLOUD_COVER_MAX]: max };
}

function columns(card: PierPressureCard): HTMLElement[] {
  return cells(card, "cloud_range");
}

describe("the Cloud range columns", () => {
  it("draw one column for an hour both forecasts give", async () => {
    const card = await mountCard(
      range(forecastEntity([[HOUR_21, 40]]), forecastEntity([[HOUR_21, 70]])),
    );

    expect(columns(card).map((column) => column.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("read the sensors named from the pier's slug", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_cloud_cover_min": forecastEntity([[HOUR_21, 40]]),
        "sensor.pierpressure_back_yard_cloud_cover_max": forecastEntity([[HOUR_21, 70]]),
      },
      "Back-Yard",
    );

    expect(columns(card)).toHaveLength(1);
  });

  it("fill only the hours that overlap the axis, cut off at its ends", async () => {
    const hours = ["2026-10-31T15:00:00Z", "2026-10-31T16:00:00Z", "2026-11-01T09:00:00Z"];
    const card = await mountCard(
      range(
        forecastEntity(hours.map((hour) => [hour, 40])),
        forecastEntity(hours.map((hour) => [hour, 70])),
      ),
    );

    expect(columns(card).map((column) => [column.dataset["hour"], column.dataset["from"]])).toEqual(
      [["2026-10-31T16:00:00.000Z", "2026-10-31T16:30:00.000Z"]],
    );
  });
});

function rangeBar(card: PierPressureCard): HTMLElement | null | undefined {
  return columns(card)[0]?.querySelector<HTMLElement>(".range");
}

async function oneHour(min: unknown, max: unknown): Promise<PierPressureCard> {
  return mountCard(range(forecastEntity([[HOUR_21, min]]), forecastEntity([[HOUR_21, max]])));
}

describe("a Cloud range bar", () => {
  it("runs from the min to the max, measured up the column", async () => {
    const card = await oneHour(40, 70);

    expect(rangeBar(card)?.getAttribute("style")).toBe(
      "bottom: min(40%, calc(100% - 2px)); height: max(2px, 30%)",
    );
  });

  it("is at least 2 px tall when the forecasts agree", async () => {
    const card = await oneHour(40, 40);

    expect(rangeBar(card)?.getAttribute("style")).toBe(
      "bottom: min(40%, calc(100% - 2px)); height: max(2px, 0%)",
    );
  });

  it("stays inside the top of the column at 100%", async () => {
    const card = await oneHour(100, 100);

    expect(rangeBar(card)?.getAttribute("style")).toContain("bottom: min(100%, calc(100% - 2px))");
  });

  it("draws values outside 0 to 100 at the column's ends", async () => {
    const card = await oneHour(-5, 120);

    expect(rangeBar(card)?.getAttribute("style")).toBe(
      "bottom: min(0%, calc(100% - 2px)); height: max(2px, 100%)",
    );
  });

  it("gives the clamped values to the column", async () => {
    const card = await oneHour(-5, 120);

    const column = columns(card)[0];
    expect([column?.dataset["low"], column?.dataset["high"]]).toEqual(["0", "100"]);
  });
});

describe("an hour without a readable pair", () => {
  it("has no column when both forecasts are null", async () => {
    const card = await mountCard(
      range(
        forecastEntity([
          [HOUR_21, 40],
          ["2026-10-31T22:00:00Z", null],
        ]),
        forecastEntity([
          [HOUR_21, 70],
          ["2026-10-31T22:00:00Z", null],
        ]),
      ),
    );

    expect(columns(card).map((column) => column.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("has no column when the max forecast has no point for the hour", async () => {
    const card = await mountCard(
      range(forecastEntity([[HOUR_21, 40]]), forecastEntity([["2026-10-31T22:00:00Z", 70]])),
    );

    expect(columns(card)).toEqual([]);
  });

  it("has no column when a value is not a number", async () => {
    const card = await oneHour(40, "70");

    expect(columns(card)).toEqual([]);
  });

  // Home Assistant applies the two sensors' updates one at a time, so for a
  // moment a new min can meet an old max.
  it("has no column when the min is above the max", async () => {
    const card = await oneHour(70, 20);

    expect(columns(card)).toEqual([]);
  });
});
