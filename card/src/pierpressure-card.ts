import { LitElement, css, html, nothing } from "lit";
import { pierSlug, verdictEntityId } from "./entity";
import {
  type Axis,
  type Bar,
  type Cell,
  HOUR,
  type Line,
  type Missing,
  type Strip,
  type TimeLabel,
  asRecord,
  buildStrip,
} from "./strip";

declare const __CARD_VERSION__: string;

export const CARD_VERSION: string = __CARD_VERSION__;

const CARD_TYPE = "pierpressure-card";

const MINUTE = 60 * 1000;

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
    /* Fills the cell, so the arrow is as large as the cell's shorter side allows. */
    .cell svg {
      display: block;
      width: 100%;
      height: 100%;
      color: var(--secondary-text-color);
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
    /* An indent, not padding: the bar's width is set inline, and padding would
       widen it past the end of the target's window. */
    .bar[data-target] {
      background-color: #6250d6;
      color: #ffffff;
      font-size: 0.75em;
      line-height: 16px;
      text-indent: 4px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }
  `;

  // Home Assistant sets hass after setConfig and after the card is attached.
  declare hass?: HomeAssistant;
  declare config?: CardConfig;
  private timer?: ReturnType<typeof setInterval>;

  // The now line, and the fallback axis around it, follow the browser's clock
  // between Home Assistant's state updates.
  override connectedCallback(): void {
    super.connectedCallback();
    clearInterval(this.timer);
    this.timer = setInterval(() => this.requestUpdate(), MINUTE);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    clearInterval(this.timer);
    this.timer = undefined;
  }

  // Home Assistant shows a thrown error in place of the card.
  setConfig(config: Record<string, unknown>): void {
    const pier = config["pier"];
    if (typeof pier !== "string" || pierSlug(pier) === "") {
      throw new Error("pier is required");
    }
    this.config = { type: String(config["type"]), pier };
  }

  // Three target lanes are about one of Home Assistant's 50 px size units.
  getCardSize(): number {
    return 10 + Math.ceil((this.shownStrip()?.targets.length ?? 0) / 3);
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
      ${renderStrip(this.shownStrip())}
    </div>`;
  }

  // The strip draws only beside the verdict, never under a message.
  private shownStrip(): Strip | undefined {
    if (this.hass === undefined || this.config === undefined) return undefined;
    const entity = this.hass.states[verdictEntityId(this.config.pier)];
    if (entity === undefined || entity.state === "unavailable") return undefined;
    return buildStrip(this.hass.states, this.config.pier, Date.now(), this.hass.config?.time_zone);
  }
}

const DASH = "—";

function renderStrip(strip: Strip | undefined) {
  if (strip === undefined) return nothing;
  // Grid row 1 holds the line labels, then come the rows, the Moon up lane, the
  // target lanes and the time labels. The lines' overlay spans from the first
  // row to the last lane.
  const gridRows = strip.rows.length + strip.targets.length + 3;
  const laneEnd = strip.rows.length + strip.targets.length + 3;
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
          <div class="track">
            ${row.cells.map((cell) => renderCell(cell, strip.axis))}
            ${row.missing === undefined ? nothing : renderMissing(row.missing)}
          </div>
        </div>`,
    )}
    <div class="row" data-lane="moon_up">
      <span class="label">Moon up</span>
      <div class="track">${strip.moonUp.map((bar) => renderBar(bar, strip.axis))}</div>
    </div>
    ${strip.targets.map(
      (lane) =>
        html`<div class="row" data-lane=${`target_${lane.rank}`}>
          <span class="label">${lane.label}</span>
          <div class="track">
            ${lane.bar === undefined ? nothing : renderBar(lane.bar, strip.axis, lane.name)}
          </div>
        </div>`,
    )}
    <span></span>
    <div class="track times">
      ${strip.labels.map((label) => renderTimeLabel(label, strip.axis))}
    </div>
    <div class="lines" style=${`grid-column: 2; grid-row: 2 / ${laneEnd}; inset: 0; z-index: 1`}>
      ${strip.lines.map((line) => renderLine(line, strip.axis))}
    </div>
  </div>`;
}

function renderMissing(missing: Missing) {
  const kind = missing.message.toLowerCase().replace(/ /g, "-");
  return html`<span
    class="missing"
    data-missing=${kind}
    title=${missing.text}
    aria-label=${missing.text}
    >${missing.message}</span
  >`;
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
  const place =
    `left: calc(${left}% + ${insetStart}px); ` +
    `width: calc(${width}% - ${insetStart + insetEnd}px)`;
  const style = cell.shade === undefined ? place : `${place}; background-color: ${cell.shade}`;
  // `nothing` leaves an attribute out; `undefined` would leave it empty.
  return html`<div
    class="cell"
    style=${style}
    data-hour=${iso(cell.hour)}
    data-from=${iso(cell.from)}
    data-to=${iso(cell.to)}
    data-shade=${cell.shade ?? nothing}
    data-arrow=${cell.arrow ?? nothing}
    title=${cell.text}
    aria-label=${cell.text}
  >
    ${cell.arrow === undefined ? nothing : renderArrow(cell.arrow)}
  </div>`;
}

// An arrow pointing up, turned about the centre of its 12 by 12 box.
function renderArrow(degrees: number) {
  return html`<svg viewBox="0 0 12 12" aria-hidden="true">
    <g transform=${`rotate(${degrees} 6 6)`}>
      <path d="M6 1 L10.5 6 H7.5 V11 H4.5 V6 H1.5 Z" fill="currentColor"></path>
    </g>
  </svg>`;
}

// A target's bar carries its name; a Moon up bar has none.
function renderBar(bar: Bar, axis: Axis, name?: string) {
  const style = `left: ${offset(bar.from, axis)}%; width: ${share(bar.to - bar.from, axis)}%`;
  return html`<div
    class="bar"
    style=${style}
    ?data-target=${name !== undefined}
    data-start=${iso(bar.start)}
    data-end=${iso(bar.end)}
    data-from=${iso(bar.from)}
    data-to=${iso(bar.to)}
    title=${bar.text}
    aria-label=${bar.text}
  >
    ${name ?? nothing}
  </div>`;
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
