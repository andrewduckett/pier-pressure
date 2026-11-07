import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_HIGH,
  CLOUD_LOW,
  CLOUD_MID,
  MOON_ALTITUDE,
  SUN_ALTITUDE,
  VERDICT,
  bars,
  cells,
  forecastEntity,
  line,
  mark,
  moonLane,
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

describe("the Sun altitude row steps through twilight", () => {
  it.each([
    [10, "#cde2fb"],
    [0, "#9ec5f4"],
    [-5.9, "#9ec5f4"],
    [-6, "#6da7ec"],
    [-12, "#3987e5"],
    [-17.9, "#3987e5"],
    [-18, "#0d366b"],
    [-30, "#0d366b"],
  ])("shades %d° as %s", async (value, colour) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SUN_ALTITUDE]: forecastEntity([["2026-10-31T21:00:00Z", value]]),
    });

    const [cell] = cells(card, "sun_altitude");
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

describe("hovering over a Sun altitude cell", () => {
  it("shows the altitude in degrees", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SUN_ALTITUDE]: forecastEntity([["2026-10-31T21:00:00Z", -14.235]]),
    });

    const [cell] = cells(card, "sun_altitude");
    expect([cell?.getAttribute("title"), cell?.getAttribute("aria-label")]).toEqual([
      "Sun altitude, the hour from 21:00: -14.235°",
      "Sun altitude, the hour from 21:00: -14.235°",
    ]);
  });
});

describe("the Moon up lane", () => {
  function spans(card: PierPressureCard, start: string, end: string): Array<[string?, string?]> {
    return bars(card).map((bar) => [bar.dataset[start], bar.dataset[end]]);
  }

  it("is labelled Moon up, under Cloud high", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const lane = moonLane(card);
    expect([
      lane?.querySelector(".label")?.textContent?.trim(),
      (lane?.previousElementSibling as HTMLElement | null)?.dataset["row"],
    ]).toEqual(["Moon up", "cloud_high"]);
  });

  it("reads the moon altitude sensor named from the pier", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_moon_altitude": forecastEntity([
          ["2026-10-31T21:00:00Z", 12],
        ]),
      },
      "Back-Yard",
    );

    expect(bars(card)).toHaveLength(1);
  });

  it("draws one bar for each run of hours the moon is up", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-10-31T16:00:00Z", 4],
        ["2026-10-31T17:00:00Z", 6],
        ["2026-10-31T18:00:00Z", -1],
        ["2026-10-31T19:00:00Z", 2],
        ["2026-10-31T20:00:00Z", 8],
        ["2026-10-31T21:00:00Z", null],
        ["2026-10-31T22:00:00Z", 12],
        ["2026-10-31T23:00:00Z", 0],
      ]),
    });

    expect(spans(card, "from", "to")).toEqual([
      ["2026-10-31T16:30:00.000Z", "2026-10-31T18:00:00.000Z"],
      ["2026-10-31T19:00:00.000Z", "2026-10-31T21:00:00.000Z"],
      ["2026-10-31T22:00:00.000Z", "2026-10-31T23:00:00.000Z"],
    ]);
  });

  it("ends a run at an hour the forecast has no point for", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-11-01T01:00:00Z", 5],
        ["2026-11-01T03:00:00Z", 5],
      ]),
    });

    expect(spans(card, "start", "end")).toEqual([
      ["2026-11-01T01:00:00.000Z", "2026-11-01T02:00:00.000Z"],
      ["2026-11-01T03:00:00.000Z", "2026-11-01T04:00:00.000Z"],
    ]);
  });

  it("keeps a bar's own hours where the axis cuts it off", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-11-01T07:00:00Z", 5],
        ["2026-11-01T08:00:00Z", 5],
        ["2026-11-01T09:00:00Z", 5],
      ]),
    });

    expect([spans(card, "start", "end"), spans(card, "from", "to")]).toEqual([
      [["2026-11-01T07:00:00.000Z", "2026-11-01T10:00:00.000Z"]],
      [["2026-11-01T07:00:00.000Z", "2026-11-01T08:25:00.000Z"]],
    ]);
  });

  it("draws no bar for a run wholly outside the axis", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-10-31T12:00:00Z", 5],
        ["2026-10-31T13:00:00Z", 5],
      ]),
    });

    expect(bars(card)).toEqual([]);
  });

  it("follows the hours in time order, whatever order the forecast holds them in", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([
        ["2026-10-31T22:00:00Z", 5],
        ["2026-10-31T21:00:00Z", 5],
      ]),
    });

    expect(spans(card, "start", "end")).toEqual([
      ["2026-10-31T21:00:00.000Z", "2026-10-31T23:00:00.000Z"],
    ]);
  });

  it("draws its bars in grey", () => {
    const element = customElements.get("pierpressure-card") as typeof PierPressureCard;
    const styles = [element.styles]
      .flat()
      .map((style) => String(style))
      .join("");

    expect(styles).toMatch(/\.bar\s*\{[^}]*background-color:\s*#898781/);
  });

  it.each([
    [
      "the moon stays down",
      forecastEntity([
        ["2026-10-31T21:00:00Z", -5],
        ["2026-10-31T22:00:00Z", 0],
      ]),
    ],
    ["its sensor is missing", undefined],
    [
      "its sensor is unavailable but kept its forecast",
      { ...forecastEntity([["2026-10-31T21:00:00Z", 12]]), state: "unavailable" },
    ],
    ["its sensor has no forecast", { state: "12", attributes: {} }],
    ["its forecast is not a list", { state: "12", attributes: { forecast: "soon" } }],
  ])("stays labelled with no bars when %s", async (_, moon) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      ...(moon && { [MOON_ALTITUDE]: moon }),
    });

    expect([moonLane(card)?.textContent?.trim(), bars(card)]).toEqual(["Moon up", []]);
  });
});

describe("hovering over a Moon up bar", () => {
  async function hoverText(
    points: Array<[string, unknown]>,
    verdict = NIGHT,
    timeZone = "UTC",
  ): Promise<string[]> {
    const card = await mountCard(
      { [VERDICT]: verdict, [MOON_ALTITUDE]: forecastEntity(points) },
      "backyard",
      timeZone,
    );
    const [bar] = bars(card);
    return [bar?.getAttribute("title") ?? "", bar?.getAttribute("aria-label") ?? ""];
  }

  const RISE_AND_SET: Array<[string, unknown]> = [
    ["2026-10-31T15:00:00Z", -2],
    ["2026-10-31T16:00:00Z", 4],
    ["2026-10-31T17:00:00Z", 6],
    ["2026-10-31T18:00:00Z", -1],
  ];

  it("shows the hours the moon rises and sets", async () => {
    expect(await hoverText(RISE_AND_SET)).toEqual([
      "Moon up from 16:00 to 18:00",
      "Moon up from 16:00 to 18:00",
    ]);
  });

  it("shows the hours in Home Assistant's time zone", async () => {
    const [title] = await hoverText(RISE_AND_SET, NIGHT, "Asia/Tokyo");

    expect(title).toBe("Moon up from 01:00 to 03:00");
  });

  it("leaves out a rise before the forecast starts", async () => {
    const [title] = await hoverText([
      ["2026-11-01T00:00:00Z", 4],
      ["2026-11-01T01:00:00Z", 6],
      ["2026-11-01T02:00:00Z", -1],
    ]);

    expect(title).toBe("Moon up until 02:00");
  });

  it("leaves out a rise after a null hour", async () => {
    const [title] = await hoverText([
      ["2026-10-31T21:00:00Z", null],
      ["2026-10-31T22:00:00Z", 4],
      ["2026-10-31T23:00:00Z", -1],
    ]);

    expect(title).toBe("Moon up until 23:00");
  });

  it("leaves out a set after the forecast ends", async () => {
    const [title] = await hoverText([
      ["2026-11-01T06:00:00Z", -1],
      ["2026-11-01T07:00:00Z", 3],
      ["2026-11-01T08:00:00Z", 5],
    ]);

    expect(title).toBe("Moon up from 07:00");
  });

  it("shows neither when the forecast holds no rise or set", async () => {
    const [title] = await hoverText([["2026-10-31T22:00:00Z", 5]]);

    expect(title).toBe("Moon up");
  });

  const POLAR = verdictEntity("GO", {
    dark_window: { start: "2026-12-20T12:00:00Z", end: "2026-12-21T06:00:00Z" },
  });

  function runOf(hours: number): Array<[string, unknown]> {
    const start = Date.parse("2026-12-20T07:00:00Z");
    const at = (n: number) => new Date(start + n * 60 * 60 * 1000).toISOString();
    return [
      [at(-1), -1],
      ...Array.from({ length: hours }, (_, n): [string, unknown] => [at(n), 5]),
      [at(hours), -1],
    ];
  }

  it("shows the hours of a run shorter than a day", async () => {
    const [title] = await hoverText(runOf(23), POLAR);

    expect(title).toBe("Moon up from 07:00 to 06:00");
  });

  it.each([24, 30])("shows no hours for a run of %d hours", async (hours) => {
    const [title] = await hoverText(runOf(hours), POLAR);

    expect(title).toBe("Moon up");
  });
});

function cardStyles(): string {
  const element = customElements.get("pierpressure-card") as typeof PierPressureCard;
  return [element.styles]
    .flat()
    .map((style) => String(style))
    .join("");
}

describe("the dusk and dawn lines", () => {
  it("sit at the ends of the dark window", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([line(card, "dusk")?.dataset["at"], line(card, "dawn")?.dataset["at"]]).toEqual([
      "2026-10-31T20:30:00.000Z",
      "2026-11-01T03:25:00.000Z",
    ]);
  });

  // 16:30 to 08:25 is 955 minutes; dusk at 20:30 is 240 minutes in.
  it("are placed in percent of the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(line(card, "dusk")?.style.left).toBe("25.1309%");
  });

  it("are labelled dusk and dawn above the strip, over their lines", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(
      ["dusk", "dawn"].map((kind) => [
        mark(card, kind)?.textContent?.trim(),
        mark(card, kind)?.style.left === line(card, kind)?.style.left,
      ]),
    ).toEqual([
      ["dusk", true],
      ["dawn", true],
    ]);
  });

  it("show their time on hover", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(
      ["dusk", "dawn"].flatMap((kind) => [
        line(card, kind)?.getAttribute("title"),
        line(card, kind)?.getAttribute("aria-label"),
      ]),
    ).toEqual(["Dusk, 20:30", "Dusk, 20:30", "Dawn, 03:25", "Dawn, 03:25"]);
  });

  it("are dashed grey", () => {
    expect(cardStyles()).toMatch(/\.line::after\s*\{[^}]*border-left:\s*2px dashed #898781/);
  });

  it("are missing on a night with no astronomical darkness", async () => {
    pinClock("2026-06-21T12:00:00Z");

    const card = await mountCard({
      [VERDICT]: verdictEntity("GO", { dark_window: { start: null, end: null } }),
    });

    expect([line(card, "dusk"), line(card, "dawn"), mark(card, "dusk")]).toEqual([
      null,
      null,
      null,
    ]);
  });
});

describe("the now line", () => {
  it("sits at the browser's time", async () => {
    pinClock("2026-10-31T22:00:00Z");

    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([line(card, "now")?.dataset["at"], mark(card, "now")?.textContent?.trim()]).toEqual([
      "2026-10-31T22:00:00.000Z",
      "now",
    ]);
  });

  it("shows its time on hover", async () => {
    pinClock("2026-10-31T22:00:00Z");

    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([
      line(card, "now")?.getAttribute("title"),
      line(card, "now")?.getAttribute("aria-label"),
    ]).toEqual(["Now, 22:00", "Now, 22:00"]);
  });

  it("is solid red", () => {
    expect(cardStyles()).toMatch(
      /\.line\[data-line="now"\]::after\s*\{[^}]*border-left:\s*2px solid #e66767/,
    );
  });

  it("has a red label", () => {
    expect(cardStyles()).toMatch(/\.mark\[data-mark="now"\]\s*\{[^}]*color:\s*#e66767/);
  });

  it("is missing before the axis starts", async () => {
    pinClock("2026-10-31T12:00:00Z");

    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([line(card, "now"), mark(card, "now")]).toEqual([null, null]);
  });

  it("is missing after the axis ends", async () => {
    pinClock("2026-11-01T09:00:00Z");

    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(line(card, "now")).toBeNull();
  });

  it("sits at the browser's time on a night with no astronomical darkness", async () => {
    pinClock("2026-06-21T12:00:00Z");

    const card = await mountCard({
      [VERDICT]: verdictEntity("GO", { dark_window: { start: null, end: null } }),
    });

    expect(line(card, "now")?.dataset["at"]).toBe("2026-06-21T12:00:00.000Z");
  });
});

describe("the lines' overlay", () => {
  function overlay(card: PierPressureCard): HTMLElement | null | undefined {
    return card.shadowRoot?.querySelector<HTMLElement>(".strip .lines");
  }

  // Grid row 1 holds the line labels, rows 2 to 6 the five rows, and row 7 the
  // Moon up lane, so the overlay runs from line 2 to line 8.
  it("covers the rows and the Moon up lane", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const style = overlay(card)?.getAttribute("style") ?? "";
    expect([style.includes("grid-column: 2"), style.includes("grid-row: 2 / 8")]).toEqual([
      true,
      true,
    ]);
  });

  it("stretches over its grid area", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(overlay(card)?.getAttribute("style")).toContain("inset: 0");
  });

  it("paints above the cells and bars", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const element = overlay(card);
    expect([
      element?.getAttribute("style")?.includes("z-index: 1"),
      element === strip(card)?.lastElementChild,
    ]).toEqual([true, true]);
  });

  it("gives the strip one explicit grid row for each of its rows", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(strip(card)?.getAttribute("style")).toContain("grid-template-rows: repeat(8, auto)");
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
