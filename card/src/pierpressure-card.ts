import { LitElement, css, html, nothing } from "lit";
import { pierSlug, verdictEntityId } from "./entity";

declare const __CARD_VERSION__: string;

export const CARD_VERSION: string = __CARD_VERSION__;

const CARD_TYPE = "pierpressure-card";

interface CustomCardEntry {
  type: string;
  name: string;
  description?: string;
}

declare global {
  interface Window {
    customCards?: CustomCardEntry[];
  }
}

// Only the part of Home Assistant's frontend object that the card reads.
export interface HassEntity {
  state: string;
  attributes: Record<string, unknown>;
}

export interface HomeAssistant {
  states: Record<string, HassEntity | undefined>;
}

export interface CardConfig {
  type: string;
  pier: string;
}

export class PierPressureCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
  };

  static override styles = css`
    dl {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 4px 16px;
      margin: 0;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
    }
  `;

  // Home Assistant sets hass after setConfig and after the card is attached.
  declare hass?: HomeAssistant;
  declare config?: CardConfig;

  // Home Assistant shows a thrown error in place of the card.
  setConfig(config: Record<string, unknown>): void {
    const pier = config["pier"];
    if (typeof pier !== "string" || pierSlug(pier) === "") {
      throw new Error("pier is required");
    }
    this.config = { type: String(config["type"]), pier };
  }

  getCardSize(): number {
    return 2;
  }

  override render() {
    if (this.config === undefined) return nothing;
    return html`<ha-card header=${`PierPressure ${this.config.pier}`}>${this.renderBody()}</ha-card>`;
  }

  private renderBody() {
    if (this.hass === undefined || this.config === undefined) return nothing;
    const entityId = verdictEntityId(this.config.pier);
    const entity = this.hass.states[entityId];
    if (entity === undefined) {
      return html`<div class="card-content message">No PierPressure verdict found: ${entityId}</div>`;
    }
    if (entity.state === "unavailable") {
      return html`<div class="card-content message">PierPressure is offline</div>`;
    }
    const confidence = asRecord(entity.attributes["confidence"]);
    return html`<div class="card-content">
      <dl>
        <dt>Verdict</dt>
        <dd data-field="verdict">${entity.state === "unknown" ? DASH : entity.state}</dd>
        <dt>Score</dt>
        <dd data-field="score">${shown(entity.attributes["score"])}</dd>
        <dt>Confidence</dt>
        <dd>
          <span data-field="confidence-band">${shown(confidence?.["band"])}</span> ·
          <span data-field="confidence-value">${shown(confidence?.["value"])}</span>
        </dd>
      </dl>
    </div>`;
  }
}

const DASH = "—";

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : undefined;
}

// A type check, not a truthiness check: a score or confidence of 0 is a value.
function shown(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (typeof value === "string" && value !== "") return value;
  return DASH;
}

// HACS can load the file again when it updates the card in place; defining
// the element twice throws, and a second entry would show twice in the picker.
if (!customElements.get(CARD_TYPE)) {
  customElements.define(CARD_TYPE, PierPressureCard);
}
window.customCards ??= [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: "PierPressure",
    description: "Tonight's verdict, score and confidence for one pier.",
  });
}
console.info(`PIERPRESSURE-CARD ${CARD_VERSION}`);
