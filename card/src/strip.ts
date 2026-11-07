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

export interface Night {
  dusk: number;
  dawn: number;
}

export function darkWindow(attribute: unknown): Night | undefined {
  const window = asRecord(attribute);
  const dusk = readTime(window?.["start"]);
  const dawn = readTime(window?.["end"]);
  if (dusk === undefined || dawn === undefined || dawn <= dusk) return undefined;
  if (dawn - dusk > LONGEST_WINDOW) return undefined;
  return { dusk, dawn };
}

export function stripAxis(night: Night | undefined, now: number): Axis {
  if (night !== undefined) return { start: night.dusk - BEFORE_DUSK, end: night.dawn + AFTER_DAWN };
  return { start: now - FALLBACK_BEFORE, end: now + FALLBACK_AFTER };
}

function readTime(value: unknown): number | undefined {
  if (typeof value !== "string") return undefined;
  const time = Date.parse(value);
  return Number.isNaN(time) ? undefined : time;
}

export function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : undefined;
}

interface RowKind {
  key: string;
  label: string;
  unit: string;
  shade: (value: number) => string;
}

// Top to bottom, as in the YAML night strip.
export const ROWS: readonly RowKind[] = [
  { key: "sun_altitude", label: "Sun altitude", unit: "°", shade: sunShade },
  { key: "cloud_cover", label: "Cloud cover", unit: "%", shade: cloudShade },
  { key: "cloud_low", label: "Cloud low", unit: "%", shade: cloudShade },
  { key: "cloud_mid", label: "Cloud mid", unit: "%", shade: cloudShade },
  { key: "cloud_high", label: "Cloud high", unit: "%", shade: cloudShade },
];

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

export interface Bar {
  // The run's own hours, from the start of its first to the end of its last.
  start: number;
  end: number;
  // The part of the run on the axis.
  from: number;
  to: number;
  // What hovering over the bar shows.
  text: string;
}

export interface Line {
  kind: "dusk" | "dawn" | "now";
  at: number;
  // What hovering over the line shows.
  text: string;
}

export interface TimeLabel {
  at: number;
  text: string;
}

export interface Strip {
  axis: Axis;
  rows: Row[];
  moonUp: Bar[];
  lines: Line[];
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
  const night = darkWindow(verdict?.attributes["dark_window"]);
  const axis = stripAxis(night, now);
  const time = clock(timeZone);
  return {
    axis,
    labels: timeLabels(axis, time),
    rows: ROWS.map(({ key, label, unit, shade }) => ({
      key,
      label,
      cells: rowCells(forecastOf(states[pierEntityId(pier, key)]), axis, shade).map((cell) => ({
        ...cell,
        text: `${label}, the hour from ${time(cell.hour)}: ${cell.value}${unit}`,
      })),
    })),
    moonUp: moonUpBars(forecastOf(states[pierEntityId(pier, "moon_altitude")]), axis, time),
    lines: [...(night === undefined ? [] : nightLines(night, time)), ...nowLine(now, axis, time)],
  };
}

function nightLines(night: Night, time: (at: number) => string): Line[] {
  return [
    { kind: "dusk", at: night.dusk, text: `Dusk, ${time(night.dusk)}` },
    { kind: "dawn", at: night.dawn, text: `Dawn, ${time(night.dawn)}` },
  ];
}

function nowLine(now: number, axis: Axis, time: (at: number) => string): Line[] {
  if (now < axis.start || now > axis.end) return [];
  return [{ kind: "now", at: now, text: `Now, ${time(now)}` }];
}

// Home Assistant normally drops an unavailable entity's attributes; when it has
// not, they are stale, as they are for the Verdict sensor.
function forecastOf(entity: States[string]): unknown {
  if (entity === undefined || entity.state === "unavailable") return undefined;
  return entity.attributes["forecast"];
}

function rowCells(
  forecast: unknown,
  axis: Axis,
  shade: (value: number) => string,
): Omit<Cell, "text">[] {
  if (!Array.isArray(forecast)) return [];
  return forecast.flatMap((point: unknown) => {
    const record = asRecord(point);
    const hour = readTime(record?.["datetime"]);
    const value = record?.["value"];
    if (hour === undefined || hour + HOUR <= axis.start || hour >= axis.end) return [];
    // A type check, not a truthiness check: 0% cloud or 0° is a value, null is a gap.
    if (typeof value !== "number" || !Number.isFinite(value)) return [];
    return [
      {
        hour,
        from: Math.max(hour, axis.start),
        to: Math.min(hour + HOUR, axis.end),
        value,
        shade: shade(value),
      },
    ];
  });
}

function moonUpBars(forecast: unknown, axis: Axis, time: (at: number) => string): Bar[] {
  const altitudes = hourlyValues(forecast);
  const runs: Array<{ start: number; end: number }> = [];
  for (const [hour, value] of altitudes) {
    if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) continue;
    const last = runs.at(-1);
    if (last?.end === hour) last.end = hour + HOUR;
    else runs.push({ start: hour, end: hour + HOUR });
  }
  return runs
    .filter((run) => run.end > axis.start && run.start < axis.end)
    .map((run) => ({
      ...run,
      from: Math.max(run.start, axis.start),
      to: Math.min(run.end, axis.end),
      text: moonUpText(run, altitudes, time),
    }));
}

// A run at either end of the forecast may have begun before it or go on after
// it, so the text names a rise or set only where the forecast shows the moon down.
function moonUpText(
  run: { start: number; end: number },
  altitudes: Map<number, unknown>,
  time: (at: number) => string,
): string {
  // HH:MM cannot tell one day from the next.
  if (run.end - run.start >= 24 * HOUR) return "Moon up";
  const down = (hour: number) => {
    const value = altitudes.get(hour);
    return typeof value === "number" && Number.isFinite(value) && value <= 0;
  };
  const rise = down(run.start - HOUR);
  const set = down(run.end);
  if (rise && set) return `Moon up from ${time(run.start)} to ${time(run.end)}`;
  if (rise) return `Moon up from ${time(run.start)}`;
  if (set) return `Moon up until ${time(run.end)}`;
  return "Moon up";
}

// Hour by hour in time order, so a run never depends on the forecast's order.
function hourlyValues(forecast: unknown): Map<number, unknown> {
  if (!Array.isArray(forecast)) return new Map();
  const values = new Map<number, unknown>();
  for (const point of forecast) {
    const record = asRecord(point);
    const hour = readTime(record?.["datetime"]);
    if (hour !== undefined) values.set(hour, record?.["value"]);
  }
  return new Map([...values].sort(([a], [b]) => a - b));
}

// The YAML strip's seven blues, lightest to darkest, one step per 15% of cloud.
const BLUES = [
  "#cde2fb",
  "#9ec5f4",
  "#6da7ec",
  "#3987e5",
  "#256abf",
  "#184f95",
  "#0d366b",
] as const;

function cloudShade(percent: number): string {
  const step = Math.min(BLUES.length - 1, Math.max(0, Math.floor(percent / 15)));
  return BLUES[step] ?? BLUES[0];
}

// The YAML strip's twilight band: sun up, civil, nautical and astronomical
// twilight, then the darkest blue for astronomical night from −18°.
function sunShade(degrees: number): string {
  const step = degrees > 0 ? 0 : degrees > -6 ? 1 : degrees > -12 ? 2 : degrees > -18 ? 3 : 6;
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
