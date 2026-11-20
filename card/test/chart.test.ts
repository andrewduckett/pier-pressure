import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import {
  VERDICT,
  moonLane,
  mountCard,
  target,
  targetEntity,
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

function chart(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>('.strip [data-chart="temperature"]') ?? null;
}

function keyNames(card: PierPressureCard): Array<string | undefined> {
  return [...(chart(card)?.querySelectorAll(".key [data-series] .name") ?? [])].map((name) =>
    name.textContent?.trim(),
  );
}

describe("the Temperature chart", () => {
  it("comes after the last target lane and before the time labels", async () => {
    const card = await mountCard({
      [VERDICT]: NIGHT,
      [target(1)]: targetEntity("Andromeda Galaxy", EVENING),
      [target(2)]: targetEntity("Orion Nebula", EVENING),
    });

    const row = chart(card);
    expect([
      (row?.previousElementSibling as HTMLElement | null)?.dataset["lane"],
      row?.nextElementSibling?.nextElementSibling?.classList.contains("times"),
    ]).toEqual(["target_2", true]);
  });

  it("comes straight after the Moon up lane with no target tonight", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(chart(card)?.previousElementSibling).toBe(moonLane(card));
  });

  it("names Temperature, then Dew point, in its key", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(keyNames(card)).toEqual(["Temperature", "Dew point"]);
  });
});
