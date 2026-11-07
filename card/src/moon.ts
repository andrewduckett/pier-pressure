import { asRecord, readTime } from "./strip";

const DASH = "—";

// The core's eight phase names (pierpressure/core/model.py MoonPhase).
const PHASES: readonly string[] = [
  "new",
  "waxing crescent",
  "first quarter",
  "waxing gibbous",
  "full",
  "waning gibbous",
  "last quarter",
  "waning crescent",
];

export interface MoonView {
  phase: string;
  illumination: string;
  rise: string;
  set: string;
}

// Each text falls back to a dash on its own, as the verdict lines do.
export function readMoon(attribute: unknown, time: (at: number) => string): MoonView {
  const moon = asRecord(attribute);
  const phase = readPhase(moon?.["phase"]);
  const illumination = readIllumination(moon?.["illumination"]);
  return {
    phase: phase === undefined ? DASH : phase.charAt(0).toUpperCase() + phase.slice(1),
    illumination: illumination === undefined ? DASH : `${percent(illumination)}%`,
    rise: shownTime(moon?.["rise"], time),
    set: shownTime(moon?.["set"], time),
  };
}

function readPhase(value: unknown): string | undefined {
  return typeof value === "string" && PHASES.includes(value) ? value : undefined;
}

function readIllumination(value: unknown): number | undefined {
  return typeof value === "number" && value >= 0 && value <= 1 ? value : undefined;
}

function percent(illumination: number): number {
  return Math.round(illumination * 100);
}

function shownTime(value: unknown, time: (at: number) => string): string {
  const at = readTime(value);
  return at === undefined ? DASH : time(at);
}
