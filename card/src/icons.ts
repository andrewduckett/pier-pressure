// The strip's label icons: 24 by 24 drawings, stroked in the text colour.
import { css, html, nothing, svg, type SVGTemplateResult } from "lit";
import type { Strip } from "./strip";

export const iconStyles = css`
  .icon {
    display: inline-flex;
    flex-shrink: 0;
  }
  .icon svg {
    display: block;
    width: 16px;
    height: 16px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  /* Shown only on a narrow card, which names its icons nowhere else. */
  .legend {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 4px 12px;
    margin: 12px 0 0;
    padding: 0;
    list-style: none;
    color: var(--secondary-text-color);
    font-size: 0.75em;
  }
  .legend li {
    display: flex;
    align-items: center;
    gap: 4px;
    line-height: 16px;
  }
`;

// A small cloud centred on 0 0, moved into place by each icon that draws one.
const CLOUD = "M-6 3h11a3 3 0 0 0 0-6a4 4 0 0 0-7.6 1A2.6 2.6 0 0 0-6 3z";

// Cloud low, mid and high share a corner of axes, with the cloud at its height.
function cloudAt(y: number): SVGTemplateResult {
  return svg`<path d="M3 3v18h18" opacity=".55"></path><path
      d=${CLOUD}
      transform=${`translate(14 ${y})`}
    ></path>`;
}

// Keyed by a row's key, `moon_up`, or a Temperature chart line's key.
export const ICONS: Readonly<Record<string, SVGTemplateResult>> = {
  sun_altitude: svg`<path d="M2 19h20"></path><path d="M7 19a5 5 0 0 1 10 0"></path><path
      d="M12 9V6M6.3 11.3 4.5 9.5M17.7 11.3l1.8-1.8"
    ></path>`,
  moon_altitude: svg`<path d="M2 20h20"></path><path d="M15 4a6 6 0 1 0 5 9 5 5 0 0 1-5-9z"></path>`,
  cloud_cover: svg`<path d="M7 19h10a4.5 4.5 0 0 0 .6-9A6 6 0 0 0 6.2 12 3.5 3.5 0 0 0 7 19z"></path>`,
  cloud_range: svg`<path d=${CLOUD} transform="translate(12 7)"></path><path
      d="M12 13v8M9.5 13h5M9.5 21h5"
    ></path>`,
  cloud_low: cloudAt(17),
  cloud_mid: cloudAt(11.5),
  cloud_high: cloudAt(6),
  wind_gust: svg`<path d="M2 8h9a2.5 2.5 0 1 0-2.5-2.5"></path><path d="M2 13h6"></path><path
      d="M14 11l2.5 2.5L14 16M18.5 11l2.5 2.5-2.5 2.5"
    ></path><path d="M2 18h9"></path>`,
  seeing: svg`<path
      d="M12 2.5l1.3 3.2 3.2 1.3-3.2 1.3L12 11.5l-1.3-3.2L7.5 7l3.2-1.3z"
      fill="currentColor"
    ></path><path
      d="M3 15.5q2.25-2 4.5 0t4.5 0 4.5 0 4.5 0M3 20q2.25-2 4.5 0t4.5 0 4.5 0 4.5 0"
    ></path>`,
  transparency: svg`<path
      d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"
    ></path><circle cx="12" cy="12" r="2.8"></circle>`,
  humidity: svg`<path d="M12 2.8S5.8 10 5.8 14.2a6.2 6.2 0 0 0 12.4 0C18.2 10 12 2.8 12 2.8z"></path>`,
  wind_speed: svg`<path
      d="M9.6 4.6A2 2 0 1 1 11 8H2m10.6 11.4A2 2 0 1 0 14 16H2m15.7-8.3A2.5 2.5 0 1 1 19.5 12H2"
    ></path>`,
  wind_direction: svg`<circle cx="12" cy="12" r="9.5"></circle><path
      d="M12 5.5l3 9-3-1.8-3 1.8z"
      fill="currentColor"
    ></path>`,
  precipitation_probability: svg`<path d="M2.5 12a9.5 9.5 0 0 1 19 0z"></path><path
      d="M12 12v6.5a2 2 0 0 0 4 0"
    ></path>`,
  moon_up: svg`<path
      d="M15 3a8 8 0 1 0 6 12.5A6.5 6.5 0 0 1 15 3z"
      fill="currentColor"
      stroke="none"
    ></path>`,
  temperature: svg`<path d="M14 14.8V4.5a2 2 0 0 0-4 0v10.3a4.2 4.2 0 1 0 4 0z"></path>`,
  dew_point: svg`<path
      d="M12 2.8S5.8 10 5.8 14.2a6.2 6.2 0 0 0 12.4 0C18.2 10 12 2.8 12 2.8z"
    ></path><path d="M8.5 15.5h7"></path>`,
};

// The wrapper, not an SVG <title>, names the icon: a <title> would add the name
// to the label's text a second time.
export function renderIcon(key: string, name: string) {
  return html`<span class="icon" role="img" title=${name} aria-label=${name}
    ><svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[key]}</svg></span
  >`;
}

// The label's icon names it for a screen reader, so this copy is hidden, and a
// tap on it closes the box.
function renderListedIcon(key: string) {
  return html`<span class="icon" aria-hidden="true"
    ><svg viewBox="0 0 24 24">${ICONS[key]}</svg></span
  >`;
}

// Each icon the strip draws, top to bottom, then what a bare rank number means.
export function renderLegend(strip: Strip | undefined) {
  if (strip === undefined) return nothing;
  const entries = [
    ...strip.rows.map((row) => ({ key: row.key, name: row.label })),
    { key: "moon_up", name: "Moon up" },
    ...strip.chart.lines.map((line) => ({ key: line.key, name: line.label })),
  ];
  const first = strip.targets[0];
  return html`<ul class="legend">
    ${entries.map(
      ({ key, name }) => html`<li>${renderListedIcon(key)}<span class="name">${name}</span></li>`,
    )}
    ${
      first === undefined
        ? nothing
        : html`<li>
            <span class="rank" aria-hidden="true">${first.rank}</span
            ><span class="name">Target rank</span>
          </li>`
    }
  </ul>`;
}
