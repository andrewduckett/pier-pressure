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
