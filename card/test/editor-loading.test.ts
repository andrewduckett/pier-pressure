import { beforeAll, describe, expect, it, vi } from "vitest";
import type { PierPressureCardEditor } from "../src/editor";
import type { PierPressureCard } from "../src/pierpressure-card";

// Its own file: a page cannot undefine an element, and here ha-form starts
// undefined, as it can in Home Assistant before a built-in card editor loads it.
// No field initialisers, so an upgrade keeps what the editor set before it.
class StandInForm extends HTMLElement {
  declare schema?: Array<{ name: string }>;
  declare computeLabel?: (entry: { name: string }) => string;
}

// Home Assistant's entities card, whose editor loads ha-form.
class StandInEntitiesCard extends HTMLElement {
  static async getConfigElement(): Promise<HTMLElement> {
    customElements.define("ha-form", StandInForm);
    return document.createElement("div");
  }
}

let Card: typeof PierPressureCard;

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  Card = (await import("../src/pierpressure-card")).PierPressureCard;
});

async function mountEditor(): Promise<PierPressureCardEditor> {
  const editor = Card.getConfigElement() as PierPressureCardEditor;
  editor.hass = { states: {} };
  editor.setConfig({ type: "custom:pierpressure-card" });
  document.body.append(editor);
  await editor.updateComplete;
  return editor;
}

// In this order: the first test needs neither element defined.
describe("loading Home Assistant's form", () => {
  it("still shows the message when Home Assistant has no entities card", async () => {
    const editor = await mountEditor();

    expect(editor.shadowRoot?.querySelector("[data-note]")?.textContent).toContain(
      "No PierPressure piers found",
    );
  });

  it("loads ha-form through the entities card's editor", async () => {
    customElements.define("hui-entities-card", StandInEntitiesCard);
    const editor = await mountEditor();
    await customElements.whenDefined("ha-form");
    await editor.updateComplete;

    const form = editor.shadowRoot?.querySelector("ha-form");
    expect(
      form instanceof StandInForm && form.schema?.[0] && form.computeLabel?.(form.schema[0]),
    ).toBe("Pier");
  });
});
