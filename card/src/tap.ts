// What a tap on the card shows: the tapped item's hover text in a box.
import type { MoonDrawing } from "./moon";
import { iso } from "./place";
import type { Line, Strip } from "./strip";

// The `data-tip` key of each item a tap can open. A key names the item's place
// in the strip, so the same item keeps its key when the card redraws.
export const tipKey = {
  cell: (row: string, hour: number) => `cell:${row}:${iso(hour)}`,
  column: (hour: number) => `column:${iso(hour)}`,
  hour: (hour: number) => `hour:${iso(hour)}`,
  moonUp: (start: number) => `moon-up:${iso(start)}`,
  target: (rank: number) => `target:${rank}`,
  // Two nights' dusk lines can share the axis, so a dusk or dawn line names its night.
  line: ({ kind, night }: Line) => (night === undefined ? `line:${kind}` : `line:${kind}:${night}`),
  // A row's key, `moon_up`, or `chart:` and a chart line's key.
  missing: (place: string) => `missing:${place}`,
  moon: "moon",
};

// The latest text of the item a key names, or none when the card no longer
// draws that item.
export function tipText(
  strip: Strip | undefined,
  moon: MoonDrawing | undefined,
  key: string,
): string | undefined {
  return tipTexts(strip, moon).get(key);
}

function tipTexts(strip: Strip | undefined, moon: MoonDrawing | undefined): Map<string, string> {
  const texts = new Map<string, string>();
  if (moon !== undefined) texts.set(tipKey.moon, moon.text);
  if (strip === undefined) return texts;
  for (const row of strip.rows) {
    for (const cell of row.cells) texts.set(tipKey.cell(row.key, cell.hour), cell.text);
    for (const band of row.bands ?? []) texts.set(tipKey.column(band.hour), band.text);
    if (row.missing !== undefined) texts.set(tipKey.missing(row.key), row.missing.text);
  }
  for (const bar of strip.moonUp) texts.set(tipKey.moonUp(bar.start), bar.text);
  if (strip.moonUpMissing !== undefined) {
    texts.set(tipKey.missing("moon_up"), strip.moonUpMissing.text);
  }
  for (const lane of strip.targets) {
    for (const bar of lane.bars) {
      if (bar.night === 1) texts.set(tipKey.target(lane.rank), bar.text);
    }
  }
  for (const line of strip.lines) texts.set(tipKey.line(line), line.text);
  for (const hour of strip.chart.hours) texts.set(tipKey.hour(hour.hour), hour.text);
  for (const line of strip.chart.lines) {
    if (line.missing !== undefined)
      texts.set(tipKey.missing(`chart:${line.key}`), line.missing.text);
  }
  return texts;
}

export interface Size {
  width: number;
  height: number;
}

export interface Rect extends Size {
  left: number;
  top: number;
}

// How far, in px, the box keeps from the card's edges, and from its item.
const EDGE = 8;
const GAP = 4;

// In px from the card's top left corner. The box centres on the part of the item
// inside the card, so a bar the axis cuts off centres on what shows.
export function placeTip(item: Rect, card: Rect, box: Size): { left: number; top: number } {
  const from = Math.max(item.left, card.left);
  const to = Math.min(item.left + item.width, card.left + card.width);
  const centre = (from + to) / 2 - card.left;
  const left = Math.max(EDGE, Math.min(centre - box.width / 2, card.width - EDGE - box.width));
  const above = item.top - card.top - GAP - box.height;
  const top = above < EDGE ? item.top - card.top + item.height + GAP : above;
  return { left, top };
}
