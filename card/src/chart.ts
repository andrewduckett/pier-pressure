import { css, html, svg } from "lit";
import { iso, offset } from "./place";
import type { Axis, ChartLine, ChartPoint, Missing, TemperatureChart } from "./strip";

export const chartStyles = css`
  /* The key and the scale side by side, as tall as the chart. */
  .chart-label {
    display: grid;
    grid-template-columns: max-content minmax(40px, max-content);
    column-gap: 8px;
  }
  .key .entry {
    display: flex;
    align-items: center;
    gap: 4px;
    height: 16px;
  }
  .key .swatch {
    flex-shrink: 0;
    width: 12px;
    height: 3px;
  }
  .scale {
    position: relative;
  }
  .scale .step {
    position: absolute;
    right: 0;
    font-size: 0.75em;
    line-height: 1;
    white-space: nowrap;
  }
  /* Fills the track and cuts the lines off at the axis ends. */
  .plot {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
`;

type Scale = NonNullable<TemperatureChart["scale"]>;

// The chart's grid row: its key in the label column, its lines in the track.
export function renderChart(chart: TemperatureChart, axis: Axis) {
  const scale = chart.scale;
  const celsius = scale === undefined ? [] : steps(scale);
  // One step is as tall as a row.
  const tall = scale === undefined ? 32 : ((scale.high - scale.low) / STEP) * 16;
  return html`<div class="row" data-chart="temperature">
    <div class="label chart-label">
      <div class="key">${chart.lines.map(renderKeyEntry)}</div>
      <div class="scale">
        ${scale === undefined ? [] : celsius.map((value) => renderStep(value, scale))}
      </div>
    </div>
    <div class="track" style=${`height: ${tall}px`}>
      <svg class="plot" aria-hidden="true">
        ${scale === undefined ? [] : celsius.map((value) => renderGridline(value, scale))}
        ${scale === undefined ? [] : chart.lines.map((line) => renderLine(line, scale, axis))}
      </svg>
    </div>
  </div>`;
}

const STEP = 5;

// From the top of the scale down.
function steps(scale: Scale): number[] {
  const count = (scale.high - scale.low) / STEP;
  return Array.from({ length: count + 1 }, (_, index) => scale.high - index * STEP);
}

// The end labels align to the chart's edges, so neither sticks out into the
// next row.
function renderStep(celsius: number, scale: Scale) {
  const shift = celsius === scale.high ? "0" : celsius === scale.low ? "-100%" : "-50%";
  const style = `top: ${height(celsius, scale)}%; transform: translateY(${shift})`;
  return html`<span class="step" style=${style} data-celsius=${celsius}>${celsius} °C</span>`;
}

function renderGridline(celsius: number, scale: Scale) {
  const y = `${height(celsius, scale)}%`;
  return svg`<line
    class="grid"
    data-celsius=${celsius}
    x1="0"
    x2="100%"
    y1=${y}
    y2=${y}
    stroke="#898781"
    stroke-opacity="0.4"
    stroke-width="1"
  ></line>`;
}

// Percent coordinates, so the chart reflows with the card as the cells do.
function renderLine(line: ChartLine, scale: Scale, axis: Axis) {
  const x = (point: ChartPoint) => `${offset(point.at, axis)}%`;
  const y = (point: ChartPoint) => `${height(point.value, scale)}%`;
  return svg`${line.segments.map(
    ([from, to]) =>
      svg`<line
        data-series=${line.key}
        data-from=${iso(from.at)}
        data-to=${iso(to.at)}
        x1=${x(from)}
        y1=${y(from)}
        x2=${x(to)}
        y2=${y(to)}
        stroke=${line.colour}
        stroke-width="2"
        stroke-linecap="round"
      ></line>`,
  )}${line.dots.map(
    (dot) =>
      svg`<circle
        data-series=${line.key}
        data-at=${iso(dot.at)}
        cx=${x(dot)}
        cy=${y(dot)}
        r="2.5"
        fill=${line.colour}
      ></circle>`,
  )}`;
}

// Percent from the top of the chart.
function height(celsius: number, scale: Scale): string {
  return (((scale.high - celsius) / (scale.high - scale.low)) * 100).toFixed(4);
}

function renderKeyEntry(line: ChartLine) {
  return html`<span class="entry" data-series=${line.key}>
    <span class="swatch" style=${`background-color: ${line.colour}`}></span
    ><span class="name">${line.label}</span>
  </span>`;
}

export function renderMissing(missing: Missing) {
  const kind = missing.message.toLowerCase().replace(/ /g, "-");
  return html`<span
    class="missing"
    data-missing=${kind}
    title=${missing.text}
    aria-label=${missing.text}
    >${missing.message}</span
  >`;
}
