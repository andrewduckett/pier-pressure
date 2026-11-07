import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, mountCard, verdictEntity } from "./harness";
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
