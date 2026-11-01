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
            refresh_interval: 300
            time_zone: server
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
                  moon: hours.map((h) => [new Date(h), values[1].get(h)]),
                };
              }
            pier_night: |
              $ex {
                const night = hass.states["sensor.pierpressure_backyard_verdict"]?.attributes?.dark_window ?? {};
                const hour = 60 * 60 * 1000;
                vars.now = new Date();
                vars.dusk = night.start && night.end ? new Date(night.start) : null;
                vars.dawn = night.start && night.end ? new Date(night.end) : null;
                vars.range = vars.dusk
                  ? [new Date(vars.dusk.getTime() - 4 * hour), new Date(vars.dawn.getTime() + 5 * hour)]
                  : [new Date(vars.now.getTime() - 6 * hour), new Date(vars.now.getTime() + 18 * hour)];
              }
            pier_targets: |
              $ex {
                const ids = [
                  "sensor.pierpressure_backyard_target_1", "sensor.pierpressure_backyard_target_2",
                  "sensor.pierpressure_backyard_target_3", "sensor.pierpressure_backyard_target_4",
                  "sensor.pierpressure_backyard_target_5", "sensor.pierpressure_backyard_target_6",
                  "sensor.pierpressure_backyard_target_7", "sensor.pierpressure_backyard_target_8",
                  "sensor.pierpressure_backyard_target_9", "sensor.pierpressure_backyard_target_10",
                ];
                // An unavailable rank has no attributes, so it has no window and leaves no lane.
                vars.targets = ids
                  .map((id, i) => ({ lane: `Target ${i + 1}`, state: hass.states[id] }))
                  .filter((t) => t.state?.attributes?.window?.start && t.state?.attributes?.window?.end)
                  .map((t) => ({
                    lane: t.lane,
                    label: t.state.state,
                    start: new Date(t.state.attributes.window.start),
                    end: new Date(t.state.attributes.window.end),
                  }));
              }
            pier_lanes: |
              $ex {
                const hour = 60 * 60 * 1000;
                const runs = [];
                vars.strip.moon.forEach(([start, v]) => {
                  if (v == null || v <= 0) return;
                  const last = runs.at(-1);
                  if (last && last.end.getTime() === start.getTime()) last.end = new Date(start.getTime() + hour);
                  else runs.push({ lane: "Moon up", label: "Moon up", start, end: new Date(start.getTime() + hour) });
                });
                vars.bars = [...runs, ...vars.targets];
                vars.lanes = ["Moon up", ...vars.targets.map((t) => t.lane)];
                // Every lane keeps the same height, whatever the number of lanes.
                const rowsPx = 9 * 22, lanePx = 20, marginPx = 30 + 50;
                vars.height = rowsPx + lanePx * vars.lanes.length + marginPx + 10;
                const plot = vars.height - marginPx;
                vars.split = (lanePx * vars.lanes.length) / plot;
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
              - entity: ""
                name: Lanes
                type: bar
                orientation: h
                yaxis: y2
                y: $ex vars.bars.map((b) => b.lane)
                base: $ex vars.bars.map((b) => b.start)
                x: $ex vars.bars.map((b) => b.end.getTime() - b.start.getTime())
                text: $ex vars.bars.map((b) => b.label)
                textposition: inside
                insidetextanchor: start
                marker:
                  color: >-
                    $ex vars.bars.map((b) => (b.lane === "Moon up" ? "#898781" : "#6250d6"))
                hovertemplate: "%{text}<extra></extra>"
            layout:
              height: $ex vars.height
              margin: { t: 30, b: 50, l: 100, r: 10 }
              showlegend: false
              bargap: 0.25
              xaxis:
                type: date
                # Ticks along the bottom, under the lanes.
                anchor: y2
                range: $ex vars.range
              yaxis:
                domain: $ex [vars.split + 0.02, 1]
                type: category
                categoryorder: array
                categoryarray: [Sun altitude, Moon altitude, Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust, Seeing, Transparency]
                autorange: reversed
                fixedrange: true
                showgrid: false
              yaxis2:
                # The card overlays extra y-axes on the first by default; the lanes need their own band.
                overlaying: free
                side: left
                anchor: x
                domain: $ex [0, vars.split]
                type: category
                categoryorder: array
                categoryarray: $ex vars.lanes
                range: $ex [vars.lanes.length - 0.5, -0.5]
                fixedrange: true
                showgrid: false
              shapes: |
                $ex [
                  ...(vars.dusk ? [vars.dusk, vars.dawn] : []).map((x) => ({
                    type: "line", xref: "x", yref: "paper", x0: x, x1: x, y0: 0, y1: 1,
                    line: { color: "#898781", width: 2, dash: "dash" },
                  })),
                  { type: "line", xref: "x", yref: "paper", x0: vars.now, x1: vars.now, y0: 0, y1: 1,
                    line: { color: "#e66767", width: 2 } },
                ]
              annotations: |
                $ex [
                  ...(vars.dusk ? [[vars.dusk, "dusk"], [vars.dawn, "dawn"]] : []).map(([x, text]) => ({
                    x, text, xref: "x", yref: "paper", y: 1, yanchor: "bottom", showarrow: false,
                    font: { color: "#898781", size: 11 },
                  })),
                  { x: vars.now, text: "now", xref: "x", yref: "paper", y: 1, yanchor: "bottom",
                    showarrow: false, font: { color: "#e66767", size: 11 } },
                ]
```
