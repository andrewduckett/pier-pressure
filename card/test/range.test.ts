import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  CLOUD_COVER_MIN,
  VERDICT,
  cardStyles,
  cells,
  forecastEntity,
  mountCard,
  rowMessage,
  verdictEntity,
} from "./harness";
import type { HassEntity, PierPressureCard } from "../src/pierpressure-card";
import { ROWS } from "../src/strip";

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

// A readable pair at 23:00 keeps the row in the strip, so an empty 21:00 is
// the hour's own doing.
const HOUR_23 = "2026-10-31T23:00:00Z";

async function besidePair(min: unknown, max: unknown): Promise<PierPressureCard> {
  return mountCard(
    range(
      forecastEntity([
        [HOUR_21, min],
        [HOUR_23, 50],
      ]),
      forecastEntity([
        [HOUR_21, max],
        [HOUR_23, 60],
      ]),
    ),
  );
}

function drawnHours(card: PierPressureCard): Array<string | undefined> {
  return columns(card).map((column) => column.dataset["hour"]);
}

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
      range(
        forecastEntity([
          [HOUR_21, 40],
          [HOUR_23, 50],
        ]),
        forecastEntity([
          ["2026-10-31T22:00:00Z", 70],
          [HOUR_23, 60],
        ]),
      ),
    );

    expect(drawnHours(card)).toEqual(["2026-10-31T23:00:00.000Z"]);
  });

  it("has no column when a value is not a number", async () => {
    const card = await besidePair(40, "70");

    expect(drawnHours(card)).toEqual(["2026-10-31T23:00:00.000Z"]);
  });

  // Home Assistant applies the two sensors' updates one at a time, so for a
  // moment a new min can meet an old max.
  it("has no column when the min is above the max", async () => {
    const card = await besidePair(70, 20);

    expect(drawnHours(card)).toEqual(["2026-10-31T23:00:00.000Z"]);
  });
});

describe("hovering over a Cloud range column", () => {
  it("shows the hour and both values as the forecasts hold them", async () => {
    const card = await oneHour(40, 70.5);

    const column = columns(card)[0];
    expect([column?.title, column?.getAttribute("aria-label")]).toEqual([
      "Cloud range, the hour from 21:00: 40% to 70.5%",
      "Cloud range, the hour from 21:00: 40% to 70.5%",
    ]);
  });

  it("shows a value outside 0 to 100 unclamped", async () => {
    const card = await oneHour(-5, 120);

    expect(columns(card)[0]?.title).toBe("Cloud range, the hour from 21:00: -5% to 120%");
  });
});

const NULLS = forecastEntity([
  [HOUR_21, null],
  ["2026-10-31T22:00:00Z", null],
]);
const ON_AXIS = forecastEntity([[HOUR_21, 40]]);
// A paired hour two nights on, so the row stays with nothing to draw on the axis.
const OFF_AXIS = forecastEntity([
  [HOUR_21, null],
  ["2026-11-02T21:00:00Z", 40],
]);

function message(card: PierPressureCard): [string | undefined, string | undefined] {
  const element = rowMessage(card, "cloud_range");
  return [element?.textContent?.trim(), element?.title];
}

function cloudRangeRow(card: PierPressureCard): HTMLElement | null | undefined {
  return card.shadowRoot?.querySelector<HTMLElement>('.strip [data-row="cloud_range"]');
}

describe("a Cloud range row with no paired hour", () => {
  it("is left out when both forecasts are null", async () => {
    const card = await mountCard(range(NULLS, NULLS));

    expect(cloudRangeRow(card)).toBeNull();
  });

  it("is left out before the first verdict", async () => {
    const unknown = Object.fromEntries(
      [...ROWS.map(({ key }) => key), "cloud_cover_min", "cloud_cover_max"].map((key) => [
        `sensor.pierpressure_backyard_${key}`,
        verdictEntity("unknown"),
      ]),
    );
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown"), ...unknown });

    expect(cloudRangeRow(card)).toBeNull();
  });

  it("stays to say a sensor is not in Home Assistant", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT, [CLOUD_COVER_MIN]: NULLS });

    expect(message(card)[0]).toBe("Not found");
  });

  it("stays to say a sensor is unavailable", async () => {
    const card = await mountCard(range(verdictEntity("unavailable"), NULLS));

    expect(message(card)[0]).toBe("Unavailable");
  });
});

describe("a Cloud range row with no column", () => {
  it("marks the message for styling", async () => {
    const card = await mountCard(range(OFF_AXIS, OFF_AXIS));

    expect(rowMessage(card, "cloud_range")?.dataset["missing"]).toBe("needs-two-forecasts");
  });

  it("leaves the Cloud cover row drawing as usual", async () => {
    const card = await mountCard({ ...range(NULLS, NULLS), [CLOUD_COVER]: ON_AXIS });

    expect([cells(card, "cloud_cover").length, rowMessage(card, "cloud_cover")]).toEqual([1, null]);
  });

  it("names the max sensor when it is not in Home Assistant", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT, [CLOUD_COVER_MIN]: ON_AXIS });

    expect(message(card)).toEqual([
      "Not found",
      "sensor.pierpressure_backyard_cloud_cover_max is not in Home Assistant",
    ]);
  });

  it("names the min sensor when it is unavailable", async () => {
    const card = await mountCard(
      range({ ...ON_AXIS, state: "unavailable" }, forecastEntity([[HOUR_21, 70]])),
    );

    expect(message(card)).toEqual([
      "Unavailable",
      "sensor.pierpressure_backyard_cloud_cover_min is unavailable",
    ]);
  });

  it("says a missing sensor before an unavailable one", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER_MIN]: { ...ON_AXIS, state: "unavailable" },
    });

    expect(message(card)[0]).toBe("Not found");
  });
});

describe("a Cloud range row with a column", () => {
  it("shows no message", async () => {
    const card = await oneHour(40, 70);

    expect(rowMessage(card, "cloud_range")).toBeNull();
  });
});

// The declarations of every rule whose selector list holds `selector`.
function declarations(selector: string): string[] {
  const css = cardStyles().replace(/\/\*[\s\S]*?\*\//g, "");
  const rules = [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)];
  return rules
    .filter(([, selectors]) => selectors?.split(",").some((part) => part.trim() === selector))
    .flatMap(([, , body]) => (body ?? "").split(";").map((part) => part.trim()));
}

describe("the Cloud range row's styles", () => {
  it("make the row's track twice a shaded row's height", () => {
    expect(declarations('.row[data-row="cloud_range"] .track')).toContain("height: 32px");
  });

  it.each([".label", ".missing"])("centre its %s in the taller row", (part) => {
    expect(declarations(`.row[data-row="cloud_range"] ${part}`)).toContain("line-height: 32px");
  });

  it.each(["background-color: #cde2fb", "overflow: hidden"])(
    "style each column with %s",
    (declaration) => {
      expect(declarations(".column")).toContain(declaration);
    },
  );

  it.each(["position: absolute", "left: 0", "right: 0", "background-color: #256abf"])(
    "style each range bar with %s",
    (declaration) => {
      expect(declarations(".range")).toContain(declaration);
    },
  );

  it("mark each column for those styles", async () => {
    const card = await oneHour(40, 70);

    expect(columns(card)[0]?.classList.contains("column")).toBe(true);
  });
});
