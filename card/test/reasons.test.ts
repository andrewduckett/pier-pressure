import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, cardStyles, field, mountCard, verdictEntity } from "./harness";
import type { PierPressureCard } from "../src/pierpressure-card";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

function reasonsList(card: PierPressureCard): HTMLElement | null {
  return card.shadowRoot?.querySelector<HTMLElement>('ul[aria-label="Reasons"]') ?? null;
}

function reasons(card: PierPressureCard): string[] {
  return [...(reasonsList(card)?.querySelectorAll("li") ?? [])].map(
    (item) => item.textContent?.trim() ?? "",
  );
}

const WIND = "Wind gust over the 40 km/h limit during the dark window.";

describe("the reasons list", () => {
  it("lists a gated NO-GO's reason", async () => {
    const card = await mountCard({
      [VERDICT]: verdictEntity("NO-GO", { score: null, reasons: [WIND] }),
    });

    expect(reasons(card)).toEqual([WIND]);
  });

  it("keeps the reasons' order", async () => {
    const scored = [
      "Cloud: 90% of the dark window usable.",
      "Atmosphere factor 95%.",
      "Score 86/100.",
    ];
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", { reasons: scored }) });

    expect(reasons(card)).toEqual(scored);
  });

  it("sits after the Moon section and before the strip", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("NO-GO", { reasons: [WIND] }) });

    const shown = card.shadowRoot?.querySelectorAll(".summary, .moon, .reasons, .strip");
    const inOrder = [...(shown ?? [])];
    expect(inOrder.map((element) => element.className)).toEqual([
      "summary",
      "moon",
      "reasons",
      "strip",
    ]);
  });
});

describe("reasons that are not a list of strings", () => {
  it.each<[string, Record<string, unknown>]>([
    ["no reasons attribute", {}],
    ["a null", { reasons: null }],
    ["an empty list", { reasons: [] }],
    ["a string", { reasons: "Score 72/100." }],
    ["a list with a number in it", { reasons: ["Score 72/100.", 3] }],
  ])("show no list for %s", async (_, attributes) => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", attributes) });

    expect(reasonsList(card)).toBeNull();
  });

  it("leave the verdict and the strip in place", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", { reasons: [3] }) });

    expect([field(card, "verdict"), card.shadowRoot?.querySelector(".strip") === null]).toEqual([
      "GO",
      false,
    ]);
  });
});

describe("without a verdict", () => {
  it("shows no list before Home Assistant gives the card its state", async () => {
    const card = await mountCard();

    expect(reasonsList(card)).toBeNull();
  });

  it("shows no list before the first verdict", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown") });

    expect(reasonsList(card)).toBeNull();
  });

  it("shows no list while PierPressure is offline", async () => {
    const card = await mountCard({
      [VERDICT]: verdictEntity("unavailable", { reasons: ["Score 72/100."] }),
    });

    expect(reasonsList(card)).toBeNull();
  });

  it("shows no list while the Verdict sensor is missing", async () => {
    const card = await mountCard({}, "frontyard");

    expect(reasonsList(card)).toBeNull();
  });
});

describe("on a night with no astronomical darkness", () => {
  const SUMMER = verdictEntity("NO-GO", {
    dark_window: { start: null, end: null },
    reasons: ["No astronomical night tonight: the sun never drops below -18°."],
  });

  it("lists the reasons before the darkness note", async () => {
    const card = await mountCard({ [VERDICT]: SUMMER });

    const shown = card.shadowRoot?.querySelectorAll(".reasons, .note, .strip");
    expect([...(shown ?? [])].map((element) => element.className)).toEqual([
      "reasons",
      "note",
      "strip",
    ]);
  });

  it("keeps Back to tonight's place straight above the strip", async () => {
    const card = await mountCard({ [VERDICT]: SUMMER });

    const back = card.shadowRoot?.querySelector(".back");
    expect(back?.nextElementSibling?.className).toBe("strip");
  });
});

describe("a reason's UTC times", () => {
  const SPAN = "Scored from 2026-10-31T21:00:00Z to 2026-11-01T03:25:00Z (the rest of tonight).";

  async function shown(reason: string, timeZone = "UTC"): Promise<string[]> {
    const card = await mountCard(
      { [VERDICT]: verdictEntity("GO", { reasons: [reason] }) },
      "backyard",
      timeZone,
    );
    return reasons(card);
  }

  it("show as hours and minutes", async () => {
    expect(await shown(SPAN)).toEqual(["Scored from 21:00 to 03:25 (the rest of tonight)."]);
  });

  it("show in Home Assistant's time zone", async () => {
    expect(await shown(SPAN, "Europe/Paris")).toEqual([
      "Scored from 22:00 to 04:25 (the rest of tonight).",
    ]);
  });

  it("leave a reason with no time as it is", async () => {
    expect(await shown("Atmosphere factor 95%.")).toEqual(["Atmosphere factor 95%."]);
  });

  it("leave a time that is not a real time as it is", async () => {
    const unreal = "Scored from 2026-13-45T21:00:00Z onwards.";

    expect(await shown(unreal)).toEqual([unreal]);
  });
});

describe("a long list", () => {
  const TEN = Array.from({ length: 10 }, (_, index) => `Reason ${index + 1}.`);

  it("shows every reason", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", { reasons: TEN }) });

    expect(reasons(card)).toEqual(TEN);
  });

  it("offers no control that hides the list", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", { reasons: TEN }) });

    expect(reasonsList(card)?.querySelector("button, details")).toBeNull();
  });

  it("is in the secondary text colour", () => {
    const rule = /\.reasons\s*\{([^}]*)\}/.exec(cardStyles())?.[1] ?? "";

    expect(rule.split(";").map((part) => part.trim())).toContain(
      "color: var(--secondary-text-color)",
    );
  });
});
