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

// Once the night has started, the axis keeps its length and slides with the
// clock, so it never opens on hours long gone and a pan's length never shrinks.
export function stripAxis(night: Night | undefined, now: number): Axis {
  if (night === undefined) return { start: now - FALLBACK_BEFORE, end: now + FALLBACK_AFTER };
  const length = night.dawn + AFTER_DAWN - (night.dusk - BEFORE_DUSK);
  const start = Math.max(night.dusk, now) - BEFORE_DUSK;
  return { start, end: start + length };
}

// The opening axis's length, moved to `start` and held inside the reach.
export function panned(opening: Axis, reach: Axis, start: number): Axis {
  const length = opening.end - opening.start;
  const from = Math.min(Math.max(start, reach.start), reach.end - length);
  return { start: from, end: from + length };
}

// How far the axis can pan: every timeline hour a row's sensor holds, and never
// less than the opening axis. PierPressure publishes every timeline hour in every
// sensor, null where it has no value, so a null still marks a timeline hour. A
// Rain chance point is the exception: it fills the hour before its time, so it
// counts that hour, and only when there is a value to fill it with.
export function stripReach(states: States, pier: string, opening: Axis): Axis {
  const reach = { ...opening };
  const keys = [...ROWS.map((row) => row.key), "cloud_cover_min", "cloud_cover_max"];
  for (const key of keys) {
    const forecast = forecastOf(states[pierEntityId(pier, key)]);
    if (!Array.isArray(forecast)) continue;
    const hourBefore = ROWS.find((row) => row.key === key)?.hourBefore === true;
    for (const point of forecast) {
      const record = asRecord(point);
      const time = readTime(record?.["datetime"]);
      if (time === undefined) continue;
      if (hourBefore && !isNumber(record?.["value"])) continue;
      const hour = hourBefore ? time - HOUR : time;
      reach.start = Math.min(reach.start, hour);
      reach.end = Math.max(reach.end, hour + HOUR);
    }
  }
  return reach;
}

export function readTime(value: unknown): number | undefined {
  if (typeof value !== "string") return undefined;
  const time = Date.parse(value);
  return Number.isNaN(time) ? undefined : time;
}

export function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : undefined;
}

// A row draws each hour as a shade, or, for a direction, as an arrow.
type Mark =
  | { shade: (value: number) => string; arrow?: never }
  | { arrow: (value: number) => number; shade?: never };

type RowKind = Mark & {
  key: string;
  label: string;
  unit: string;
  // The value is for the hour that ends at its datetime, not the one that starts there.
  hourBefore?: true;
  // How hovering writes the value, when the unit alone is not enough.
  reading?: (value: number) => string;
};

// Top to bottom: the YAML night strip's nine, then the rest in the order
// PierPressure publishes them.
export const ROWS: readonly RowKind[] = [
  { key: "sun_altitude", label: "Sun altitude", unit: "°", shade: sunShade },
  { key: "moon_altitude", label: "Moon altitude", unit: "°", shade: moonShade },
  { key: "cloud_cover", label: "Cloud cover", unit: "%", shade: percentShade },
  { key: "cloud_low", label: "Cloud low", unit: "%", shade: percentShade },
  { key: "cloud_mid", label: "Cloud mid", unit: "%", shade: percentShade },
  { key: "cloud_high", label: "Cloud high", unit: "%", shade: percentShade },
  { key: "wind_gust", label: "Wind gust", unit: " km/h", shade: windShade },
  { key: "seeing", label: "Seeing", unit: "", shade: qualityShade },
  { key: "transparency", label: "Transparency", unit: "", shade: qualityShade },
  { key: "temperature", label: "Temperature", unit: " °C", shade: temperatureShade },
  { key: "dew_point", label: "Dew point", unit: " °C", shade: temperatureShade },
  { key: "humidity", label: "Humidity", unit: "%", shade: percentShade },
  { key: "wind_speed", label: "Wind speed", unit: " km/h", shade: windShade },
  {
    key: "wind_direction",
    label: "Wind direction",
    unit: "°",
    arrow: windArrow,
    reading: (degrees) => `${degrees}° from ${compassPoint(degrees)}`,
  },
  {
    key: "precipitation_probability",
    label: "Rain chance",
    unit: "%",
    shade: percentShade,
    hourBefore: true,
  },
];

export interface Cell {
  hour: number;
  // The part of the hour on the axis: the hour itself, unless an axis end cuts it.
  from: number;
  to: number;
  value: number;
  // One of the two, as the row draws it: a blue, or an arrow's turn in degrees
  // clockwise from pointing up.
  shade?: string;
  arrow?: number;
  // What hovering over the cell shows.
  text: string;
}

// Why a row has no cell to draw, in the words the row shows.
export interface Missing {
  message: "Not found" | "Unavailable" | "No forecast" | "Needs two forecasts";
  // What hovering over the message shows: the sensor's id, so the user can find
  // it, or for the Cloud range row, what the row needs.
  text: string;
}

// One hour of the Cloud range row: a column across the hour, holding a bar from
// the lowest to the highest cloud any forecast gave.
export interface Band {
  hour: number;
  from: number;
  to: number;
  // In percent, clamped to 0–100 for drawing.
  low: number;
  high: number;
  // What hovering over the column shows, with the values unclamped.
  text: string;
}

export interface Row {
  key: string;
  label: string;
  cells: Cell[];
  // Only on the Cloud range row, which draws bands instead of cells.
  bands?: Band[];
  // Only on a row with no cell.
  missing?: Missing;
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

// One rank of the target list, drawn as a lane under the Moon up lane.
export interface TargetLane {
  rank: number;
  label: string;
  // The Target sensor's state: the target's name.
  name: string;
  // Absent when the window is wholly off the axis; the lane stays, so the
  // number of lanes never moves with the clock.
  bar?: Bar;
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
  // The axis the strip opens on, and how far it can pan from there.
  opening: Axis;
  reach: Axis;
  // The core sends a dark window with two null ends when the sun never gets 18°
  // below the horizon; a missing or unreadable window is not that.
  noDarkness: boolean;
  rows: Row[];
  moonUp: Bar[];
  // The Moon altitude row's, since the lane reads the same sensor.
  moonUpMissing?: Missing;
  targets: TargetLane[];
  lines: Line[];
  labels: TimeLabel[];
}

type States = Record<string, { state: string; attributes: Record<string, unknown> } | undefined>;

// Without a start, the strip is on the opening axis. With one, it is panned
// there, as far as the reach allows.
export function buildStrip(
  states: States,
  pier: string,
  now: number,
  timeZone: string | undefined,
  start?: number,
): Strip {
  const verdict = states[pierEntityId(pier, "verdict")];
  const window = asRecord(verdict?.attributes["dark_window"]);
  const night = darkWindow(window);
  const opening = stripAxis(night, now);
  const reach = stripReach(states, pier, opening);
  const axis = start === undefined ? opening : panned(opening, reach, start);
  const time = clock(timeZone);
  const rows = ROWS.map(({ key, label, unit, hourBefore, reading, ...mark }): Row => {
    const write = reading ?? ((value: number) => `${value}${unit}`);
    const entityId = pierEntityId(pier, key);
    const entity = states[entityId];
    const cells = rowCells(
      forecastOf(entity),
      axis,
      (value) => (mark.arrow ? { arrow: mark.arrow(value) } : { shade: mark.shade(value) }),
      hourBefore ? -HOUR : 0,
    ).map((cell) => ({
      ...cell,
      text: `${label}, the hour from ${time(cell.hour)}: ${write(cell.value)}`,
    }));
    if (cells.length > 0) return { key, label, cells };
    return { key, label, cells, missing: missing(entityId, entity) };
  });
  // Under Cloud cover, the row it explains.
  const cloudCover = rows.findIndex((row) => row.key === "cloud_cover");
  rows.splice(cloudCover + 1, 0, cloudRange(states, pier, axis, time));
  const moonMissing = rows.find((row) => row.key === "moon_altitude")?.missing;
  return {
    axis,
    opening,
    reach,
    noDarkness: window?.["start"] === null && window["end"] === null,
    labels: timeLabels(axis, time),
    rows,
    moonUp: moonUpBars(forecastOf(states[pierEntityId(pier, "moon_altitude")]), axis, time),
    ...(moonMissing && { moonUpMissing: moonMissing }),
    targets: targetLanes(states, pier, axis, time),
    lines: [
      ...(night === undefined ? [] : nightLines(night, axis, time)),
      ...nowLine(now, axis, time),
    ],
  };
}

// The opening axis always holds both; a panned one may hold either or neither.
function nightLines(night: Night, axis: Axis, time: (at: number) => string): Line[] {
  const lines: Line[] = [
    { kind: "dusk", at: night.dusk, text: `Dusk, ${time(night.dusk)}` },
    { kind: "dawn", at: night.dawn, text: `Dawn, ${time(night.dawn)}` },
  ];
  return lines.filter((line) => line.at >= axis.start && line.at <= axis.end);
}

function nowLine(now: number, axis: Axis, time: (at: number) => string): Line[] {
  if (now < axis.start || now > axis.end) return [];
  return [{ kind: "now", at: now, text: `Now, ${time(now)}` }];
}

// Decided after the cells, so every way a row can end up empty, from no list to
// every point off the axis, gives a message.
function missing(entityId: string, entity: States[string]): Missing {
  if (entity === undefined) {
    return { message: "Not found", text: `${entityId} is not in Home Assistant` };
  }
  if (entity.state === "unavailable") {
    return { message: "Unavailable", text: `${entityId} is unavailable` };
  }
  return { message: "No forecast", text: `${entityId} has no forecast for these hours` };
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
  mark: (value: number) => Pick<Cell, "shade" | "arrow">,
  shift: number,
): Omit<Cell, "text">[] {
  if (!Array.isArray(forecast)) return [];
  return forecast.flatMap((point: unknown) => {
    const record = asRecord(point);
    const time = readTime(record?.["datetime"]);
    const hour = time === undefined ? undefined : time + shift;
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
        ...mark(value),
      },
    ];
  });
}

// An hour has a band only when both sensors give it a number: the core sends
// both or neither, and a gap in one forecast is not a range. A min above the
// max is skipped, not swapped: Home Assistant applies the two sensors' updates
// one at a time, and a new min against an old max is no forecast's range.
function cloudRange(states: States, pier: string, axis: Axis, time: (at: number) => string): Row {
  const lows = hourlyValues(forecastOf(states[pierEntityId(pier, "cloud_cover_min")]));
  const highs = hourlyValues(forecastOf(states[pierEntityId(pier, "cloud_cover_max")]));
  const bands = [...lows].flatMap(([hour, low]): Band[] => {
    const high = highs.get(hour);
    if (!isNumber(low) || !isNumber(high) || low > high) return [];
    if (hour + HOUR <= axis.start || hour >= axis.end) return [];
    return [
      {
        hour,
        from: Math.max(hour, axis.start),
        to: Math.min(hour + HOUR, axis.end),
        low: percent(low),
        high: percent(high),
        text: `Cloud range, the hour from ${time(hour)}: ${low}% to ${high}%`,
      },
    ];
  });
  const row = { key: "cloud_range", label: "Cloud range", cells: [], bands };
  if (bands.length > 0) return row;
  return { ...row, missing: cloudRangeMissing(states, pier) };
}

// A missing sensor comes before an unavailable one, whichever of the two it is.
// With both there, an empty row usually means one cloud provider, which is the
// default, so the message says what the row needs rather than that no forecast came.
function cloudRangeMissing(states: States, pier: string): Missing {
  const ids = [pierEntityId(pier, "cloud_cover_min"), pierEntityId(pier, "cloud_cover_max")];
  const absent = ids.find((id) => states[id] === undefined);
  if (absent) return { message: "Not found", text: `${absent} is not in Home Assistant` };
  const down = ids.find((id) => states[id]?.state === "unavailable");
  if (down) return { message: "Unavailable", text: `${down} is unavailable` };
  return {
    message: "Needs two forecasts",
    text: "No hour on the strip has cloud cover from two or more forecasts",
  };
}

function percent(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
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
  // HH:MM cannot tell one day from the next. A clock change can make a run
  // under 24 hours start and end at the same time of day.
  if (run.end - run.start >= 24 * HOUR || time(run.start) === time(run.end)) return "Moon up";
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

// The rank sensors PierPressure publishes, Target 1 to Target 10.
const TARGET_RANKS = 10;

// A rank's state is the name its bar shows. PierPressure publishes the state and
// the window as two messages, so for a moment Home Assistant can hold an empty or
// unknown state beside a window; such a rank waits for its name.
const NO_NAME = new Set(["", "unknown", "unavailable"]);

function targetLanes(
  states: States,
  pier: string,
  axis: Axis,
  time: (at: number) => string,
): TargetLane[] {
  return Array.from({ length: TARGET_RANKS }, (_, index) => index + 1).flatMap((rank) => {
    const entity = states[pierEntityId(pier, `target_${rank}`)];
    if (entity === undefined || NO_NAME.has(entity.state)) return [];
    const window = asRecord(entity.attributes["window"]);
    const start = readTime(window?.["start"]);
    const end = readTime(window?.["end"]);
    if (start === undefined || end === undefined || end <= start) return [];
    const name = entity.state;
    const lane: TargetLane = { rank, label: `Target ${rank}`, name };
    if (end <= axis.start || start >= axis.end) return [lane];
    const from = Math.max(start, axis.start);
    const to = Math.min(end, axis.end);
    return [{ ...lane, bar: { start, end, from, to, text: targetText(name, start, end, time) } }];
  });
}

// As for a Moon up run, HH:MM cannot tell one day from the next. A polar night's
// window runs from solar noon to solar noon, and a target can be up for all of it.
function targetText(name: string, start: number, end: number, time: (at: number) => string) {
  if (end - start >= 24 * HOUR || time(start) === time(end)) return name;
  return `${name} from ${time(start)} to ${time(end)}`;
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

// The YAML strip's seven blues, lightest to darkest.
const BLUES = [
  "#cde2fb",
  "#9ec5f4",
  "#6da7ec",
  "#3987e5",
  "#256abf",
  "#184f95",
  "#0d366b",
] as const;

// A value outside its row's range takes the nearest end of the palette.
function blue(step: number): string {
  return BLUES[Math.min(BLUES.length - 1, Math.max(0, step))] ?? BLUES[0];
}

function percentShade(percent: number): string {
  return blue(Math.floor(percent / 15));
}

// The YAML strip's twilight band: sun up, civil, nautical and astronomical
// twilight, then the darkest blue for astronomical night from −18°.
function sunShade(degrees: number): string {
  return blue(degrees > 0 ? 0 : degrees > -6 ? 1 : degrees > -12 ? 2 : degrees > -18 ? 3 : 6);
}

// The YAML strip's moon band: lightest while the moon is down, then one step per 6°.
function moonShade(degrees: number): string {
  return blue(degrees <= 0 ? 0 : 1 + Math.floor(degrees / 6));
}

// A quality from 0 to 1, where 1 is best, so darker is worse, as in the YAML strip.
function qualityShade(quality: number): string {
  return blue(Math.round((1 - quality) * 7));
}

// Temperature and Dew point share this scale, so the two rows compare by eye:
// one step per 5 °C, from below −5 °C to 20 °C or more.
function temperatureShade(celsius: number): string {
  return blue(Math.floor((celsius + 10) / 5));
}

// The sensor gives the direction the wind blows from; the arrow points the
// way it blows to, as on a weather map.
function windArrow(degrees: number): number {
  return (((degrees + 180) % 360) + 360) % 360;
}

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] as const;

// The nearest of eight points; halfway between two rounds to the next clockwise.
function compassPoint(degrees: number): string {
  const turned = ((degrees % 360) + 360) % 360;
  return COMPASS[Math.round(turned / 45) % COMPASS.length] ?? COMPASS[0];
}

// One step per 7 km/h, so 42 km/h or more is the darkest, as in the YAML strip.
function windShade(speed: number): string {
  return blue(Math.floor(speed / 7));
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
