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
  // Only when both the phase and the illumination are valid.
  drawing?: MoonDrawing;
}

export interface MoonDrawing {
  // The illumination, as the share of the disc that is lit.
  lit: number;
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
    ...(phase !== undefined && illumination !== undefined && { drawing: { lit: illumination } }),
  };
}

// The right half-disc's edge, then the terminator back to the top as a
// half-ellipse. It crosses the middle at x = 1 - 2k, so the lit part spans the
// share k of the width, as the sphere's terminator does seen face on.
export function litPath(lit: number): string {
  const rx = Number(Math.abs(1 - 2 * lit).toFixed(4));
  const sweep = lit < 0.5 ? 0 : 1;
  return `M 0 -1 A 1 1 0 0 1 0 1 A ${rx} 1 0 0 ${sweep} 0 -1 Z`;
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
