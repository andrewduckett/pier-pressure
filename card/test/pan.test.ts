import { describe, expect, it } from "vitest";
import {
  CLOUD_COVER,
  CLOUD_COVER_MAX,
  PRECIPITATION_PROBABILITY,
  SEEING,
  VERDICT,
  forecastEntity,
  target,
  targetEntity,
  verdictEntity,
} from "./harness";
import type { HassEntity } from "../src/pierpressure-card";
import { HOUR, buildStrip, stripReach } from "../src/strip";

// The judged night's opening axis: 4 hours before a 20:30 dusk to 5 hours after a 03:25 dawn.
const OPENING = {
  start: Date.parse("2026-10-31T16:30:00Z"),
  end: Date.parse("2026-11-01T08:25:00Z"),
};

// Hourly points from `first`, `count` of them, each with the value 40.
function hourly(first: string, count: number, value: unknown = 40): Array<[string, unknown]> {
  const start = Date.parse(first);
  return Array.from({ length: count }, (_, index) => [
    new Date(start + index * HOUR).toISOString(),
    value,
  ]);
}

function iso(reach: { start: number; end: number }): [string, string] {
  return [new Date(reach.start).toISOString(), new Date(reach.end).toISOString()];
}

function reach(states: Record<string, HassEntity>): [string, string] {
  return iso(stripReach(states, "backyard", OPENING));
}

describe("the reach", () => {
  it("runs from the first timeline hour to the end of the last", () => {
    const states = { [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)) };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-03T12:00:00.000Z"]);
  });

  it("counts a Cloud range sensor's hours", () => {
    const states = { [CLOUD_COVER_MAX]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)) };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-03T12:00:00.000Z"]);
  });

  it("starts at the hour a Rain chance value fills, the hour before its time", () => {
    const states = {
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-10-31T12:00:00Z", 20]]),
    };

    expect(reach(states)[0]).toBe("2026-10-31T11:00:00.000Z");
  });

  it("leaves out a null Rain chance point", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24)),
      [PRECIPITATION_PROBABILITY]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24, null)),
    };

    expect(reach(states)[0]).toBe("2026-10-31T12:00:00.000Z");
  });

  it("ends at a Rain chance value's own time, not the hour after it", () => {
    const states = {
      [PRECIPITATION_PROBABILITY]: forecastEntity([["2026-11-02T11:00:00Z", 20]]),
    };

    expect(reach(states)[1]).toBe("2026-11-02T11:00:00.000Z");
  });

  it("counts a null point's hour", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T12:00:00Z", 40],
        ["2026-11-02T11:00:00Z", null],
      ]),
    };

    expect(reach(states)[1]).toBe("2026-11-02T12:00:00.000Z");
  });

  it("leaves out an unavailable sensor's forecast", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 24)),
      [SEEING]: { ...forecastEntity(hourly("2026-10-31T12:00:00Z", 72)), state: "unavailable" },
    };

    expect(reach(states)[1]).toBe("2026-11-01T12:00:00.000Z");
  });

  it("skips a point without a readable time", () => {
    const states = {
      [CLOUD_COVER]: forecastEntity([
        ["2026-10-31T12:00:00Z", 40],
        ["tomorrow", 40],
      ]),
    };

    expect(reach(states)).toEqual(["2026-10-31T12:00:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it("covers the opening axis when the forecast is shorter", () => {
    const states = { [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T18:00:00Z", 12)) };

    expect(reach(states)).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });

  it("is the opening axis with no forecast", () => {
    expect(reach({})).toEqual(["2026-10-31T16:30:00.000Z", "2026-11-01T08:25:00.000Z"]);
  });
});

const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

// Three days of cloud cover around the judged night, so the axis can pan either way.
const THREE_DAYS = {
  [VERDICT]: NIGHT,
  [CLOUD_COVER]: forecastEntity(hourly("2026-10-31T12:00:00Z", 72)),
};

const NOW = Date.parse("2026-10-31T22:00:00Z");

function held(states: Record<string, HassEntity>, start?: string) {
  return buildStrip(
    states,
    "backyard",
    NOW,
    "UTC",
    start === undefined ? undefined : Date.parse(start),
  );
}

describe("a strip with a held start", () => {
  it("is on the opening axis without one", () => {
    expect(iso(held(THREE_DAYS).axis)).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("starts at the held start, as long as the opening axis", () => {
    expect(iso(held(THREE_DAYS, "2026-11-01T16:30:00Z").axis)).toEqual([
      "2026-11-01T16:30:00.000Z",
      "2026-11-02T08:25:00.000Z",
    ]);
  });

  it("stays inside the reach", () => {
    expect(iso(held(THREE_DAYS, "2026-11-05T00:00:00Z").axis)).toEqual([
      "2026-11-02T20:05:00.000Z",
      "2026-11-03T12:00:00.000Z",
    ]);
  });

  it("carries the opening axis", () => {
    expect(iso(held(THREE_DAYS, "2026-11-01T16:30:00Z").opening)).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("carries the reach", () => {
    expect(iso(held(THREE_DAYS).reach)).toEqual([
      "2026-10-31T12:00:00.000Z",
      "2026-11-03T12:00:00.000Z",
    ]);
  });

  it("drops a dusk line panned off the axis", () => {
    const kinds = held(THREE_DAYS, "2026-10-31T22:30:00Z").lines.map((line) => line.kind);

    expect(kinds).toEqual(["dawn"]);
  });

  it("has no dusk or dawn line on the next night", () => {
    const kinds = held(THREE_DAYS, "2026-11-01T16:30:00Z").lines.map((line) => line.kind);

    expect(kinds).toEqual([]);
  });

  it("keeps a target lane with no bar on the next night", () => {
    const states = {
      ...THREE_DAYS,
      [target(1)]: targetEntity("Andromeda Galaxy", {
        start: "2026-10-31T21:00:00Z",
        end: "2026-11-01T02:00:00Z",
      }),
    };

    const lanes = held(states, "2026-11-01T16:30:00Z").targets;

    expect(lanes.map((lane) => [lane.label, lane.bar])).toEqual([["Target 1", undefined]]);
  });
});
