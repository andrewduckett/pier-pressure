import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, cardStyles, mountCard, verdictEntity } from "./harness";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

// With the harness's clock, the axis runs from 2026-10-31T16:30:00Z to
// 2026-11-01T08:25:00Z.
const NIGHT = verdictEntity("GO", {
  dark_window: { start: "2026-10-31T20:30:00Z", end: "2026-11-01T03:25:00Z" },
});

function days(card: PierPressureCard): HTMLElement[] {
  return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip .days .day") ?? [])];
}

describe("the day labels", () => {
  it("name each day on the axis in order", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(days(card).map((day) => day.textContent?.trim())).toEqual(["Sat 31 Oct", "Sun 1 Nov"]);
  });

  it("follow Home Assistant's time zone", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT }, "backyard", "Asia/Tokyo");

    expect(days(card).map((day) => day.textContent?.trim())).toEqual(["Sun 1 Nov"]);
  });

  it("sit in the row directly under the time labels", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const times = card.shadowRoot?.querySelector(".strip .track.times");
    const row = card.shadowRoot?.querySelector(".strip .track.days");
    expect(times?.nextElementSibling?.nextElementSibling).toBe(row);
  });

  it("mark each day's segment of the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(days(card).map((day) => [day.dataset["from"], day.dataset["to"]])).toEqual([
      ["2026-10-31T16:30:00.000Z", "2026-11-01T00:00:00.000Z"],
      ["2026-11-01T00:00:00.000Z", "2026-11-01T08:25:00.000Z"],
    ]);
  });

  // 16:30 to 08:25 is 955 minutes; midnight is 450 minutes in.
  it("place a day by its segment in percent of the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const day = days(card)[1];
    expect([day?.style.left, day?.style.width]).toEqual(["47.1204%", "52.8796%"]);
  });

  it("share the time labels' text size and colour", () => {
    expect(cardStyles()).toMatch(
      /\.times,\s*\.days\s*\{\s*color: var\(--secondary-text-color\);\s*font-size: 0\.75em;/,
    );
  });
});

function dividers(card: PierPressureCard): HTMLElement[] {
  return [...(card.shadowRoot?.querySelectorAll<HTMLElement>(".strip .dividers .divider") ?? [])];
}

describe("the dividers", () => {
  it("mark the start of each day that starts on the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(dividers(card).map((divider) => divider.dataset["at"])).toEqual([
      "2026-11-01T00:00:00.000Z",
    ]);
  });

  it("leave out a day that starts off the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT }, "backyard", "Asia/Tokyo");

    expect(dividers(card)).toEqual([]);
  });

  it("place a divider in percent of the axis", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    expect(dividers(card)[0]?.style.left).toBe("47.1204%");
  });

  // Rows 2 to 15 hold the fourteen rows, 16 the Moon up lane, 17 the
  // Temperature chart, 18 the time labels and 19 the day labels.
  it("cross only the time-label and day-label rows", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const style = card.shadowRoot?.querySelector(".strip .dividers")?.getAttribute("style") ?? "";
    expect([style.includes("grid-column: 2"), style.includes("grid-row: 18 / span 2")]).toEqual([
      true,
      true,
    ]);
  });

  it("have no hover text", async () => {
    const card = await mountCard({ [VERDICT]: NIGHT });

    const divider = dividers(card)[0];
    expect(["title", "aria-label", "data-tip"].map((name) => divider?.hasAttribute(name))).toEqual([
      false,
      false,
      false,
    ]);
  });

  it("draw a 1 px solid rule in Home Assistant's divider colour", () => {
    expect(cardStyles()).toMatch(
      /\.divider\s*\{[^}]*width: 1px;[^}]*background-color: var\(--divider-color, #898781\);/,
    );
  });
});
