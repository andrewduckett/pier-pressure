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

const WANING: readonly string[] = ["waning gibbous", "last quarter", "waning crescent"];

export interface MoonView {
  phase: string;
  illumination: string;
  rise: string;
  set: string;
  // Only when both the phase and the illumination are valid.
  drawing?: MoonDrawing;
}

export interface MoonDrawing {
  // A number is the share of the disc that is lit, above 0 and below 1.
  lit: "none" | "all" | number;
  // True when the lit part touches the left edge rather than the right.
  mirrored: boolean;
  text: string;
}

// Each text falls back to a dash on its own, as the verdict lines do. The
// latitude is Home Assistant's: the document carries no pier location.
export function readMoon(
  attribute: unknown,
  time: (at: number) => string,
  latitude: unknown,
): MoonView {
  const moon = asRecord(attribute);
  const phase = readPhase(moon?.["phase"]);
  const illumination = readIllumination(moon?.["illumination"]);
  return {
    phase: phase === undefined ? DASH : phase.charAt(0).toUpperCase() + phase.slice(1),
    illumination: illumination === undefined ? DASH : `${percent(illumination)}%`,
    rise: shownTime(moon?.["rise"], time),
    set: shownTime(moon?.["set"], time),
    ...(phase !== undefined &&
      illumination !== undefined && { drawing: drawn(phase, illumination, latitude) }),
  };
}

// The document does not say which side a new or full moon's sliver is on, so
// those two phases draw no lit part and the whole disc. At 0 or 1 no phase has
// a lit path to draw.
function drawn(phase: string, illumination: number, latitude: unknown): MoonDrawing {
  const text = `Moon: ${phase}, ${percent(illumination)}% lit`;
  if (phase === "new" || illumination === 0) return { lit: "none", mirrored: false, text };
  if (phase === "full" || illumination === 1) return { lit: "all", mirrored: false, text };
  // Seen from the north, a waxing moon is lit on the right; from the south, on the left.
  const south = typeof latitude === "number" && latitude < 0;
  return { lit: illumination, mirrored: WANING.includes(phase) !== south, text };
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
