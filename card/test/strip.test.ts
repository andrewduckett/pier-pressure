import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_HIGH,
  CLOUD_LOW,
  CLOUD_MID,
  VERDICT,
  cells,
  cloudEntity,
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

describe("the cloud rows", () => {
  it("are Cloud cover, Cloud low, Cloud mid and Cloud high, top to bottom", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(rows(card).map((row) => row.querySelector(".label")?.textContent?.trim())).toEqual([
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
        "sensor.pierpressure_back_yard_cloud_high": cloudEntity([["2026-10-31T21:00:00Z", 40]]),
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
      [CLOUD_COVER]: cloudEntity([
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
      [CLOUD_COVER]: cloudEntity([
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
      [CLOUD_COVER]: cloudEntity([["2026-10-31T17:00:00Z", 30]]),
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
      [CLOUD_COVER]: cloudEntity([["2026-10-31T17:00:00Z", 30]]),
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
      [CLOUD_COVER]: cloudEntity([["2026-10-31T21:00:00Z", value]]),
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
      [CLOUD_LOW]: cloudEntity([
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
      [CLOUD_MID]: cloudEntity([["2026-10-31T22:00:00Z", 0]]),
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
  const forecast = cloudEntity([["2026-10-31T21:00:00Z", 30]]);

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
      [CLOUD_COVER]: cloudEntity([["2026-10-31T21:00:00Z", 30]]),
      [CLOUD_HIGH]: { state: "unavailable", attributes: {} },
    });

    expect(cells(card, "cloud_cover")).toHaveLength(1);
  });

  it("draws four empty rows when no cloud sensor exists", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([rows(card).length, card.shadowRoot?.querySelectorAll(".cell").length]).toEqual([4, 0]);
  });
});
