import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  CLOUD_MID,
  SEEING,
  VERDICT,
  WIND_GUST,
  cardText,
  cells,
  field,
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

describe("a missing Verdict sensor", () => {
  it("names the entity the card looked for", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") }, "frontyard");

    expect(cardText(card)).toContain(
      "No PierPressure verdict found: sensor.pierpressure_frontyard_verdict",
    );
  });

  it("shows no verdict", async () => {
    const card = await mountCard({}, "frontyard");

    expect(field(card, "verdict")).toBeUndefined();
  });
});

describe("an unavailable Verdict sensor", () => {
  it("says PierPressure is offline", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unavailable") });

    expect(cardText(card)).toContain("PierPressure is offline");
  });

  it("shows no verdict", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unavailable", { score: 72 }) });

    expect(field(card, "verdict")).toBeUndefined();
  });
});

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

const ON_AXIS = forecastEntity([["2026-10-31T22:00:00Z", 40]]);

function message(card: PierPressureCard, key: string): string | undefined {
  return rowMessage(card, key)?.textContent?.trim();
}

describe("a row with no cell", () => {
  it("says Not found when Home Assistant has no such sensor", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([message(card, "humidity"), rowMessage(card, "humidity")?.dataset["missing"]]).toEqual([
      "Not found",
      "not-found",
    ]);
  });

  it("says Unavailable when its sensor kept a forecast", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [SEEING]: { ...ON_AXIS, state: "unavailable" },
    });

    expect([message(card, "seeing"), rowMessage(card, "seeing")?.dataset["missing"]]).toEqual([
      "Unavailable",
      "unavailable",
    ]);
  });

  it.each<[string, HassEntity]>([
    ["no attributes", { state: "unknown", attributes: {} }],
    ["an empty forecast", forecastEntity([], "unknown")],
    ["only null hours", forecastEntity([["2026-10-31T22:00:00Z", null]])],
    ["only hours off the axis", forecastEntity([["2026-11-02T22:00:00Z", 40]])],
  ])("says No forecast for %s", async (_, wind) => {
    const card = await mountCard({ [VERDICT]: NIGHT, [WIND_GUST]: wind });

    expect([message(card, "wind_gust"), rowMessage(card, "wind_gust")?.dataset["missing"]]).toEqual(
      ["No forecast", "no-forecast"],
    );
  });

  it("says No forecast in every row before the first verdict", async () => {
    const unknown = Object.fromEntries(
      ROWS.map(({ key }) => [`sensor.pierpressure_backyard_${key}`, verdictEntity("unknown")]),
    );
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown"), ...unknown });

    const messages = ROWS.map(({ key }) => message(card, key));
    expect(messages).toEqual(ROWS.map(() => "No forecast"));
  });
});

describe("a row with a cell", () => {
  it("has its cell and no message", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [CLOUD_MID]: forecastEntity([
        ["2026-10-31T21:00:00Z", null],
        ["2026-10-31T22:00:00Z", 40],
        ["2026-10-31T23:00:00Z", null],
      ]),
    });

    expect([cells(card, "cloud_mid").length, rowMessage(card, "cloud_mid")]).toEqual([1, null]);
  });
});
