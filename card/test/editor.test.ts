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
