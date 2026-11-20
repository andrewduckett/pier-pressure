import { css, html } from "lit";
import type { Axis, ChartLine, Missing, TemperatureChart } from "./strip";

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
`;

// The chart's grid row: its key in the label column, its lines in the track.
export function renderChart(chart: TemperatureChart, _axis: Axis) {
  return html`<div class="row" data-chart="temperature">
    <div class="label chart-label">
      <div class="key">${chart.lines.map(renderKeyEntry)}</div>
    </div>
    <div class="track" style="height: 32px"></div>
  </div>`;
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
