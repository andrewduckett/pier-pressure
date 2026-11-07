import { LitElement, css, html, nothing } from "lit";
import { pierSlug, verdictEntityId } from "./entity";
import { type Axis, type Cell, HOUR, asRecord, buildStrip } from "./strip";

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
  config?: { time_zone?: string };
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
    .strip {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 2px 8px;
      margin-top: 16px;
    }
    .row {
      display: contents;
    }
    .label {
      color: var(--secondary-text-color);
      font-size: 0.85em;
      line-height: 16px;
    }
    .track {
      position: relative;
      height: 16px;
    }
    .cell {
      position: absolute;
      top: 0;
      bottom: 0;
      border-radius: 2px;
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
        <dd data-field="score">${shownNumber(entity.attributes["score"])}</dd>
        <dt>Confidence</dt>
        <dd>
          <span data-field="confidence-band">${shownText(confidence?.["band"])}</span> ·
          <span data-field="confidence-value">${shownNumber(confidence?.["value"])}</span>
        </dd>
      </dl>
      ${this.renderStrip()}
    </div>`;
  }

  private renderStrip() {
    if (this.hass === undefined || this.config === undefined) return nothing;
    const strip = buildStrip(
      this.hass.states,
      this.config.pier,
      Date.now(),
      this.hass.config?.time_zone,
    );
    return html`<div
      class="strip"
      data-axis-start=${iso(strip.axis.start)}
      data-axis-end=${iso(strip.axis.end)}
    >
      ${strip.rows.map(
        (row) => html`<div class="row" data-row=${row.key}>
          <span class="label">${row.label}</span>
          <div class="track">${row.cells.map((cell) => renderCell(cell, strip.axis))}</div>
        </div>`,
      )}
    </div>`;
  }
}

const DASH = "—";

// Neighbouring hours keep a 2 px gap, as in the YAML strip; an edge cut off by
// the axis stays flush with the axis end instead.
function renderCell(cell: Cell, axis: Axis) {
  const span = axis.end - axis.start;
  const left = percent(cell.from - axis.start, span);
  const width = percent(cell.to - cell.from, span);
  const insetStart = cell.from === cell.hour ? 1 : 0;
  const insetEnd = cell.to === cell.hour + HOUR ? 1 : 0;
  const style =
    `left: calc(${left}% + ${insetStart}px); width: calc(${width}% - ${insetStart + insetEnd}px); ` +
    `background-color: ${cell.shade}`;
  return html`<div
    class="cell"
    style=${style}
    data-hour=${iso(cell.hour)}
    data-from=${iso(cell.from)}
    data-to=${iso(cell.to)}
    data-shade=${cell.shade}
    title=${cell.text}
    aria-label=${cell.text}
  ></div>`;
}

function percent(part: number, whole: number): string {
  return ((part / whole) * 100).toFixed(4);
}

function iso(time: number): string {
  return new Date(time).toISOString();
}

// A type check, not a truthiness check: a score or confidence of 0 is a value.
function shownNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? String(value) : DASH;
}

function shownText(value: unknown): string {
  return typeof value === "string" && value !== "" ? value : DASH;
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
