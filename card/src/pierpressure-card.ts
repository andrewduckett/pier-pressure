import { LitElement, css, html, nothing } from "lit";
import { pierSlug, verdictEntityId } from "./entity";
import {
  type Axis,
  type Bar,
  type Cell,
  HOUR,
  type Line,
  type TimeLabel,
  asRecord,
  buildStrip,
} from "./strip";

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
      position: relative;
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
    .times {
      color: var(--secondary-text-color);
      font-size: 0.75em;
    }
    .time {
      position: absolute;
      transform: translateX(-50%);
    }
    .cell {
      position: absolute;
      top: 0;
      bottom: 0;
      border-radius: 2px;
    }
    .marks {
      color: #898781;
      font-size: 0.75em;
    }
    .mark {
      position: absolute;
      transform: translateX(-50%);
    }
    .mark[data-mark="now"] {
      color: #e66767;
    }
    .lines {
      position: absolute;
      pointer-events: none;
    }
    /* A box wider than the stroke, so the line is easy to hover. */
    .line {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 8px;
      transform: translateX(-50%);
      pointer-events: auto;
    }
    .line::after {
      content: "";
      position: absolute;
      top: 0;
      bottom: 0;
      left: 3px;
      border-left: 2px dashed #898781;
    }
    .line[data-line="now"]::after {
      border-left: 2px solid #e66767;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      border-radius: 4px;
      background-color: #898781;
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
    return 5;
  }

  // A sections view gives a card half its section's width by default, too
  // narrow for the strip's time labels.
  getGridOptions(): { columns: "full" } {
    return { columns: "full" };
  }

  override render() {
    if (this.config === undefined) return nothing;
    return html`<ha-card header=${`PierPressure ${this.config.pier}`}
      >${this.renderBody()}</ha-card
    >`;
  }

  private renderBody() {
    if (this.hass === undefined || this.config === undefined) return nothing;
    const entityId = verdictEntityId(this.config.pier);
    const entity = this.hass.states[entityId];
    if (entity === undefined) {
      return html`<div class="card-content message">
        No PierPressure verdict found: ${entityId}
      </div>`;
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
      ${renderStrip(this.hass, this.config.pier)}
    </div>`;
  }
}

const DASH = "—";

function renderStrip(hass: HomeAssistant, pier: string) {
  const strip = buildStrip(hass.states, pier, Date.now(), hass.config?.time_zone);
  // Grid row 1 holds the line labels, then come the rows, the Moon up lane and
  // the time labels. The lines' overlay spans from the first row to the lane.
  const gridRows = strip.rows.length + 3;
  const laneEnd = strip.rows.length + 3;
  return html`<div
    class="strip"
    style=${`grid-template-rows: repeat(${gridRows}, auto)`}
    data-axis-start=${iso(strip.axis.start)}
    data-axis-end=${iso(strip.axis.end)}
  >
    <span></span>
    <div class="track marks">${strip.lines.map((line) => renderMark(line, strip.axis))}</div>
    ${strip.rows.map(
      (row) =>
        html`<div class="row" data-row=${row.key}>
          <span class="label">${row.label}</span>
          <div class="track">${row.cells.map((cell) => renderCell(cell, strip.axis))}</div>
        </div>`,
    )}
    <div class="row" data-lane="moon_up">
      <span class="label">Moon up</span>
      <div class="track">${strip.moonUp.map((bar) => renderBar(bar, strip.axis))}</div>
    </div>
    <span></span>
    <div class="track times">
      ${strip.labels.map((label) => renderTimeLabel(label, strip.axis))}
    </div>
    <div class="lines" style=${`grid-column: 2; grid-row: 2 / ${laneEnd}; inset: 0; z-index: 1`}>
      ${strip.lines.map((line) => renderLine(line, strip.axis))}
    </div>
  </div>`;
}

function renderMark(line: Line, axis: Axis) {
  const style = `left: ${offset(line.at, axis)}%`;
  return html`<span class="mark" style=${style} data-mark=${line.kind}>${line.kind}</span>`;
}

function renderLine(line: Line, axis: Axis) {
  const style = `left: ${offset(line.at, axis)}%`;
  return html`<div
    class="line"
    style=${style}
    data-line=${line.kind}
    data-at=${iso(line.at)}
    title=${line.text}
    aria-label=${line.text}
  ></div>`;
}

function renderTimeLabel(label: TimeLabel, axis: Axis) {
  const style = `left: ${offset(label.at, axis)}%`;
  return html`<span class="time" style=${style} data-at=${iso(label.at)}>${label.text}</span>`;
}

// Neighbouring hours keep a 2 px gap, as in the YAML strip; an edge cut off by
// the axis stays flush with the axis end instead.
function renderCell(cell: Cell, axis: Axis) {
  const left = offset(cell.from, axis);
  const width = share(cell.to - cell.from, axis);
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

function renderBar(bar: Bar, axis: Axis) {
  const style = `left: ${offset(bar.from, axis)}%; width: ${share(bar.to - bar.from, axis)}%`;
  return html`<div
    class="bar"
    style=${style}
    data-start=${iso(bar.start)}
    data-end=${iso(bar.end)}
    data-from=${iso(bar.from)}
    data-to=${iso(bar.to)}
    title=${bar.text}
    aria-label=${bar.text}
  ></div>`;
}

// Percent of the axis, so the strip reflows with the card's width.
function share(duration: number, axis: Axis): string {
  return ((duration / (axis.end - axis.start)) * 100).toFixed(4);
}

function offset(at: number, axis: Axis): string {
  return share(at - axis.start, axis);
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
    description: "Tonight's verdict and night strip for one pier.",
  });
}
console.info(`PIERPRESSURE-CARD ${CARD_VERSION}`);
