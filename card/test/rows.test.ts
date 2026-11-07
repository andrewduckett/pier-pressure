import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  DEW_POINT,
  MOON_ALTITUDE,
  HUMIDITY,
  PRECIPITATION_PROBABILITY,
  SEEING,
  TEMPERATURE,
  TRANSPARENCY,
  VERDICT,
  WIND_DIRECTION,
  WIND_GUST,
  WIND_SPEED,
  cells,
  forecastEntity,
  mountCard,
  rowMessage,
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

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

function rows(card: PierPressureCard): HTMLElement[] {
  return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip [data-row]") ?? [])];
}

function row(card: PierPressureCard, key: string): HTMLElement | undefined {
  return rows(card).find((element) => element.dataset["row"] === key);
}

// One value an hour from 21:00 UTC, inside the night's axis.
function hourly(values: number[]): HassEntity {
  return forecastEntity(
    values.map((value, n) => [new Date(Date.UTC(2026, 9, 31, 21 + n)).toISOString(), value]),
  );
}

async function shades(entityId: string, key: string, values: number[]): Promise<string[]> {
  const card = await mountCard({ [VERDICT]: NIGHT, [entityId]: hourly(values) });
  return cells(card, key).map((cell) => cell.dataset["shade"] ?? "");
}

const SUN_AND_CLOUD = ["sun_altitude", "cloud_cover", "cloud_low", "cloud_mid", "cloud_high"];

describe("every timeline row", () => {
  it("is drawn in the YAML strip's order, then the rest", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    const labels = rows(card).map((element) => element.querySelector(".label")?.textContent);
    expect(labels.map((label) => label?.trim())).toEqual([
      "Sun altitude",
      "Moon altitude",
      "Cloud cover",
      "Cloud range",
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

describe("a Rain chance value fills the hour before its time", () => {
  it("fills the hour that ends at its datetime", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-10-31T22:00:00Z", 40]]),
    });

    const [cell] = cells(card, "precipitation_probability");
    expect([cell?.dataset["from"], cell?.dataset["to"]]).toEqual([
      "2026-10-31T21:00:00.000Z",
      "2026-10-31T22:00:00.000Z",
    ]);
  });

  it("draws every hour before a value that overlaps the axis, and none outside it", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [PRECIPITATION_PROBABILITY]: forecastEntity([
        ["2026-10-31T16:00:00Z", 10],
        ["2026-10-31T17:00:00Z", 20],
        ["2026-11-01T09:00:00Z", 30],
        ["2026-11-01T10:00:00Z", 40],
      ]),
    });

    const drawn = cells(card, "precipitation_probability");
    const spans = drawn.map(({ dataset }) => [dataset["hour"], dataset["from"], dataset["to"]]);
    expect(spans).toEqual([
      ["2026-10-31T16:00:00.000Z", "2026-10-31T16:30:00.000Z", "2026-10-31T17:00:00.000Z"],
      ["2026-11-01T08:00:00.000Z", "2026-11-01T08:00:00.000Z", "2026-11-01T08:25:00.000Z"],
    ]);
  });
});

describe("the Moon altitude row darkens as the moon climbs", () => {
  it("steps from set to high", async () => {
    const altitudes = [-10, 0, 3, 6, 12, 18, 24, 30, 60];
    expect(await shades(MOON_ALTITUDE, "moon_altitude", altitudes)).toEqual([
      "#cde2fb",
      "#cde2fb",
      "#9ec5f4",
      "#6da7ec",
      "#3987e5",
      "#256abf",
      "#184f95",
      "#0d366b",
      "#0d366b",
    ]);
  });
});

describe("more wind is darker", () => {
  it("steps Wind gust from calm to gale", async () => {
    expect(await shades(WIND_GUST, "wind_gust", [0, 6.9, 7, 41, 42])).toEqual([
      "#cde2fb",
      "#cde2fb",
      "#9ec5f4",
      "#184f95",
      "#0d366b",
    ]);
  });

  it("shades Wind speed on the same scale", async () => {
    expect(await shades(WIND_SPEED, "wind_speed", [21])).toEqual(["#3987e5"]);
  });
});

describe("worse seeing and transparency are darker", () => {
  it("steps Seeing from excellent to poor", async () => {
    expect(await shades(SEEING, "seeing", [1, 0.8, 0.5, 0])).toEqual([
      "#cde2fb",
      "#9ec5f4",
      "#256abf",
      "#0d366b",
    ]);
  });

  it("keeps a Transparency above 1 at the lightest", async () => {
    expect(await shades(TRANSPARENCY, "transparency", [1.2])).toEqual(["#cde2fb"]);
  });
});

describe("warmer is darker in Temperature and Dew point", () => {
  it("steps Temperature from a cold night to a warm one", async () => {
    expect(await shades(TEMPERATURE, "temperature", [-8, -5, 0, 7, 12, 17, 25])).toEqual([
      "#cde2fb",
      "#9ec5f4",
      "#6da7ec",
      "#3987e5",
      "#256abf",
      "#184f95",
      "#0d366b",
    ]);
  });

  it("shades Dew point on the same scale", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [TEMPERATURE]: hourly([7]),
      [DEW_POINT]: hourly([6]),
    });

    const shaded = ["temperature", "dew_point"].map((key) => cells(card, key)[0]?.dataset["shade"]);
    expect(shaded).toEqual(["#3987e5", "#3987e5"]);
  });
});

describe("more humidity and rain chance is darker", () => {
  it("steps Humidity from dry to saturated", async () => {
    expect(await shades(HUMIDITY, "humidity", [0, 44, 100])).toEqual([
      "#cde2fb",
      "#6da7ec",
      "#0d366b",
    ]);
  });

  it("shades Rain chance on the same scale", async () => {
    const key = "precipitation_probability";
    expect(await shades(PRECIPITATION_PROBABILITY, key, [90])).toEqual(["#0d366b"]);
  });
});

describe("a Wind direction arrow points downwind", () => {
  async function arrowCell(degrees: number): Promise<HTMLElement | undefined> {
    const card = await mountCard({ [VERDICT]: NIGHT, [WIND_DIRECTION]: hourly([degrees]) });
    return cells(card, "wind_direction")[0];
  }

  it.each([
    [225, "45"],
    [0, "180"],
    [270, "90"],
  ])("turns the arrow for a wind from %s° to %s°", async (degrees, rotation) => {
    expect((await arrowCell(degrees))?.dataset["arrow"]).toBe(rotation);
  });

  it("rotates the drawn arrow by the same angle", async () => {
    const group = (await arrowCell(225))?.querySelector("svg g");

    expect(group?.getAttribute("transform")).toBe("rotate(45 6 6)");
  });

  it("gives the cell no shade", async () => {
    const cell = await arrowCell(225);

    expect([cell?.hasAttribute("data-shade"), cell?.style.backgroundColor]).toEqual([false, ""]);
  });

  it("gives a shaded cell no arrow", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT, [WIND_GUST]: hourly([12]) });

    const [cell] = cells(card, "wind_gust");
    expect([cell?.hasAttribute("data-arrow"), cell?.querySelector("svg")]).toEqual([false, null]);
  });
});

describe("hovering over a cell shows its unit", () => {
  it.each([
    [WIND_GUST, "wind_gust", 12.5, "Wind gust, the hour from 21:00: 12.5 km/h"],
    [WIND_SPEED, "wind_speed", 8, "Wind speed, the hour from 21:00: 8 km/h"],
    [TEMPERATURE, "temperature", 4.2, "Temperature, the hour from 21:00: 4.2 °C"],
    [DEW_POINT, "dew_point", -1.5, "Dew point, the hour from 21:00: -1.5 °C"],
    [HUMIDITY, "humidity", 87, "Humidity, the hour from 21:00: 87%"],
    [MOON_ALTITUDE, "moon_altitude", 23.456, "Moon altitude, the hour from 21:00: 23.456°"],
    [SEEING, "seeing", 0.62, "Seeing, the hour from 21:00: 0.62"],
    [TRANSPARENCY, "transparency", 0.4, "Transparency, the hour from 21:00: 0.4"],
  ])("shows %s with its unit", async (entityId, key, value, text) => {
    const card = await mountCard({ [VERDICT]: NIGHT, [entityId]: hourly([value]) });

    const [cell] = cells(card, key);
    expect([cell?.title, cell?.getAttribute("aria-label")]).toEqual([text, text]);
  });

  it("names the start of the hour a Rain chance cell fills", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-10-31T22:00:00Z", 40]]),
    });

    const [cell] = cells(card, "precipitation_probability");
    expect(cell?.title).toBe("Rain chance, the hour from 21:00: 40%");
  });
});

describe("hovering over a Wind direction cell names the compass point", () => {
  it.each([
    [225, "225° from SW"],
    [22.5, "22.5° from NE"],
    [350, "350° from N"],
    [-22.5, "-22.5° from N"],
    [400, "400° from NE"],
  ])("reads %s as %s", async (degrees, reading) => {
    const card = await mountCard({ [VERDICT]: NIGHT, [WIND_DIRECTION]: hourly([degrees]) });

    const [cell] = cells(card, "wind_direction");
    expect(cell?.title).toBe(`Wind direction, the hour from 21:00: ${reading}`);
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

describe("a null Wind direction hour", () => {
  it("has no cell and no arrow", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [WIND_DIRECTION]: forecastEntity([["2026-10-31T22:00:00Z", null]]),
    });

    const row = card.shadowRoot?.querySelector('.strip [data-row="wind_direction"]');
    expect([cells(card, "wind_direction"), row?.querySelector("svg")]).toEqual([[], null]);
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

    expect([
      row(card, "humidity")?.querySelector(".label")?.textContent?.trim(),
      cells(card, "humidity"),
      rowMessage(card, "humidity")?.textContent,
    ]).toEqual(["Humidity", [], "Unavailable"]);
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
      (element) => ![...SUN_AND_CLOUD, "cloud_range"].includes(element.dataset["row"] ?? ""),
    );
    const drawn = others.flatMap((element) => [...element.querySelectorAll(".cell")]);
    const messages = others.map((element) => element.querySelector(".missing")?.textContent);
    expect([others.length, drawn, new Set(messages)]).toEqual([10, [], new Set(["Not found"])]);
  });
});
