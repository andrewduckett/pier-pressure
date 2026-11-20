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
  return html`<div class="row" data-chart="temperature">
    <div class="label chart-label">
      <div class="key">${chart.lines.map(renderKeyEntry)}</div>
    </div>
    <div class="track" style="height: 32px">
      <svg class="plot" aria-hidden="true">
        ${scale === undefined ? [] : chart.lines.map((line) => renderLine(line, scale, axis))}
      </svg>
    </div>
  </div>`;
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
        stroke="currentColor"
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
        fill="currentColor"
      ></circle>`,
  )}`;
}

// Percent from the top of the chart.
function height(celsius: number, scale: Scale): string {
  return (((scale.high - celsius) / (scale.high - scale.low)) * 100).toFixed(4);
}

function renderKeyEntry(line: ChartLine) {
  return html`<span class="entry" data-series=${line.key}>
    <span class="swatch"></span><span class="name">${line.label}</span>
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
