import { LitElement, css, html, nothing } from "lit";
import { type PierChoice, listPiers } from "./entity";
import type { HomeAssistant } from "./pierpressure-card";

export const EDITOR_TYPE = "pierpressure-card-editor";

export class PierPressureCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
  };

  static override styles = css`
    .note {
      margin: 0 0 8px;
      color: var(--secondary-text-color);
    }
  `;

  declare hass?: HomeAssistant;
  declare config?: Record<string, unknown>;

  // Keeps every key, so a key the editor does not edit survives.
  setConfig(config: Record<string, unknown>): void {
    this.config = config;
  }

  override render() {
    if (this.hass === undefined || this.config === undefined) return nothing;
    const pier = this.config["pier"];
    const piers = listPiers(this.hass.states);
    return html`${renderNote(piers)}
      <ha-form
        .hass=${this.hass}
        .data=${{ pier: typeof pier === "string" ? pier : "" }}
        .schema=${pierSchema(piers)}
        .computeLabel=${label}
        @value-changed=${this.changed}
      ></ha-form>`;
  }

  // Clearing the field gives no pier at all, which the card reads as an empty one.
  private changed(event: CustomEvent<{ value: Record<string, unknown> }>): void {
    if (this.config === undefined) return;
    const picked = event.detail.value["pier"];
    const pier = typeof picked === "string" ? picked : "";
    if (pier === this.config["pier"]) return;
    this.config = { ...this.config, pier };
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this.config },
        bubbles: true,
        composed: true,
      }),
    );
  }
}

// Home Assistant's ha-form and its select selector draw the field as Home
// Assistant's own combo box, which lists the piers and takes typed text.
function pierSchema(piers: PierChoice[]) {
  return [{ name: "pier", selector: { select: { custom_value: true, options: piers } } }];
}

function renderNote(piers: PierChoice[]) {
  if (piers.length > 0) return nothing;
  return html`<p class="note" data-note="no-piers">No PierPressure piers found</p>`;
}

// ha-form takes labels from this callback, not from the schema.
function label(): string {
  return "Pier";
}

// HACS can load the file again when it updates the card in place.
if (!customElements.get(EDITOR_TYPE)) {
  customElements.define(EDITOR_TYPE, PierPressureCardEditor);
}
