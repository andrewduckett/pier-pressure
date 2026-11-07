import { pierEntityId } from "./entity";

export const HOUR = 60 * 60 * 1000;

// The YAML night strip's span (docs/night-dashboard.md): the judged night with
// its evening and morning around it, or a day around now when there is no night.
const BEFORE_DUSK = 4 * HOUR;
const AFTER_DAWN = 5 * HOUR;
const FALLBACK_BEFORE = 6 * HOUR;
const FALLBACK_AFTER = 18 * HOUR;
// The core never sends a longer window; a hand-edited state could.
const LONGEST_WINDOW = 48 * HOUR;

export interface Axis {
  start: number;
  end: number;
}

export function stripAxis(darkWindow: unknown, now: number): Axis {
  const window = asRecord(darkWindow);
  const dusk = readTime(window?.["start"]);
  const dawn = readTime(window?.["end"]);
  if (dusk !== undefined && dawn !== undefined && dawn > dusk && dawn - dusk <= LONGEST_WINDOW) {
    return { start: dusk - BEFORE_DUSK, end: dawn + AFTER_DAWN };
  }
  return { start: now - FALLBACK_BEFORE, end: now + FALLBACK_AFTER };
}

function readTime(value: unknown): number | undefined {
  if (typeof value !== "string") return undefined;
  const time = Date.parse(value);
  return Number.isNaN(time) ? undefined : time;
}

export function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : undefined;
}

// Top to bottom, as in the YAML night strip.
export const CLOUD_ROWS = [
  { key: "cloud_cover", label: "Cloud cover" },
  { key: "cloud_low", label: "Cloud low" },
  { key: "cloud_mid", label: "Cloud mid" },
  { key: "cloud_high", label: "Cloud high" },
] as const;

export interface Cell {
  hour: number;
  // The part of the hour on the axis: the hour itself, unless an axis end cuts it.
  from: number;
  to: number;
}

export interface Row {
  key: string;
  label: string;
  cells: Cell[];
}

export interface Strip {
  axis: Axis;
  rows: Row[];
}

type States = Record<string, { state: string; attributes: Record<string, unknown> } | undefined>;

export function buildStrip(states: States, pier: string, now: number): Strip {
  const verdict = states[pierEntityId(pier, "verdict")];
  const axis = stripAxis(verdict?.attributes["dark_window"], now);
  return {
    axis,
    rows: CLOUD_ROWS.map(({ key, label }) => ({
      key,
      label,
      cells: rowCells(states[pierEntityId(pier, key)]?.attributes["forecast"], axis),
    })),
  };
}

function rowCells(forecast: unknown, axis: Axis): Cell[] {
  if (!Array.isArray(forecast)) return [];
  return forecast.flatMap((point: unknown) => {
    const hour = readTime(asRecord(point)?.["datetime"]);
    if (hour === undefined || hour + HOUR <= axis.start || hour >= axis.end) return [];
    return [{ hour, from: Math.max(hour, axis.start), to: Math.min(hour + HOUR, axis.end) }];
  });
}
