import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, cardText, field, mountCard, verdictEntity } from "./harness";

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  await import("../src/pierpressure-card");
});

afterEach(() => {
  document.body.replaceChildren();
});

describe("before Home Assistant gives the card its state", () => {
  it("renders the card's frame", async () => {
    const card = await mountCard();

    expect(card.shadowRoot?.querySelector("ha-card")).not.toBeNull();
  });

  it("shows no verdict or message", async () => {
    const card = await mountCard();

    expect(card.shadowRoot?.querySelector("ha-card")?.textContent?.trim()).toBe("");
  });
});

describe("the verdict", () => {
  it("titles the card with the pier", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(card.shadowRoot?.querySelector("ha-card")?.getAttribute("header")).toBe(
      "PierPressure backyard",
    );
  });

  it("shows the Verdict sensor's state", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO") });

    expect(field(card, "verdict")).toBe("GO");
  });

  it("shows a dash for every value before the first verdict", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown") });

    expect([
      field(card, "verdict"),
      field(card, "score"),
      field(card, "confidence-band"),
      field(card, "confidence-value"),
    ]).toEqual(["—", "—", "—", "—"]);
  });

  it("never shows the word unknown", async () => {
    const card = await mountCard({ [VERDICT]: verdictEntity("unknown") });

    expect(cardText(card)).not.toContain("unknown");
  });
});

describe("the score", () => {
  it.each([
    ["72", { score: 72 }],
    ["0", { score: 0 }],
    ["—", { score: null }],
    ["—", {}],
  ])("shows %s for %j", async (shown, attributes) => {
    const card = await mountCard({ [VERDICT]: verdictEntity("MAYBE", attributes) });

    expect(field(card, "score")).toBe(shown);
  });
});

describe("the confidence", () => {
  it.each([
    [["HIGH", "82"], { confidence: { band: "HIGH", value: 82 } }],
    [["LOW", "0"], { confidence: { band: "LOW", value: 0 } }],
    [["MEDIUM", "—"], { confidence: { band: "MEDIUM", value: null } }],
    [["—", "—"], { confidence: null }],
    [["—", "—"], {}],
  ])("shows %j for %j", async (shown, attributes) => {
    const card = await mountCard({ [VERDICT]: verdictEntity("GO", attributes) });

    expect([field(card, "confidence-band"), field(card, "confidence-value")]).toEqual(shown);
  });
});
