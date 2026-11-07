const HOUR = 60 * 60 * 1000;

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
