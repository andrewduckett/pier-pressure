import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  MOON_ALTITUDE,
  VERDICT,
  bars,
  cardStyles,
  forecastEntity,
  moonLane,
  mountCard,
  target,
  targetBar,
  targetEntity,
  targetLanes,
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

// The axis runs from 2026-10-31T16:30:00Z to 2026-11-01T08:25:00Z.
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

const EVENING = { start: "2026-10-31T21:00:00Z", end: "2026-11-01T02:00:00Z" };
const MORNING = { start: "2026-11-01T01:00:00Z", end: "2026-11-01T03:00:00Z" };

function labels(card: PierPressureCard): Array<string | undefined> {
  return targetLanes(card).map((lane) => lane.querySelector(".label")?.textContent?.trim());
}

describe("the target lanes", () => {
  it("draws one lane per rank with a target tonight, in rank order", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
      [target(2)]: targetEntity("Orion Nebula", MORNING),
      [target(3)]: { state: "unavailable", attributes: {} },
    });

    expect(labels(card)).toEqual(["Target 1", "Target 2"]);
  });

  it("puts the first lane straight under the Moon up lane", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
    });

    expect(targetLanes(card)[0]?.previousElementSibling).toBe(moonLane(card));
  });

  it("leaves no gap for a rank with no lane", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
      [target(3)]: targetEntity("Orion Nebula", MORNING),
    });

    expect(targetLanes(card)[1]?.previousElementSibling).toBe(targetLanes(card)[0]);
  });

  it("reads the Target sensors named from the pier", async () => {
    const card = await mountCard(
      {
        "sensor.pierpressure_back_yard_verdict": NIGHT,
        "sensor.pierpressure_back_yard_target_10": targetEntity("Orion Nebula", MORNING),
      },
      "Back-Yard",
    );

    expect(labels(card)).toEqual(["Target 10"]);
  });

  it("draws a bar over the target's window", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
    });

    const data = targetBar(card, 1)?.dataset;
    expect([data?.["start"], data?.["end"], data?.["from"], data?.["to"]]).toEqual([
      "2026-10-31T21:00:00.000Z",
      "2026-11-01T02:00:00.000Z",
      "2026-10-31T21:00:00.000Z",
      "2026-11-01T02:00:00.000Z",
    ]);
  });
});

describe("a rank with no target tonight", () => {
  it.each([
    [
      "is unavailable, with a stale window",
      { state: "unavailable", attributes: { window: EVENING } },
    ],
    ["has an unknown state", targetEntity("Andromeda Galaxy", EVENING, "unknown")],
    ["has an empty state", targetEntity("", EVENING)],
    [
      "has a window that ends before it starts",
      targetEntity("Andromeda Galaxy", { start: EVENING.end, end: EVENING.start }),
    ],
    [
      "has a window that ends as it starts",
      targetEntity("Andromeda Galaxy", { start: EVENING.start, end: EVENING.start }),
    ],
    ["has a window with no end", targetEntity("Andromeda Galaxy", { start: EVENING.start })],
    [
      "has a window whose start is not a time",
      targetEntity("Andromeda Galaxy", { start: "soon", end: EVENING.end }),
    ],
    ["has no window", targetEntity("Andromeda Galaxy", undefined)],
  ])("leaves no lane when it %s", async (_, entity) => {
    const card = await mountCard({ [VERDICT]: NIGHT, [target(1)]: entity });

    expect(targetLanes(card)).toEqual([]);
  });

  it("leaves no lane when Home Assistant has no Target sensors", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect([targetLanes(card), moonLane(card)?.querySelector(".label")?.textContent]).toEqual([
      [],
      "Moon up",
    ]);
  });
});

describe("a target bar at the axis ends", () => {
  it("is cut off at the axis end", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Orion Nebula", {
        start: "2026-11-01T06:00:00Z",
        end: "2026-11-01T10:00:00Z",
      }),
    });

    const data = targetBar(card, 1)?.dataset;
    expect([data?.["from"], data?.["to"]]).toEqual([
      "2026-11-01T06:00:00.000Z",
      "2026-11-01T08:25:00.000Z",
    ]);
  });

  it("is cut off at the axis start", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Orion Nebula", {
        start: "2026-10-31T15:00:00Z",
        end: "2026-10-31T18:00:00Z",
      }),
    });

    const data = targetBar(card, 1)?.dataset;
    expect([data?.["from"], data?.["to"]]).toEqual([
      "2026-10-31T16:30:00.000Z",
      "2026-10-31T18:00:00.000Z",
    ]);
  });

  it.each([
    ["wholly after the axis", { start: "2026-11-02T21:00:00Z", end: "2026-11-03T02:00:00Z" }],
    ["ending at the axis start", { start: "2026-10-31T14:00:00Z", end: "2026-10-31T16:30:00Z" }],
    ["starting at the axis end", { start: "2026-11-01T08:25:00Z", end: "2026-11-01T10:00:00Z" }],
  ])("keeps its lane with no bar for a window %s", async (_, window) => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Orion Nebula", window),
    });

    expect([labels(card), targetBar(card, 1)]).toEqual([["Target 1"], null]);
  });
});

describe("a target bar's look", () => {
  it("holds the target's name", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
    });

    expect(targetBar(card, 1)?.textContent?.trim()).toBe("Andromeda Galaxy");
  });

  it("is marked as a target's bar", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
    });

    expect(targetBar(card, 1)?.hasAttribute("data-target")).toBe(true);
  });

  it("leaves a Moon up bar unmarked and empty", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [MOON_ALTITUDE]: forecastEntity([["2026-10-31T21:00:00Z", 12]]),
    });

    const [bar] = bars(card);
    expect([bar?.hasAttribute("data-target"), bar?.textContent?.trim()]).toEqual([false, ""]);
  });

  it("is violet with white text", () => {
    expect(cardStyles()).toMatch(
      /\.bar\[data-target\]\s*\{[^}]*background-color:\s*#6250d6;[^}]*color:\s*#ffffff/,
    );
  });

  // Padding would widen the bar past its window's end, since its width is set inline.
  it("indents its name without padding", () => {
    const rule = /\.bar\[data-target\]\s*\{([^}]*)\}/.exec(cardStyles())?.[1] ?? "";

    expect([/text-indent:\s*4px/.test(rule), /padding/.test(rule)]).toEqual([true, false]);
  });

  it("cuts a long name short with an ellipsis", () => {
    const rule = /\.bar\[data-target\]\s*\{([^}]*)\}/.exec(cardStyles())?.[1] ?? "";

    expect([
      /overflow:\s*hidden/.test(rule),
      /white-space:\s*nowrap/.test(rule),
      /text-overflow:\s*ellipsis/.test(rule),
    ]).toEqual([true, true, true]);
  });
});

describe("hovering over a target bar", () => {
  function hover(card: PierPressureCard): [string | null | undefined, string | null | undefined] {
    const bar = targetBar(card, 1);
    return [bar?.getAttribute("title"), bar?.getAttribute("aria-label")];
  }

  it("shows the target's name and window", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
    });

    expect(hover(card)).toEqual([
      "Andromeda Galaxy from 21:00 to 02:00",
      "Andromeda Galaxy from 21:00 to 02:00",
    ]);
  });

  it("shows the window's own times where the axis cuts the bar off", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Orion Nebula", {
        start: "2026-11-01T06:00:00Z",
        end: "2026-11-01T10:00:00Z",
      }),
    });

    expect(hover(card)[0]).toBe("Orion Nebula from 06:00 to 10:00");
  });

  it("shows the name alone for a target up all through a polar night", async () => {
    const card = await mountCard({
      [VERDICT]: verdictEntity("GO", {
        dark_window: { start: "2026-12-21T10:58:02Z", end: "2026-12-22T10:58:32Z" },
      }),
      [target(1)]: targetEntity("IC2184", {
        start: "2026-12-21T10:58:02Z",
        end: "2026-12-22T10:58:32Z",
      }),
    });

    expect(hover(card)[0]).toBe("IC2184");
  });

  it("shows the name alone for a window of over 24 hours", async () => {
    const card = await mountCard({
      [VERDICT]: verdictEntity("GO", {
        dark_window: { start: "2026-12-21T10:00:00Z", end: "2026-12-22T10:30:00Z" },
      }),
      [target(1)]: targetEntity("IC2184", {
        start: "2026-12-21T10:00:00Z",
        end: "2026-12-22T10:30:00Z",
      }),
    });

    expect(hover(card)[0]).toBe("IC2184");
  });

  // London's clocks go forward at 01:00 UTC, so 23 hours from 00:30 is 00:30 again.
  it("shows the name alone when both ends read the same time", async () => {
    const card = await mountCard(
      {
        [VERDICT]: verdictEntity("GO", {
          dark_window: { start: "2026-03-29T00:00:00Z", end: "2026-03-30T00:00:00Z" },
        }),
        [target(1)]: targetEntity("Orion Nebula", {
          start: "2026-03-29T00:30:00Z",
          end: "2026-03-29T23:30:00Z",
        }),
      },
      "backyard",
      "Europe/London",
    );

    expect(hover(card)[0]).toBe("Orion Nebula");
  });
});
