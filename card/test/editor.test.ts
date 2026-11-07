import { beforeAll, describe, expect, it, vi } from "vitest";
import type { PierPressureCardEditor } from "../src/editor";
import type { HassEntity, PierPressureCard } from "../src/pierpressure-card";
import { verdictEntity } from "./harness";

interface SchemaEntry {
  name: string;
  selector: { select: { custom_value?: boolean; options: unknown[] } };
}

// Home Assistant's ha-form, as far as the editor uses it: it takes the schema,
// the data and a label callback, and fires value-changed with the whole data.
class StandInForm extends HTMLElement {
  schema: SchemaEntry[] = [];
  data: Record<string, unknown> = {};
  computeLabel?: (entry: SchemaEntry) => string;

  pick(value: Record<string, unknown>): void {
    this.dispatchEvent(new CustomEvent("value-changed", { detail: { value } }));
  }

  label(): string | undefined {
    const entry = this.schema[0];
    return entry === undefined ? undefined : this.computeLabel?.(entry);
  }
}

let Card: typeof PierPressureCard;

beforeAll(async () => {
  vi.spyOn(console, "info").mockImplementation(() => {});
  customElements.define("ha-form", StandInForm);
  Card = (await import("../src/pierpressure-card")).PierPressureCard;
});

const PIERS = {
  "sensor.pierpressure_frontyard_verdict": verdictEntity("GO", { pier: "frontyard" }),
  "sensor.pierpressure_backyard_verdict": verdictEntity("GO", { pier: "backyard" }),
};

async function mountEditor(
  config: Record<string, unknown>,
  states: Record<string, HassEntity> = PIERS,
): Promise<PierPressureCardEditor> {
  const editor = Card.getConfigElement() as PierPressureCardEditor;
  editor.hass = { states };
  editor.setConfig({ type: "custom:pierpressure-card", ...config });
  document.body.append(editor);
  await editor.updateComplete;
  return editor;
}

function form(editor: PierPressureCardEditor): StandInForm {
  const found = editor.shadowRoot?.querySelector("ha-form");
  if (!(found instanceof StandInForm)) throw new Error("the editor renders no ha-form");
  return found;
}

describe("the card's editor", () => {
  it("is a pierpressure-card-editor element", () => {
    expect(Card.getConfigElement().tagName).toBe("PIERPRESSURE-CARD-EDITOR");
  });

  it("has one field, for the pier", async () => {
    const schema = form(await mountEditor({ pier: "backyard" })).schema;

    expect(schema.map((entry) => entry.name)).toEqual(["pier"]);
  });

  it("labels the field Pier", async () => {
    expect(form(await mountEditor({ pier: "backyard" })).label()).toBe("Pier");
  });

  it("offers exactly the listed piers", async () => {
    const select = form(await mountEditor({ pier: "oldpier" })).schema[0]?.selector.select;

    expect(select?.options).toEqual([
      { value: "backyard", label: "backyard" },
      { value: "frontyard", label: "frontyard" },
    ]);
  });

  it("takes a pier that is not listed", async () => {
    const select = form(await mountEditor({ pier: "backyard" })).schema[0]?.selector.select;

    expect(select?.custom_value).toBe(true);
  });

  it("shows the configured pier", async () => {
    expect(form(await mountEditor({ pier: "backyard" })).data).toEqual({ pier: "backyard" });
  });

  it("shows a configured pier that is not listed", async () => {
    expect(form(await mountEditor({ pier: "oldpier" })).data).toEqual({ pier: "oldpier" });
  });

  it("shows an empty pier when the configured one is not text", async () => {
    expect(form(await mountEditor({ pier: 7 })).data).toEqual({ pier: "" });
  });
});

describe("a change in the editor", () => {
  function reported(editor: PierPressureCardEditor): Array<Record<string, unknown>> {
    const configs: Array<Record<string, unknown>> = [];
    editor.addEventListener("config-changed", (event) => {
      configs.push((event as CustomEvent<{ config: Record<string, unknown> }>).detail.config);
    });
    return configs;
  }

  it("reports a picked pier", async () => {
    const editor = await mountEditor({ pier: "backyard" });
    const configs = reported(editor);

    form(editor).pick({ pier: "frontyard" });

    expect(configs).toEqual([{ type: "custom:pierpressure-card", pier: "frontyard" }]);
  });

  it("keeps the keys it does not edit", async () => {
    const editor = await mountEditor({ pier: "backyard", title: "Garden" });
    const configs = reported(editor);

    form(editor).pick({ pier: "frontyard" });

    expect(configs[0]).toEqual({
      type: "custom:pierpressure-card",
      pier: "frontyard",
      title: "Garden",
    });
  });

  it("reports a typed pier unchanged", async () => {
    const editor = await mountEditor({ pier: "backyard" });
    const configs = reported(editor);

    form(editor).pick({ pier: "Garden Pier" });

    expect(configs[0]?.["pier"]).toBe("Garden Pier");
  });

  it("reports a cleared field as an empty pier", async () => {
    const editor = await mountEditor({ pier: "backyard" });
    const configs = reported(editor);

    form(editor).pick({ pier: undefined });

    expect(configs[0]?.["pier"]).toBe("");
  });

  it("reports nothing when the pier is unchanged", async () => {
    const editor = await mountEditor({ pier: "backyard" });
    const configs = reported(editor);

    form(editor).pick({ pier: "backyard" });

    expect(configs).toEqual([]);
  });

  // Home Assistant listens for the change outside the editor's shadow root.
  it("reports the change past the editor's shadow root", async () => {
    const editor = await mountEditor({ pier: "backyard" });
    const events: Event[] = [];
    document.body.addEventListener("config-changed", (event) => events.push(event), { once: true });

    form(editor).pick({ pier: "frontyard" });

    expect(events).toHaveLength(1);
  });
});

describe("an editor with no pier to list", () => {
  function note(editor: PierPressureCardEditor): string | undefined {
    return editor.shadowRoot?.querySelector("[data-note]")?.textContent?.trim();
  }

  it("says no PierPressure pier was found", async () => {
    expect(note(await mountEditor({}, {}))).toBe("No PierPressure piers found");
  });

  it("still takes a typed pier", async () => {
    expect(form(await mountEditor({}, {})).schema[0]?.selector.select.custom_value).toBe(true);
  });

  it("says nothing when a pier is listed", async () => {
    expect(note(await mountEditor({ pier: "backyard" }))).toBeUndefined();
  });
});
