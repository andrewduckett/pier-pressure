import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  VERDICT,
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
