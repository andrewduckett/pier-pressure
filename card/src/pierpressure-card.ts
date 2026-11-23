import { LitElement, css, html, nothing, svg } from "lit";
import { chartStyles, renderChart, renderMissing } from "./chart";
import { EDITOR_TYPE } from "./editor";
import { listPiers, pierSlug, verdictEntityId } from "./entity";
import { type MoonDrawing, type MoonView, litPath, readMoon } from "./moon";
import { hourPlace, iso, offset, share } from "./place";
import {
  type Axis,
  type Band,
  type Bar,
  type Cell,
  HOUR,
  type Line,
  type Strip,
  type TargetLane,
  type TimeLabel,
  asRecord,
  buildStrip,
  clock,
  panned,
} from "./strip";
import { placeTip, tipKey, tipText } from "./tap";

declare const __CARD_VERSION__: string;

export const CARD_VERSION: string = __CARD_VERSION__;

const CARD_TYPE = "pierpressure-card";

const MINUTE = 60 * 1000;

interface CustomCardEntry {
  type: string;
  name: string;
  description?: string;
  preview?: boolean;
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
  config?: { time_zone?: string; latitude?: number };
}

export interface CardConfig {
  type: string;
  pier: string;
}

export class PierPressureCard extends LitElement {
  static override properties = {
    hass: { attribute: false },
    config: { state: true },
    heldStart: { state: true },
    tipKey: { state: true },
  };

  static override styles = [
    css`
    /* Holds the tap box, which is placed in px from the card's corner. */
    ha-card {
      position: relative;
    }
    /* Out of the flow, so showing it moves nothing, and above the lines. A tap
       goes through it to the item under it. The colours swap the card's, so it
       reads on a light or a dark theme. */
    .tip {
      position: absolute;
      z-index: 2;
      pointer-events: none;
      max-width: min(280px, calc(100% - 16px));
      box-sizing: border-box;
      padding: 4px 8px;
      border-radius: 4px;
      background-color: var(--primary-text-color);
      color: var(--card-background-color);
      font-size: 0.85em;
      white-space: normal;
      overflow-wrap: anywhere;
    }
    /* Not stretched: a stretched grid spreads the verdict lines to the Moon
       section's height. */
    .summary {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-start;
    }
    .moon {
      display: flex;
      align-items: center;
      gap: 12px;
    }
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
    .reasons {
      margin: 16px 0 0;
      padding-left: 20px;
      color: var(--secondary-text-color);
    }
    .note {
      margin: 16px 0 0;
      color: var(--secondary-text-color);
    }
    /* Always laid out, so the button showing moves nothing on the card. */
    .back {
      display: flex;
      justify-content: flex-end;
      margin-top: 16px;
    }
    .back button {
      min-height: 24px;
      padding: 0 8px;
      border: 1px solid var(--divider-color, #898781);
      border-radius: 4px;
      background: none;
      color: var(--primary-color);
      font: inherit;
      font-size: 0.85em;
      cursor: pointer;
    }
    .back button[hidden] {
      display: inline-block;
      visibility: hidden;
    }
    .back + .strip {
      margin-top: 4px;
    }
    .strip {
      position: relative;
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 2px 8px;
      margin-top: 16px;
      /* The browser keeps up and down swipes for scrolling the page, and a drag
         selects no label. */
      touch-action: pan-y;
      user-select: none;
      -webkit-user-select: none;
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
    /* A block sized to its text: the track has no line height of its own, and
       an inline box would sit low on Home Assistant's taller line and ignore
       the indent. Hovering covers only the text, and a narrow card cuts it off. */
    .missing {
      display: block;
      width: fit-content;
      max-width: 100%;
      box-sizing: border-box;
      padding-left: 4px;
      color: var(--secondary-text-color);
      font-size: 0.75em;
      line-height: 16px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
    /* Twice a shaded row, so a 15% step of cloud is about 5 px, with its label
       and message in the middle as in the other rows. */
    .row[data-row="cloud_range"] .track {
      height: 32px;
    }
    .row[data-row="cloud_range"] .label,
    .row[data-row="cloud_range"] .missing {
      line-height: 32px;
    }
    /* The hour's 0 to 100% column; its bar keeps to the rounded corners. Grey,
       not blue, since the row shows how far the forecasts agree, not good or bad.
       The bar keeps 1px in from each side, so the column frames it on a light
       or a dark card. */
    .column {
      background-color: #8c8c8c;
      overflow: hidden;
    }
    /* The column, not the bar, turns amber where the forecasts disagree: no
       amber bar keeps 3:1 against the grey column, but this column keeps 3:1
       against the grey bar and against a light or a dark card. */
    .column.disagree {
      background-color: #b58900;
    }
    .range {
      position: absolute;
      left: 1px;
      right: 1px;
      background-color: #404040;
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
      display: flex;
      background-color: #6250d6;
      color: #ffffff;
      font-size: 0.75em;
      line-height: 16px;
      text-indent: 4px;
      overflow: hidden;
      white-space: nowrap;
    }
    /* Only the name shortens: the id is what you type into a mount or a
       planetarium app. */
    .bar[data-target] .name {
      overflow: hidden;
      text-overflow: ellipsis;
    }
    /* Flex drops the space between two items, so the id keeps its own. */
    .bar[data-target] .id {
      flex-shrink: 0;
      white-space: pre;
      text-indent: 0;
    }
  `,
    chartStyles,
  ];

  // Home Assistant sets hass after setConfig and after the card is attached.
  declare hass?: HomeAssistant;
  declare config?: CardConfig;
  // Where the user panned the strip to; undefined keeps it on the opening axis.
  declare heldStart?: number;
  // The key of the item whose text the box shows; undefined shows no box.
  declare tipKey?: string;
  // Whether the pan was later than the opening axis. The opening axis follows the
  // clock through the night, so it can catch up with a later pan.
  private heldLater = false;
  private timer?: ReturnType<typeof setInterval>;
  private drag?: Drag;
  private press?: Press;
  private frame?: { strip: Strip | undefined; moon: MoonDrawing | undefined };

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
    this.clearPress();
  }

  static getConfigElement(): HTMLElement {
    return document.createElement(EDITOR_TYPE);
  }

  // The card picker draws its preview from this, so it starts on a real pier.
  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    const first = listPiers(hass.states)[0];
    return { type: `custom:${CARD_TYPE}`, ...(first !== undefined && { pier: first.value }) };
  }

  // Home Assistant shows a thrown error in place of the card.
  setConfig(config: Record<string, unknown>): void {
    const pier = config["pier"];
    if (typeof pier !== "string" || pierSlug(pier) === "") {
      throw new Error("pier is required");
    }
    // The same keys would name the other pier's items.
    if (pier !== this.config?.pier) {
      this.heldStart = undefined;
      this.tipKey = undefined;
    }
    this.config = { type: String(config["type"]), pier };
  }

  // Before each draw, so following the opening axis again costs no second one. A
  // minute's redraw a sleeping tab skipped still counts.
  // An item no longer on the card closes its box in the same draw. One snapshot
  // serves both the body and the box, so a clock tick mid-draw cannot split them.
  override willUpdate(): void {
    const now = Date.now();
    let strip = this.shownStrip(now);
    if (this.heldStart !== undefined && this.heldLater) {
      const opening = strip?.opening;
      if (opening !== undefined && opening.start >= this.heldStart) {
        this.heldStart = undefined;
        strip = this.shownStrip(now);
      }
    }
    const moon = this.shownMoon();
    if (this.tipKey !== undefined && tipText(strip, moon, this.tipKey) === undefined) {
      this.tipKey = undefined;
    }
    this.frame = { strip, moon };
  }

  // Before the browser paints, so the box never shows in the wrong place. The box
  // is measured at the card's left edge, where only its max-width limits it.
  override updated(): void {
    this.frame = undefined;
    if (this.tipKey === undefined) return;
    const box = this.renderRoot.querySelector<HTMLElement>(".tip");
    const card = this.renderRoot.querySelector("ha-card");
    const item = this.renderRoot.querySelector(`[data-tip="${this.tipKey}"]`);
    if (box === null || card === null || item === null) return;
    box.style.left = "0px";
    const place = placeTip(
      item.getBoundingClientRect(),
      card.getBoundingClientRect(),
      box.getBoundingClientRect(),
    );
    box.style.left = `${place.left}px`;
    box.style.top = `${place.top}px`;
  }

  // Three target lanes, or two reasons, are about one of Home Assistant's 50 px
  // size units.
  getCardSize(): number {
    const lanes = Math.ceil((this.shownStrip()?.targets.length ?? 0) / 3);
    return 10 + lanes + Math.ceil(this.shownReasons().length / 2);
  }

  // A sections view gives a card half its section's width by default, too
  // narrow for the strip's time labels.
  getGridOptions(): { columns: "full" } {
    return { columns: "full" };
  }

  override render() {
    if (this.config === undefined) return nothing;
    const strip = this.frame?.strip ?? this.shownStrip();
    const moon = this.frame?.moon ?? this.shownMoon();
    return html`<ha-card
      header=${`PierPressure ${this.config.pier}`}
      @pointerdown=${this.tap.pointerdown}
      @pointermove=${this.tap.pointermove}
      @pointerup=${this.tap.pointerup}
      @pointercancel=${this.tap.pointercancel}
      >${this.renderBody(strip)}${this.renderTip(strip, moon)}</ha-card
    >`;
  }

  // The item's aria-label already gives a screen reader the same text.
  private renderTip(strip: Strip | undefined, moon: MoonDrawing | undefined) {
    if (this.tipKey === undefined) return nothing;
    const text = tipText(strip, moon, this.tipKey);
    if (text === undefined) return nothing;
    return html`<div class="tip" aria-hidden="true">${text}</div>`;
  }

  private renderBody(strip: Strip | undefined) {
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
    const time = clock(this.hass.config?.time_zone);
    const moon = readMoon(entity.attributes["moon"], time, this.hass.config?.latitude);
    return html`<div class="card-content">
      <div class="summary">
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
        ${renderMoon(moon)}
      </div>
      ${renderReasons(this.shownReasons(), time)} ${renderNote(strip)}
      ${renderBack(strip, this.onBack)} ${renderStrip(strip, this.input)}
    </div>`;
  }

  // The strip draws only beside the verdict, never under a message.
  private shownStrip(now = Date.now()): Strip | undefined {
    if (this.hass === undefined || this.config === undefined) return undefined;
    const entity = this.hass.states[verdictEntityId(this.config.pier)];
    if (entity === undefined || entity.state === "unavailable") return undefined;
    return buildStrip(
      this.hass.states,
      this.config.pier,
      now,
      this.hass.config?.time_zone,
      this.heldStart,
    );
  }

  private shownMoon(): MoonDrawing | undefined {
    if (this.hass === undefined || this.config === undefined) return undefined;
    const entity = this.hass.states[verdictEntityId(this.config.pier)];
    if (entity === undefined || entity.state === "unavailable") return undefined;
    const time = clock(this.hass.config?.time_zone);
    return readMoon(entity.attributes["moon"], time, this.hass.config?.latitude).drawing;
  }

  // The reasons explain a verdict, so a dash in its place shows none, even
  // ones left over from an earlier verdict.
  private shownReasons(): string[] {
    if (this.hass === undefined || this.config === undefined) return [];
    const entity = this.hass.states[verdictEntityId(this.config.pier)];
    if (entity === undefined || ["unavailable", "unknown"].includes(entity.state)) return [];
    return readReasons(entity.attributes["reasons"]);
  }

  // A pan the reach stops entirely changes nothing, and one that lands on the
  // opening axis lets the strip follow it again, as Back to tonight does. Any
  // other pan closes the box, since its item may have moved away.
  private panTo(start: number): void {
    const strip = this.shownStrip();
    if (strip === undefined) return;
    const to = panned(strip.opening, strip.reach, start).start;
    if (to === strip.axis.start) return;
    this.tipKey = undefined;
    this.heldStart = to === strip.opening.start ? undefined : to;
    this.heldLater = to > strip.opening.start;
  }

  // The button hides itself, so focus moves to the strip it returned.
  private onBack = (): void => {
    this.heldStart = undefined;
    this.tipKey = undefined;
    this.renderRoot.querySelector<HTMLElement>(".strip")?.focus();
  };

  private input: StripInput = {
    keydown: (event) => {
      const by = PAN_KEYS[event.key];
      if (by === undefined) return;
      event.preventDefault();
      const strip = this.shownStrip();
      if (strip !== undefined) this.panTo(strip.axis.start + by);
    },
    // The width is taken once, so a layout change mid-drag cannot change the scale.
    pointerdown: (event) => {
      if (this.drag !== undefined || !event.isPrimary || event.button !== 0) return;
      const strip = this.shownStrip();
      if (strip === undefined) return;
      const width = this.renderRoot.querySelector(".times")?.getBoundingClientRect().width ?? 0;
      this.drag = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        start: strip.axis.start,
        length: strip.axis.end - strip.axis.start,
        width,
        held: this.heldStart,
        heldLater: this.heldLater,
        panning: false,
      };
      // A mouse or pen has no capture of its own, so without this a drag that
      // leaves the strip before it starts to pan would lose its moves. The Back
      // to tonight button is outside the strip, so no click there is retargeted.
      (event.currentTarget as Element).setPointerCapture(event.pointerId);
    },
    // A drag pans only once it is clearly sideways, so a tap that slips or the
    // start of a vertical swipe moves nothing.
    pointermove: (event) => {
      const drag = this.drag;
      if (drag === undefined || event.pointerId !== drag.pointerId || drag.width <= 0) return;
      const sideways = event.clientX - drag.x;
      if (!drag.panning) {
        if (Math.abs(sideways) <= DRAG_SLOP) return;
        if (Math.abs(sideways) <= Math.abs(event.clientY - drag.y)) return;
        drag.panning = true;
      }
      this.panTo(drag.start - (sideways / drag.width) * drag.length);
    },
    pointerup: (event) => this.endDrag(event),
    // The browser took the gesture, to scroll the page, so the moves it let
    // through before that are undone.
    pointercancel: (event) => {
      const drag = this.endDrag(event);
      if (drag === undefined) return;
      this.heldStart = drag.held;
      this.heldLater = drag.heldLater;
    },
    // Only the strip's own loss ends the drag. A touch pointer starts captured by
    // the element under the finger, which loses it when the strip captures it.
    lostpointercapture: (event) => {
      if (event.target === event.currentTarget) this.endDrag(event);
    },
    // Not passive, so a sideways swipe can be kept from the browser, which would
    // otherwise take it for going back a page. An up or down one scrolls the page.
    wheel: {
      passive: false,
      handleEvent: (event: WheelEvent) => {
        if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return;
        event.preventDefault();
        const strip = this.shownStrip();
        const width = this.renderRoot.querySelector(".times")?.getBoundingClientRect().width ?? 0;
        if (strip === undefined || width <= 0) return;
        const pixels = event.deltaX * (WHEEL_UNIT[event.deltaMode] ?? width);
        const length = strip.axis.end - strip.axis.start;
        this.panTo(strip.axis.start + (pixels / width) * length);
      },
    },
  };

  // Apart from the strip's drag, so a tap anywhere on the card is seen. The key is
  // taken when the pointer is pressed: the strip's capture retargets the release.
  // Moves, releases and cancels also listen on window, since presses outside the
  // strip are not captured and may end off the card.
  private tap: TapInput = {
    pointerdown: (event) => {
      if (!event.isPrimary || event.button !== 0) return;
      if (
        this.press !== undefined &&
        event.pointerId !== this.press.pointerId &&
        this.press.target.isConnected
      ) {
        return;
      }
      this.clearPress();
      const target = event.target as Element;
      const item = target.closest("[data-tip]");
      this.press = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        key: item?.getAttribute("data-tip") ?? undefined,
        target,
        moved: false,
      };
      window.addEventListener("pointermove", this.tap.pointermove);
      window.addEventListener("pointerup", this.tap.pointerup);
      window.addEventListener("pointercancel", this.tap.pointercancel);
    },
    // Every drag that pans has moved this far, so none of them is a tap.
    pointermove: (event) => {
      const press = this.press;
      if (press === undefined || event.pointerId !== press.pointerId) return;
      const far = Math.max(Math.abs(event.clientX - press.x), Math.abs(event.clientY - press.y));
      if (far > DRAG_SLOP) press.moved = true;
    },
    // A tap on the item the box shows closes it, and a tap off every item too.
    pointerup: (event) => {
      const press = this.press;
      if (press === undefined || event.pointerId !== press.pointerId) return;
      this.clearPress();
      if (press.moved || !event.composedPath().includes(this)) return;
      this.tipKey = press.key === this.tipKey ? undefined : press.key;
    },
    // The browser took the gesture, to scroll the page.
    pointercancel: (event) => {
      if (event.pointerId === this.press?.pointerId) this.clearPress();
    },
  };

  private clearPress(): void {
    this.press = undefined;
    window.removeEventListener("pointermove", this.tap.pointermove);
    window.removeEventListener("pointerup", this.tap.pointerup);
    window.removeEventListener("pointercancel", this.tap.pointercancel);
  }

  private endDrag(event: PointerEvent): Drag | undefined {
    const drag = this.drag;
    if (drag === undefined || event.pointerId !== drag.pointerId) return undefined;
    this.drag = undefined;
    return drag;
  }
}

// One pointer's drag across the strip, from where it was pressed.
interface Drag {
  pointerId: number;
  x: number;
  y: number;
  // The axis on screen when the pointer was pressed, and the hours' width then.
  start: number;
  length: number;
  width: number;
  // What a cancelled drag puts back.
  held: number | undefined;
  heldLater: boolean;
  panning: boolean;
}

// One pointer's press on the card, which is a tap if it stays in place.
interface Press {
  pointerId: number;
  x: number;
  y: number;
  // The pressed item's `data-tip`, if any.
  key: string | undefined;
  target: Element;
  moved: boolean;
}

interface TapInput {
  pointerdown: (event: PointerEvent) => void;
  pointermove: (event: PointerEvent) => void;
  pointerup: (event: PointerEvent) => void;
  pointercancel: (event: PointerEvent) => void;
}

interface StripInput {
  keydown: (event: KeyboardEvent) => void;
  pointerdown: (event: PointerEvent) => void;
  pointermove: (event: PointerEvent) => void;
  pointerup: (event: PointerEvent) => void;
  pointercancel: (event: PointerEvent) => void;
  lostpointercapture: (event: PointerEvent) => void;
  wheel: { passive: false; handleEvent: (event: WheelEvent) => void };
}

// Pixels per wheel unit: deltaMode 0 is pixels and 1 is lines; 2, a page, is the
// width the hours are drawn across.
const WHEEL_UNIT: Record<number, number | undefined> = { 0: 1, 1: 16 };

// How far, in px, a pointer moves sideways before a drag starts to pan.
const DRAG_SLOP = 8;

const PAN_KEYS: Record<string, number | undefined> = { ArrowLeft: -HOUR, ArrowRight: HOUR };

const DASH = "—";

const LIT = "#ece8dc";

function renderMoon(moon: MoonView) {
  return html`<section class="moon" aria-label="Moon">
    ${moon.drawing === undefined ? nothing : renderDrawing(moon.drawing)}
    <dl>
      <dt>Phase</dt>
      <dd data-field="moon-phase">${moon.phase}</dd>
      <dt>Illumination</dt>
      <dd data-field="moon-illumination">${moon.illumination}</dd>
      <dt>Moonrise</dt>
      <dd data-field="moon-rise">${moon.rise}</dd>
      <dt>Moonset</dt>
      <dd data-field="moon-set">${moon.set}</dd>
    </dl>
  </section>`;
}

// The unlit disc, the lit part, then the outline on top, so the lit part never
// covers the edge. The lit part is a fragment inside the <svg>, so it needs Lit's
// svg tag: an html fragment there would make unknown HTML elements a browser does
// not paint.
function renderDrawing(drawing: MoonDrawing) {
  return html`<svg
    viewBox="-1.1 -1.1 2.2 2.2"
    width="48"
    height="48"
    data-lit=${drawing.lit}
    data-mirrored=${drawing.mirrored}
    role="img"
    data-tip=${tipKey.moon}
    aria-label=${drawing.text}
  >
    <title>${drawing.text}</title>
    <circle r="1" fill="#3b3a36"></circle>
    ${renderLit(drawing)}
    <circle r="1" fill="none" stroke="#898781" stroke-width="0.08"></circle>
  </svg>`;
}

function renderLit({ lit, mirrored }: MoonDrawing) {
  if (lit === "none") return nothing;
  if (lit === "all") return svg`<circle r="1" fill=${LIT}></circle>`;
  const path = svg`<path d=${litPath(lit)} fill=${LIT}></path>`;
  return mirrored ? svg`<g transform="scale(-1 1)">${path}</g>` : path;
}

// A list with anything but strings in it is not one the core wrote, so none of
// it is shown.
function readReasons(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.every((reason) => typeof reason === "string") ? value : [];
}

function renderReasons(reasons: string[], time: (time: number) => string) {
  if (reasons.length === 0) return nothing;
  return html`<ul class="reasons" aria-label="Reasons">
    ${reasons.map((reason) => html`<li>${localTimes(reason, time)}</li>`)}
  </ul>`;
}

// The core writes times as UTC, as iso_z does. The scored span lies inside one
// night, so hours and minutes are enough, as on the strip.
const UTC_TIME = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z/g;

// The clock throws on a time Date cannot read, so such a time is left as written.
function localTimes(reason: string, time: (time: number) => string): string {
  return reason.replace(UTC_TIME, (text) => {
    const at = Date.parse(text);
    return Number.isFinite(at) ? time(at) : text;
  });
}

function renderNote(strip: Strip | undefined) {
  if (strip?.noDarkness !== true) return nothing;
  return html`<p class="note" data-note="no-darkness">No astronomical darkness tonight</p>`;
}

function renderBack(strip: Strip | undefined, onBack: () => void) {
  if (strip === undefined) return nothing;
  return html`<div class="back">
    <button type="button" ?hidden=${strip.axis.start === strip.opening.start} @click=${onBack}>
      Back to tonight
    </button>
  </div>`;
}

function renderStrip(strip: Strip | undefined, input: StripInput) {
  if (strip === undefined) return nothing;
  // Grid row 1 holds the line labels, then come the rows, the Moon up lane, the
  // target lanes, the Temperature chart and the time labels. The lines' overlay
  // spans from the first row to the bottom of the Temperature chart.
  const gridRows = strip.rows.length + strip.targets.length + 4;
  const laneEnd = strip.rows.length + strip.targets.length + 4;
  return html`<div
    class="strip"
    style=${`grid-template-rows: repeat(${gridRows}, auto)`}
    data-axis-start=${iso(strip.axis.start)}
    data-axis-end=${iso(strip.axis.end)}
    tabindex="0"
    role="group"
    aria-label="Night strip. Use the Left and Right arrow keys to move through the forecast."
    @keydown=${input.keydown}
    @pointerdown=${input.pointerdown}
    @pointermove=${input.pointermove}
    @pointerup=${input.pointerup}
    @pointercancel=${input.pointercancel}
    @lostpointercapture=${input.lostpointercapture}
    @wheel=${input.wheel}
  >
    <span></span>
    <div class="track marks">${strip.lines.map((line) => renderMark(line, strip.axis))}</div>
    ${strip.rows.map(
      (row) =>
        html`<div class="row" data-row=${row.key}>
          <span class="label">${row.label}</span>
          <div class="track">
            ${row.cells.map((cell) => renderCell(cell, row.key, strip.axis))}
            ${(row.bands ?? []).map((band) => renderBand(band, strip.axis))}
            ${row.missing === undefined ? nothing : renderMissing(row.missing, tipKey.missing(row.key))}
          </div>
        </div>`,
    )}
    <div class="row" data-lane="moon_up">
      <span class="label">Moon up</span>
      <div class="track">
        ${strip.moonUp.map((bar) => renderBar(bar, tipKey.moonUp(bar.start), strip.axis))}
        ${
          strip.moonUpMissing === undefined
            ? nothing
            : renderMissing(strip.moonUpMissing, tipKey.missing("moon_up"))
        }
      </div>
    </div>
    ${strip.targets.map(
      (lane) =>
        html`<div class="row" data-lane=${`target_${lane.rank}`}>
          <span class="label">${lane.label}</span>
          <div class="track">
            ${
              lane.bar === undefined
                ? nothing
                : renderBar(lane.bar, tipKey.target(lane.rank), strip.axis, lane)
            }
          </div>
        </div>`,
    )}
    ${renderChart(strip.chart, strip.axis)}
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
    data-tip=${tipKey.line(line)}
    title=${line.text}
    aria-label=${line.text}
  ></div>`;
}

function renderTimeLabel(label: TimeLabel, axis: Axis) {
  const style = `left: ${offset(label.at, axis)}%`;
  return html`<span class="time" style=${style} data-at=${iso(label.at)}>${label.text}</span>`;
}

function renderCell(cell: Cell, row: string, axis: Axis) {
  const place = hourPlace(cell, axis);
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
    data-tip=${tipKey.cell(row, cell.hour)}
    title=${cell.text}
    aria-label=${cell.text}
  >
    ${cell.arrow === undefined ? nothing : renderArrow(cell.arrow)}
  </div>`;
}

// Two forecasts that agree still show, as a 2 px line, and one at 100% is
// pulled down to stay inside the column.
function renderBand(band: Band, axis: Axis) {
  const range =
    `bottom: min(${band.low}%, calc(100% - 2px)); ` + `height: max(2px, ${band.high - band.low}%)`;
  return html`<div
    class=${band.disagree ? "cell column disagree" : "cell column"}
    style=${hourPlace(band, axis)}
    data-hour=${iso(band.hour)}
    data-from=${iso(band.from)}
    data-to=${iso(band.to)}
    data-low=${band.low}
    data-high=${band.high}
    data-tip=${tipKey.column(band.hour)}
    title=${band.text}
    aria-label=${band.text}
  >
    <div class="range" style=${range}></div>
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

// A target's bar carries its name and id; a Moon up bar has neither.
function renderBar(bar: Bar, key: string, axis: Axis, target?: TargetLane) {
  const style = `left: ${offset(bar.from, axis)}%; width: ${share(bar.to - bar.from, axis)}%`;
  return html`<div
    class="bar"
    style=${style}
    ?data-target=${target !== undefined}
    data-start=${iso(bar.start)}
    data-end=${iso(bar.end)}
    data-from=${iso(bar.from)}
    data-to=${iso(bar.to)}
    data-tip=${key}
    title=${bar.text}
    aria-label=${bar.text}
  >
    ${target === undefined ? nothing : renderTargetName(target)}
  </div>`;
}

function renderTargetName(target: TargetLane) {
  const id = target.id === undefined ? nothing : html`<span class="id"> (${target.id})</span>`;
  return html`<span class="name">${target.name}</span>${id}`;
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
    preview: true,
  });
}
console.info(`PIERPRESSURE-CARD ${CARD_VERSION}`);
