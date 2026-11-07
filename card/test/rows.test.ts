import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  HUMIDITY,
  SEEING,
  TEMPERATURE,
  VERDICT,
  WIND_GUST,
  cells,
  forecastEntity,
  mountCard,
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

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

function rows(card: PierPressureCard): HTMLElement[] {
  return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip [data-row]") ?? [])];
}

function row(card: PierPressureCard, key: string): HTMLElement | undefined {
  return rows(card).find((element) => element.dataset["row"] === key);
}

const SUN_AND_CLOUD = ["sun_altitude", "cloud_cover", "cloud_low", "cloud_mid", "cloud_high"];

describe("every timeline row", () => {
  it("is drawn in the YAML strip's order, then the rest", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    const labels = rows(card).map((element) => element.querySelector(".label")?.textContent?.trim());
    expect(labels).toEqual([
      "Sun altitude",
      "Moon altitude",
      "Cloud cover",
      "Cloud low",
      "Cloud mid",
      "Cloud high",
      "Wind gust",
      "Seeing",
      "Transparency",
      "Temperature",
      "Dew point",
      "Humidity",
      "Wind speed",
      "Wind direction",
      "Rain chance",
    ]);
  });

  it.each([
    ["dew_point", "sensor.pierpressure_back_yard_dew_point"],
    ["precipitation_probability", "sensor.pierpressure_back_yard_precipitation_probability"],
  ])("reads the %s row from its sensor named from the pier", async (key, entityId) => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        [entityId]: forecastEntity([["2026-10-31T23:00:00Z", 5]]),
      },
      "Back-Yard",
    );

    expect(cells(card, key)).toHaveLength(1);
  });
});

describe("a Moon altitude or weather value fills its hour", () => {
  it("draws every hour that overlaps the axis, and none outside it", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [WIND_GUST]: forecastEntity([
        ["2026-10-31T15:00:00Z", 10],
        ["2026-10-31T16:00:00Z", 20],
        ["2026-10-31T17:00:00Z", 30],
        ["2026-11-01T08:00:00Z", 40],
        ["2026-11-01T09:00:00Z", 50],
      ]),
    });

    expect(cells(card, "wind_gust").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T16:00:00.000Z",
      "2026-10-31T17:00:00.000Z",
      "2026-11-01T08:00:00.000Z",
    ]);
  });

  it("cuts a cell off at each axis end", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [WIND_GUST]: forecastEntity([
        ["2026-10-31T16:00:00Z", 20],
        ["2026-11-01T08:00:00Z", 40],
      ]),
    });

    const [first, last] = cells(card, "wind_gust");
    expect([first?.dataset["from"], last?.dataset["to"]]).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });
});

describe("a null hour is blank", () => {
  it("draws no Seeing cell for a null value", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SEEING]: forecastEntity([["2026-10-31T22:00:00Z", null]]),
    });

    expect(cells(card, "seeing")).toEqual([]);
  });

  it("draws a Temperature cell for 0 °C", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: forecastEntity([["2026-10-31T22:00:00Z", 0]]),
    });

    expect(cells(card, "temperature").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T22:00:00.000Z",
    ]);
  });
});

describe("a missing sensor leaves its row empty", () => {
  it("keeps an unavailable sensor's row labelled and empty", async () => {
    const forecast = forecastEntity([["2026-10-31T21:00:00Z", 80]]);
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecast,
      [HUMIDITY]: { ...forecast, state: "unavailable" },
    });

    expect([row(card, "humidity")?.textContent?.trim(), cells(card, "humidity")]).toEqual([
      "Humidity",
      [],
    ]);
    expect(cells(card, "cloud_cover")).toHaveLength(1);
  });

  it("draws every other row empty with only the sun and cloud sensors", async () => {
    const forecast = forecastEntity([["2026-10-31T21:00:00Z", 30]]);
    const card = await mountCard({
      [VERDICT]: NIGHT,
      ...Object.fromEntries(
        SUN_AND_CLOUD.map((key) => [`sensor.pierpressure_backyard_${key}`, forecast]),
      ),
    });

    const others = rows(card).filter(
      (element) => !SUN_AND_CLOUD.includes(element.dataset["row"] ?? ""),
    );
    const drawn = others.flatMap((element) => [...element.querySelectorAll(".cell")]);
    expect([others.length, drawn]).toEqual([10, []]);
  });
});
