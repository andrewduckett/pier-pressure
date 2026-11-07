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
  value: number;
  shade: string;
  // What hovering over the cell shows.
  text: string;
}

export interface Row {
  key: string;
  label: string;
  cells: Cell[];
}

export interface TimeLabel {
  at: number;
  text: string;
}

export interface Strip {
  axis: Axis;
  rows: Row[];
  labels: TimeLabel[];
}

type States = Record<string, { state: string; attributes: Record<string, unknown> } | undefined>;

export function buildStrip(
  states: States,
  pier: string,
  now: number,
  timeZone: string | undefined,
): Strip {
  const verdict = states[pierEntityId(pier, "verdict")];
  const axis = stripAxis(verdict?.attributes["dark_window"], now);
  const time = clock(timeZone);
  return {
    axis,
    labels: timeLabels(axis, time),
    rows: CLOUD_ROWS.map(({ key, label }) => ({
      key,
      label,
      cells: rowCells(forecastOf(states[pierEntityId(pier, key)]), axis).map((cell) => ({
        ...cell,
        text: `${label}, the hour from ${time(cell.hour)}: ${cell.value}%`,
      })),
    })),
  };
}

// Home Assistant normally drops an unavailable entity's attributes; when it has
// not, they are stale, as they are for the Verdict sensor.
function forecastOf(entity: States[string]): unknown {
  if (entity === undefined || entity.state === "unavailable") return undefined;
  return entity.attributes["forecast"];
}

function rowCells(forecast: unknown, axis: Axis): Omit<Cell, "text">[] {
  if (!Array.isArray(forecast)) return [];
  return forecast.flatMap((point: unknown) => {
    const record = asRecord(point);
    const hour = readTime(record?.["datetime"]);
    const value = record?.["value"];
    if (hour === undefined || hour + HOUR <= axis.start || hour >= axis.end) return [];
    // A type check, not a truthiness check: 0% cloud is a value, null is a gap.
    if (typeof value !== "number" || !Number.isFinite(value)) return [];
    return [
      {
        hour,
        from: Math.max(hour, axis.start),
        to: Math.min(hour + HOUR, axis.end),
        value,
        shade: cloudShade(value),
      },
    ];
  });
}

// The YAML strip's seven blues, lightest to darkest, one step per 15% of cloud.
const BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"] as const;

function cloudShade(percent: number): string {
  const step = Math.min(BLUES.length - 1, Math.max(0, Math.floor(percent / 15)));
  return BLUES[step] ?? BLUES[0];
}

const QUARTER = 15 * 60 * 1000;

// Stepping by quarter hours finds local whole hours in every time zone in use,
// including +05:30 and +05:45 and across a clock change, with no offset arithmetic.
function timeLabels(axis: Axis, time: (at: number) => string): TimeLabel[] {
  const every = axis.end - axis.start > 24 * HOUR ? 6 : 3;
  const labels: TimeLabel[] = [];
  const first = Math.floor(axis.start / QUARTER) * QUARTER + QUARTER;
  for (let at = first; at < axis.end; at += QUARTER) {
    const text = time(at);
    const [hour, minute] = text.split(":").map(Number);
    if (minute !== 0 || hour === undefined || hour % every !== 0) continue;
    // When clocks go back, the same hour comes round twice; a polar night's two
    // noons a day apart are both real.
    const previous = labels.at(-1);
    if (previous?.text === text && at - previous.at < 3 * HOUR) continue;
    labels.push({ at, text });
  }
  return labels;
}

// Every viewer reads the same `HH:MM`: a pinned locale and Latin digits, so a
// browser in Arabic or Bengali still matches the time labels' filter.
export function clock(timeZone: string | undefined): (time: number) => string {
  const format = timeFormat(timeZone);
  return (time) => {
    const parts = format.formatToParts(time);
    const part = (type: Intl.DateTimeFormatPartTypes) =>
      parts.find((p) => p.type === type)?.value ?? "";
    return `${part("hour")}:${part("minute")}`;
  };
}

function timeFormat(timeZone: string | undefined): Intl.DateTimeFormat {
  const options: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    numberingSystem: "latn",
  };
  try {
    return new Intl.DateTimeFormat("en-GB", { ...options, timeZone });
  } catch (error) {
    // An unknown time zone falls back to the browser's rather than breaking the card.
    if (error instanceof RangeError) return new Intl.DateTimeFormat("en-GB", options);
    throw error;
  }
}
