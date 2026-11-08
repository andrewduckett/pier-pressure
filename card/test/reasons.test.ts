import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, mountCard, verdictEntity } from "./harness";
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
    const scored = ["Cloud: 90% of the dark window usable.", "Atmosphere factor 95%.", "Score 86/100."];
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", { reasons: scored }) });

    expect(reasons(card)).toEqual(scored);
  });

  it("sits after the Moon section and before the strip", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("NO-GO", { reasons: [WIND] }) });

    const inOrder = [
      ...(card.shadowRoot?.querySelectorAll('.summary, section[aria-label="Moon"], .reasons, .strip') ??
        []),
    ];
    expect(inOrder.map((element) => element.className)).toEqual(["summary", "moon", "reasons", "strip"]);
  });
});
