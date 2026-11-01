# Night dashboard

A Home Assistant dashboard that shows tonight's verdict for one pier.

## The dashboard YAML

```yaml
title: PierPressure
views:
  - title: Tonight
    path: tonight
    type: sections
    max_columns: 4
    sections:
      - type: grid
        column_span: 4
        cards:
          - type: heading
            heading: Night strip
          - type: custom:plotly-graph
            grid_options:
              columns: full
            pier_timeline: |
              $ex {
                const ramp = (v, step) => Math.min(6, Math.floor(v / step));
                const quality = (q) => Math.min(6, Math.round((1 - q) * 7));
                // Top to bottom: row label, timeline sensor, unit, and the band 0 (lightest) to 6 (darkest).
                const rows = [
                  ["Sun altitude", "sensor.pierpressure_backyard_sun_altitude", "°",
                    (v) => (v > 0 ? 0 : v > -6 ? 1 : v > -12 ? 2 : v > -18 ? 3 : 6)],
                  ["Moon altitude", "sensor.pierpressure_backyard_moon_altitude", "°",
                    (v) => (v <= 0 ? 0 : Math.min(6, 1 + Math.floor(v / 6)))],
                  ["Cloud cover", "sensor.pierpressure_backyard_cloud_cover", "%", (v) => ramp(v, 15)],
                  ["Cloud low", "sensor.pierpressure_backyard_cloud_low", "%", (v) => ramp(v, 15)],
                  ["Cloud mid", "sensor.pierpressure_backyard_cloud_mid", "%", (v) => ramp(v, 15)],
                  ["Cloud high", "sensor.pierpressure_backyard_cloud_high", "%", (v) => ramp(v, 15)],
                  ["Wind gust", "sensor.pierpressure_backyard_wind_gust", " km/h", (v) => ramp(v, 7)],
                  ["Seeing", "sensor.pierpressure_backyard_seeing", "", quality],
                  ["Transparency", "sensor.pierpressure_backyard_transparency", "", quality],
                ];
                const forecasts = rows.map(([, id]) => hass.states[id]?.attributes?.forecast ?? []);
                const hours = [...new Set(forecasts.flat().map((p) => p.datetime))].sort();
                const values = forecasts.map((f) => new Map(f.map((p) => [p.datetime, p.value])));
                vars.strip = {
                  // A value covers the hour that starts at its datetime, so its cell is centred on the half hour.
                  x: hours.map((h) => new Date(Date.parse(h) + 30 * 60 * 1000)),
                  y: rows.map(([label]) => label),
                  z: rows.map(([, , , band], i) => hours.map((h) => {
                    const v = values[i].get(h);
                    return v == null ? null : band(v);
                  })),
                  text: rows.map(([, , unit], i) => hours.map((h) => {
                    const v = values[i].get(h);
                    return v == null ? "no data" : `${v}${unit}`;
                  })),
                };
              }
            entities:
              - entity: ""
                name: Night strip
                type: heatmap
                yaxis: y
                x: $ex vars.strip.x
                y: $ex vars.strip.y
                z: $ex vars.strip.z
                text: $ex vars.strip.text
                zmin: -0.5
                zmax: 6.5
                showscale: false
                xgap: 1
                ygap: 2
                hoverongaps: false
                hovertemplate: "%{y} %{x|%H:%M}: %{text}<extra></extra>"
                colorscale:
                  - [0, "#cde2fb"]
                  - [0.1428, "#cde2fb"]
                  - [0.1428, "#9ec5f4"]
                  - [0.2857, "#9ec5f4"]
                  - [0.2857, "#6da7ec"]
                  - [0.4285, "#6da7ec"]
                  - [0.4285, "#3987e5"]
                  - [0.5714, "#3987e5"]
                  - [0.5714, "#256abf"]
                  - [0.7142, "#256abf"]
                  - [0.7142, "#184f95"]
                  - [0.8571, "#184f95"]
                  - [0.8571, "#0d366b"]
                  - [1, "#0d366b"]
            layout:
              height: 300
              margin: { t: 30, b: 50, l: 100, r: 10 }
              showlegend: false
              xaxis:
                type: date
              yaxis:
                type: category
                categoryorder: array
                categoryarray: [Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency]
                autorange: reversed
                fixedrange: true
                showgrid: false
```
