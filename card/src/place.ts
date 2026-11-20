import { type Axis, HOUR } from "./strip";

// Neighbouring hours keep a 2 px gap; an edge cut off by
// the axis stays flush with the axis end instead.
export function hourPlace(hour: { hour: number; from: number; to: number }, axis: Axis): string {
  const left = offset(hour.from, axis);
  const width = share(hour.to - hour.from, axis);
  const insetStart = hour.from === hour.hour ? 1 : 0;
  const insetEnd = hour.to === hour.hour + HOUR ? 1 : 0;
  return (
    `left: calc(${left}% + ${insetStart}px); ` +
    `width: calc(${width}% - ${insetStart + insetEnd}px)`
  );
}

// Percent of the axis, so the strip reflows with the card's width.
export function share(duration: number, axis: Axis): string {
  return ((duration / (axis.end - axis.start)) * 100).toFixed(4);
}

export function offset(at: number, axis: Axis): string {
  return share(at - axis.start, axis);
}

export function iso(time: number): string {
  return new Date(time).toISOString();
}

