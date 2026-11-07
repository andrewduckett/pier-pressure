import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { VERDICT, cardText, field, mountCard, verdictEntity } from "./harness";

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
