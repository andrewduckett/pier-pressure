import { LitElement, html, nothing } from "lit";
import { type PierChoice, listPiers } from "./entity";
import type { HomeAssistant } from "./pierpressure-card";

export const EDITOR_TYPE = "pierpressure-card-editor";

// Home Assistant's ha-form and its select selector draw the field as Home
// Assistant's own combo box, which lists the piers and takes typed text.
function pierSchema(piers: PierChoice[]) {
  return [{ name: "pier", selector: { select: { custom_value: true, options: piers } } }];
}

// ha-form takes labels from this callback, not from the schema.
function label(): string {
  return "Pier";
}

export class PierPressureCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare config?: Record<string, unknown>;

  // Keeps every key, so a key the editor does not edit survives.
  setConfig(config: Record<string, unknown>): void {
    this.config = config;
  }

  override render() {
    if (this.hass === undefined || this.config === undefined) return nothing;
    const pier = this.config["pier"];
    return html`<ha-form
      .hass=${this.hass}
      .data=${{ pier: typeof pier === "string" ? pier : "" }}
      .schema=${pierSchema(listPiers(this.hass.states))}
      .computeLabel=${label}
    ></ha-form>`;
  }
}

// HACS can load the file again when it updates the card in place.
if (!customElements.get(EDITOR_TYPE)) {
  customElements.define(EDITOR_TYPE, PierPressureCardEditor);
}
