import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_HIGH,
  CLOUD_LOW,
  CLOUD_MID,
  SUN_ALTITUDE,
  VERDICT,
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
  vi.useRealTimers();
  document.body.replaceChildren();
});

function strip(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>(".strip") ?? null;
}

function axis(card: PierPressureCard): [string | undefined, string | undefined] {
  const element = strip(card);
  return [element?.dataset["axisStart"], element?.dataset["axisEnd"]];
}

function pinClock(iso: string): void {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(iso));
}

describe("the strip's axis", () => {
  it("runs from 4 hours before dusk to 5 hours after dawn", async () => {
    const card = await mountCard({
      [VERDICT]: verdictEntity("GO", {
        dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
      }),
    });

    expect(axis(card)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it.each([
    ["a night with no astronomical darkness", { dark_window: { start: null, end: null } }],
    ["a missing dark window", {}],
    ["a missing end", { dark_window: { start: "2026-10-31T20:30:00Z" } }],
    ["an unreadable start", { dark_window: { start: "dusk", end: "2026-11-01T03:25:00Z" } }],
    ["a start that is not a string", { dark_window: { start: 0, end: "2026-11-01T03:25:00Z" } }],
    [
      "a window that ends before it starts",
      { dark_window: { start: "2026-11-01T03:25:00Z", end: "2026-10-31T20:30:00Z" } },
    ],
    [
      "a window over 48 hours long",
      { dark_window: { start: "2006-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" } },
    ],
  ])("falls back to 6 hours before now to 18 hours after for %s", async (_, attributes) => {
    pinClock("2026-11-01T12:00:00Z");

    const card = await mountCard({ [VERDICT]: verdictEntity("GO", attributes) });

    expect(axis(card)).toEqual(["2026-11-01T06:00:00.000Z", "2026-11-02T06:00:00.000Z"]);
  });

  it("falls back before the first verdict", async () => {
    pinClock("2026-11-01T12:00:00Z");

    const card = await mountCard({ [VERDICT]: verdictEntity("unknown") });

    expect(axis(card)).toEqual(["2026-11-01T06:00:00.000Z", "2026-11-02T06:00:00.000Z"]);
  });
});

function rows(card: PierPressureCard): HTMLElement[] {
  return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip [data-row]") ?? [])];
}

describe("the rows", () => {
  it("are Sun altitude, then Cloud cover, Cloud low, Cloud mid and Cloud high, top to bottom", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(rows(card).map((row) => row.querySelector(".label")?.textContent?.trim())).toEqual([
      "Sun altitude",
      "Cloud cover",
      "Cloud low",
      "Cloud mid",
      "Cloud high",
    ]);
  });

  it("are drawn under the verdict lines", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    const lines = card.shadowRoot?.querySelector("dl");
    const position = lines?.compareDocumentPosition(strip(card) as Node) ?? 0;
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("no strip", () => {
  it("when PierPressure is offline", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unavailable") });

    expect(strip(card)).toBeNull();
  });

  it("when the Verdict sensor is missing", async () => {
    const card = await mountCard({}, "frontyard");

    expect(strip(card)).toBeNull();
  });

  it("before Home Assistant gives the card its state", async () => {
    const card = await mountCard();

    expect(strip(card)).toBeNull();
  });
});

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

describe("a value fills its hour", () => {
  it("reads the cloud sensors named from the pier", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_cloud_high": forecastEntity([["2026-10-31T21:00:00Z", 40]]),
      },
      "Back-Yard",
    );

    expect(cells(card, "cloud_high").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("draws every hour that overlaps the axis, and none outside it", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T15:00:00Z", 10],
        ["2026-10-31T16:00:00Z", 20],
        ["2026-10-31T17:00:00Z", 30],
        ["2026-11-01T08:00:00Z", 40],
        ["2026-11-01T09:00:00Z", 50],
      ]),
    });

    expect(cells(card, "cloud_cover").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T16:00:00.000Z",
      "2026-10-31T17:00:00.000Z",
      "2026-11-01T08:00:00.000Z",
    ]);
  });

  it("cuts a cell off at each axis end", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T16:00:00Z", 20],
        ["2026-11-01T08:00:00Z", 40],
      ]),
    });

    const [first, last] = cells(card, "cloud_cover");
    expect([first?.dataset["from"], last?.dataset["to"]]).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("keeps a cell inside the axis whole", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([["2026-10-31T17:00:00Z", 30]]),
    });

    const [cell] = cells(card, "cloud_cover");
    expect([cell?.dataset["from"], cell?.dataset["to"]]).toEqual([
      "2026-10-31T17:00:00.000Z",
      "2026-10-31T18:00:00.000Z",
    ]);
  });

  // 16:30 to 08:25 is 955 minutes; 17:00 is 30 minutes in, and an hour is 60.
  it("places a cell in percent of the axis", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([["2026-10-31T17:00:00Z", 30]]),
    });

    const [cell] = cells(card, "cloud_cover");
    expect(cell?.style.left).toContain("3.1414%");
    expect(cell?.style.width).toContain("6.2827%");
  });
});

describe("more cloud is darker", () => {
  it.each([
    [0, "#cde2fb"],
    [14, "#cde2fb"],
    [15, "#9ec5f4"],
    [44, "#6da7ec"],
    [89, "#184f95"],
    [90, "#0d366b"],
    [100, "#0d366b"],
    [-5, "#cde2fb"],
    [120, "#0d366b"],
  ])("shades %d%% as %s", async (value, colour) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([["2026-10-31T21:00:00Z", value]]),
    });

    const [cell] = cells(card, "cloud_cover");
    expect(cell?.dataset["shade"]).toBe(colour);
  });
});

describe("a null hour is blank", () => {
  it.each([
    ["null", null],
    ["a string", "40"],
    ["not a number", Number.NaN],
  ])("draws no cell for a value that is %s", async (_, value) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_LOW]: forecastEntity([
        ["2026-10-31T21:00:00Z", 30],
        ["2026-10-31T22:00:00Z", value],
      ]),
    });

    expect(cells(card, "cloud_low").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("draws a cell for 0%", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_MID]: forecastEntity([["2026-10-31T22:00:00Z", 0]]),
    });

    expect(cells(card, "cloud_mid").map((cell) => cell.dataset["shade"])).toEqual(["#cde2fb"]);
  });

  it("skips a point without a readable datetime", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_LOW]: {
        state: "30",
        attributes: {
          forecast: [
            null,
            { value: 30 },
            { datetime: "soon", value: 30 },
            { datetime: "2026-10-31T21:00:00Z", value: 30 },
          ],
        },
      },
    });

    expect(cells(card, "cloud_low")).toHaveLength(1);
  });
});

describe("a missing cloud sensor leaves an empty row", () => {
  const forecast = forecastEntity([["2026-10-31T21:00:00Z", 30]]);

  it.each([
    ["missing", undefined],
    ["unavailable", { state: "unavailable", attributes: {} }],
    ["unavailable but still holding its forecast", { ...forecast, state: "unavailable" }],
    ["without a forecast", { state: "30", attributes: {} }],
    ["with a forecast that is not a list", { state: "30", attributes: { forecast: "soon" } }],
  ])("keeps the row labelled and empty when the sensor is %s", async (_, cloudHigh) => {
    const states = {
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecast,
      ...(cloudHigh && { [CLOUD_HIGH]: cloudHigh }),
    };

    const card = await mountCard(states);

    const row = rows(card).find((element) => element.dataset["row"] === "cloud_high");
    expect(row?.textContent?.trim()).toBe("Cloud high");
    expect(cells(card, "cloud_high")).toEqual([]);
  });

  it("still draws the other rows", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_COVER]: forecastEntity([["2026-10-31T21:00:00Z", 30]]),
      [CLOUD_HIGH]: { state: "unavailable", attributes: {} },
    });

    expect(cells(card, "cloud_cover")).toHaveLength(1);
  });

  it("draws four empty cloud rows when no cloud sensor exists", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const cloudRows = rows(card).filter((row) => row.dataset["row"]?.startsWith("cloud_"));
    expect([cloudRows.length, card.shadowRoot?.querySelectorAll(".cell").length]).toEqual([4, 0]);
  });
});

describe("the Sun altitude row", () => {
  it("reads the sun altitude sensor named from the pier", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_sun_altitude": forecastEntity([
          ["2026-10-31T21:00:00Z", -20],
        ]),
      },
      "Back-Yard",
    );

    expect(cells(card, "sun_altitude").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("draws the hours that overlap the axis, cut off at its ends", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SUN_ALTITUDE]: forecastEntity([
        ["2026-10-31T15:00:00Z", 20],
        ["2026-10-31T16:00:00Z", 10],
        ["2026-10-31T17:00:00Z", 0],
        ["2026-11-01T08:00:00Z", 5],
        ["2026-11-01T09:00:00Z", 15],
      ]),
    });

    expect(
      cells(card, "sun_altitude").map((cell) => [cell.dataset["from"], cell.dataset["to"]]),
    ).toEqual([
      ["2026-10-31T16:30:00.000Z", "2026-10-31T17:00:00.000Z"],
      ["2026-10-31T17:00:00.000Z", "2026-10-31T18:00:00.000Z"],
      ["2026-11-01T08:00:00.000Z", "2026-11-01T08:25:00.000Z"],
    ]);
  });

  it("leaves a null hour blank", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SUN_ALTITUDE]: forecastEntity([
        ["2026-10-31T21:00:00Z", -20],
        ["2026-10-31T22:00:00Z", null],
      ]),
    });

    expect(cells(card, "sun_altitude").map((cell) => cell.dataset["hour"])).toEqual([
      "2026-10-31T21:00:00.000Z",
    ]);
  });

  it("stays labelled and empty when its sensor is unavailable", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SUN_ALTITUDE]: { ...forecastEntity([["2026-10-31T21:00:00Z", -20]]), state: "unavailable" },
      [CLOUD_COVER]: forecastEntity([["2026-10-31T21:00:00Z", 30]]),
    });

    const row = rows(card).find((element) => element.dataset["row"] === "sun_altitude");
    expect([row?.textContent?.trim(), cells(card, "sun_altitude").length]).toEqual([
      "Sun altitude",
      0,
    ]);
    expect(cells(card, "cloud_cover")).toHaveLength(1);
  });
});

describe("hovering over a cell", () => {
  async function hoverText(value: unknown, at: string, timeZone = "UTC"): Promise<string[]> {
    const card = await mountCard(
      { [VERDICT]: NIGHT, [CLOUD_COVER]: forecastEntity([[at, value]]) },
      "backyard",
      timeZone,
    );
    const [cell] = cells(card, "cloud_cover");
    return [cell?.getAttribute("title") ?? "", cell?.getAttribute("aria-label") ?? ""];
  }

  it("shows the row, the hour and the value", async () => {
    expect(await hoverText(40, "2026-10-31T21:00:00Z")).toEqual([
      "Cloud cover, the hour from 21:00: 40%",
      "Cloud cover, the hour from 21:00: 40%",
    ]);
  });

  it("shows the value as the forecast holds it", async () => {
    const [title] = await hoverText(37.5, "2026-10-31T21:00:00Z");

    expect(title).toBe("Cloud cover, the hour from 21:00: 37.5%");
  });

  it("shows the hour in Home Assistant's time zone", async () => {
    const [title] = await hoverText(40, "2026-10-31T21:00:00Z", "Asia/Tokyo");

    expect(title).toBe("Cloud cover, the hour from 06:00: 40%");
  });

  it("writes midnight as 00:00", async () => {
    const [title] = await hoverText(40, "2026-11-01T00:00:00Z");

    expect(title).toBe("Cloud cover, the hour from 00:00: 40%");
  });

  // A browser's language sets the default locale, and some locales write other digits.
  it("uses the digits 0 to 9 in a browser set to Arabic", async () => {
    const Native = Intl.DateTimeFormat;
    class ArabicByDefault extends Native {
      constructor(locales?: Intl.LocalesArgument, options?: Intl.DateTimeFormatOptions) {
        super(locales ?? "ar-EG", options);
      }
    }
    Intl.DateTimeFormat = ArabicByDefault as typeof Intl.DateTimeFormat;
    try {
      const [title] = await hoverText(40, "2026-10-31T21:00:00Z");

      expect(title).toBe("Cloud cover, the hour from 21:00: 40%");
    } finally {
      Intl.DateTimeFormat = Native;
    }
  });

  it("falls back to the browser's time zone for one Intl does not know", async () => {
    const [title] = await hoverText(40, "2026-10-31T21:00:00Z", "Mars/Olympus_Mons");

    expect(title).toMatch(/^Cloud cover, the hour from \d\d:\d\d: 40%$/);
  });

  it("falls back to the browser's time zone when Home Assistant gives none", async () => {
    const card = document.createElement("pierpressure-card") as PierPressureCard;
    card.setConfig({ type: "custom:pierpressure-card", pier: "backyard" });
    document.body.append(card);
    card.hass = {
      states: { [VERDICT]: NIGHT, [CLOUD_COVER]: forecastEntity([["2026-10-31T21:00:00Z", 40]]) },
    };
    await card.updateComplete;

    const [cell] = cells(card, "cloud_cover");
    expect(cell?.getAttribute("title")).toMatch(/^Cloud cover, the hour from \d\d:\d\d: 40%$/);
  });
});

describe("the axis's time labels", () => {
  async function labels(start: string, end: string, timeZone: string) {
    // The night is 4 hours after the axis start to 5 hours before its end.
    const dusk = new Date(Date.parse(start) + 4 * 3600_000).toISOString();
    const dawn = new Date(Date.parse(end) - 5 * 3600_000).toISOString();
    const card = await mountCard(
      { [VERDICT]: verdictEntity("GO", { dark_window: { start: dusk, end: dawn } }) },
      "backyard",
      timeZone,
    );
    return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip .time") ?? [])].map(
      (label) => [label.textContent?.trim(), label.dataset["at"]],
    );
  }

  it("marks every third hour", async () => {
    const shown = await labels("2026-10-31T16:30:00Z", "2026-11-01T08:25:00Z", "UTC");

    expect(shown.map(([text]) => text)).toEqual(["18:00", "21:00", "00:00", "03:00", "06:00"]);
  });

  it("follows a half-hour time zone", async () => {
    const shown = await labels("2026-10-31T16:30:00Z", "2026-11-01T08:25:00Z", "Asia/Kolkata");

    expect(shown.map(([text]) => text)).toEqual(["00:00", "03:00", "06:00", "09:00", "12:00"]);
    expect(shown[0]?.[1]).toBe("2026-10-31T18:30:00.000Z");
  });

  it("marks only every sixth hour on a polar-night axis", async () => {
    const shown = await labels("2026-12-20T07:00:00Z", "2026-12-21T16:00:00Z", "UTC");

    expect(shown.map(([text]) => text)).toEqual(["12:00", "18:00", "00:00", "06:00", "12:00"]);
  });

  it("shows a repeated hour once when clocks go back", async () => {
    const shown = await labels("2026-10-24T18:00:00Z", "2026-10-25T09:00:00Z", "Europe/Athens");

    expect(shown.filter(([text]) => text === "03:00")).toEqual([
      ["03:00", "2026-10-25T00:00:00.000Z"],
    ]);
  });

  it("leaves out an hour at either end of the axis", async () => {
    const shown = await labels("2026-10-31T18:00:00Z", "2026-11-01T09:00:00Z", "UTC");

    expect(shown.map(([text]) => text)).toEqual(["21:00", "00:00", "03:00", "06:00"]);
  });

  // 16:30 to 08:25 is 955 minutes, and 18:00 is 90 minutes in.
  it("places a label in percent of the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const label = card.shadowRoot?.querySelector<HTMLElement>(".strip .time");
    expect(label?.style.left).toBe("9.4241%");
  });
});
