## Context

- Every value the strip needs is already published. The nine timeline sensors carry `forecast` as `[{datetime, value}]`, one point per timeline hour, with nulls kept in place. The Verdict entity carries `dark_window`, `moon` and the rest of the document except `timeline`. Target 1 to 10 carry `available`, `rank` and the target's fields, including `window {start, end}`, at the top level. The two health sensors are timestamp sensors.
- PierPressure gives each timeline sensor no `state_class`, and `docs/night-timeline.md` tells readers to exclude the timeline sensors from the recorder. So the strip cannot rely on history. It reads the live `forecast` attribute only.
- When PierPressure is offline, Home Assistant drops every attribute of its entities.
- plotly-graph-card is at v4.0.2 (released 2026-10-13). Its README confirms that `$ex` and `$fn` expressions work anywhere in the card's YAML and receive `hass` and `vars`. A trace with `entity: ""` takes computed `x` and `y`. `time_zone: server` uses Home Assistant's time zone. Times must be `Date` objects, because a number is drawn in the browser's time zone. Any plotly trace type passes through, including `heatmap` and `bar`.
- The docs already have light guard tests (`tests/test_docs.py`, `tests/test_explainer_docs.py`, `tests/test_data_updates_doc.py`). `tests/conftest.py` has `make_document` for building a verdict document. PyYAML is already a dependency.
- Docker is available, and `compose.yaml` already runs mosquitto, plus PierPressure under the `full` profile.

## Goals / Non-Goals

**Goals:**

- One dashboard YAML block that works when pasted, apart from the pier id, and reads only published entities and attributes.
- Keep the JavaScript inside the YAML short and readable, so a reader can follow it and the guard test can check it.
- A Home Assistant check that someone can repeat when the YAML changes, and that never touches a real installation.

**Non-Goals:**

- No change to the core, the delivery adapter, the entities or the verdict document.
- No bespoke card (#132) and no Markdown fallback (#137).
- No CI job that boots Home Assistant. The Docker check is run by hand.
- No change to the apexcharts-card example in `docs/night-timeline.md`.
- No styling for light and dark themes beyond a palette that reads on both.

## Test Seams

- **Primary test seam:** a new pytest module, `tests/test_night_dashboard_doc.py`. It reads the YAML block from `docs/night-dashboard.md`, and compares it with what the MQTT adapter's public builders publish for a document from `make_document`. It covers the content scenarios of the spec: the YAML parses, only allowed card types, every entity id and attribute exists, the row order, the lanes and the cards present.
- **Existing seams reused:** `make_document` from `tests/conftest.py`, and the public discovery and attribute builders in `pierpressure/delivery/mqtt.py`, which `tests/test_discovery.py` already drives.
- **Manual seam:** the Docker check, for the rendering scenarios: gaps, shading, span, lines, lanes, the offline behaviour and the screenshot. Like `ha-delivery`, Home Assistant's own drawing is confirmed by a documented check, not asserted as if PierPressure produced it.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. No runtime code changes, but the dashboard holds JavaScript that CI never runs, and the guard test sits on the adapter's public surface.
- **Blast radius:** `docs/` (a new page and an image), links in `README.md` and `docs/night-timeline.md`, one new test module, and a dev-only Docker check. Nothing in `pierpressure/` changes.

## Decisions

### DD1. The strip is one plotly-graph-card with one heatmap trace per row

Nine `type: heatmap` traces share one category y-axis. Each is an `entity: ""` trace whose `x` and `z` come from `$ex` reading `hass.states[<id>]?.attributes?.forecast ?? []`. Each row has its own colour scale and range, so a row in km/h and a row from 0 to 1 can share the strip. The row order comes from the trace order, with the y-axis reversed so that Sun altitude is on top.

- *Alternative: one heatmap with a 9-row `z` matrix.* That gives one colour scale for every row, which cannot shade % and km/h and 0 to 1 on the same ramp, nor reverse Seeing and Transparency.
- *Alternative: `entity: <id>` with `attribute: forecast`.* That fetches the attribute's history from the recorder, which readers are told to switch off, and history is not what the strip shows.

A heatmap cell is centred on its `x`, but `datetime` is the start of the hour. So `x` is shifted by 30 minutes, which makes each cell cover its hour. Plotly draws a null `z` as a transparent cell, which gives the gap the spec asks for without extra code.

### DD2. Shading maps each row onto one shared seven-step ramp

The palette is the mock's seven blues, `#cde2fb` to `#0d366b`. Each row maps its value to the ramp with the mock's rules: cloud rows from 0 to 100 %; Wind gust from 0 to 49 km/h, clamped; Seeing and Transparency as `1 − value`, so poorer is darker; Sun altitude in twilight bands (above 0°, 0 to −6°, −6 to −12°, −12 to −18°, below −18°); Moon altitude lightest at or below 0°, then darker every 6°. The mapping is in each trace's `$ex` and gives a band index, and `zmin`, `zmax` and a stepped colour scale turn the index into a colour. The hover text shows the real value with its unit, not the band index.

- *Alternative: continuous colour scales.* They are simpler, but they lose the twilight bands that make the Sun row readable, and they don't match the reference rendering.

### DD3. Lanes are horizontal bar traces under the heatmap

The "Moon up" lane and one lane per available target are `type: bar` traces with `orientation: h`. Each bar has `base` at the start as a `Date`, and `x` as the duration in milliseconds. That is plotly's Gantt pattern on a date axis. Labels are the bar's `text`, drawn inside the bar. The lanes sit on a second y-axis, in the lower part of the plot's height, so they share the x-axis with the heatmap without mixing with its rows. Moon-up runs come from the Moon altitude forecast: each run of consecutive hours above 0° becomes one bar, from the start of its first hour to the end of its last hour. An unavailable rank, or one without a `window`, gives no trace, so it leaves no lane.

- *Alternative: layout shapes with annotations.* Shapes on a category axis need numeric positions and their own label code, and get no hover. Bars give both for free.

### DD4. Dusk, dawn and now are layout shapes

Three vertical lines are layout `shapes` with `xref: x` and `yref: paper`, each with an annotation as its label. Dusk and dawn come from the Verdict's `dark_window`, and are left out when either is null. "Now" is `new Date()`. The card sets `refresh_interval: 300`, so the now line moves every five minutes. The card makes no history requests, so polling costs only a re-render.

### DD5. The time span uses the card's own relative window

The top-level `hours_to_show` and `time_offset` are computed by `$ex` from `dark_window`. `hours_to_show` is the time from `start − 4 h` to `end + 5 h`. `time_offset` is the time from now to `end + 5 h`. When `dark_window` is null, they fall back to `24h` and `18h`, which is 6 hours back and 18 hours ahead. `time_zone: server` shows the axis in Home Assistant's time zone (D9).

- *Alternative: set `layout.xaxis.range` directly.* That is plain plotly, but it competes with the card's own range handling, which the README documents only for y-axes. The relative window is the card's own mechanism. If the Docker check shows that `$ex` is not evaluated for `hours_to_show`, the build falls back to `layout.xaxis.range`. The spec does not change either way.

### DD6. The other cards are core cards

- **Tonight card:** a `markdown` card. Jinja reads `state_attr('sensor.pierpressure_backyard_verdict', …)` for `verdict`, `score`, `confidence`, `dark_window` and `reasons`, and lists the reasons as bullets.
- **Moon card:** a `markdown` card reading `moon` from the Verdict, with illumination as a percentage, the phase, and rise and set.
- **Target table:** an `entities` card listing Target 1 to Target 10. Unavailable ranks show as unavailable, which is the published meaning.
- **Health chips:** a `heading` card with one entity badge for each health sensor.

The view is a `sections` view: tonight and the moon first, the strip at full width, then targets and health.

- *Alternative: community cards such as Mushroom chips.* They look better, but each one is another HACS install for the reader.

### DD7. The guard test pairs every attribute read with its entity

The test takes the only ```` ```yaml ```` fence in `docs/night-dashboard.md` as the dashboard. It walks the parsed tree, so it reaches cards nested in stacks, grids and sections:

- **Card types:** every `type` must be in a fixed list of core card types the dashboard uses, or be `custom:plotly-graph-card`.
- **Entity ids:** every `sensor.pierpressure_backyard_<x>` string, found by a regular expression over all scalar strings, including those inside `$ex` and Jinja, must be an entity the adapter announces. The test builds that set from the discovery builders for pier `backyard`, as the device name `PierPressure backyard` plus the entity name, slugged the way Home Assistant does.
- **Attribute reads:** the YAML reads attributes in three forms only: Jinja `state_attr('<id>', '<key>')`, JavaScript `.attributes?.<key>` or `.attributes.<key>`, and an `entities` row with `type: attribute`. A Jinja or `entities` read names its entity, so the test checks that pair. For a JavaScript read, the test requires the key to be published by **every** PierPressure entity named in the same expression. The YAML therefore keeps each `$ex` to one kind of entity: the nine timeline sensors, the ten Target sensors, or the Verdict. The test fails and names the entity and key when a read is not published.
- **Published keys:** the keys of each attributes payload that the adapter's attribute builders produce for a `make_document` document in which all ten ranks hold a target, so `window` is present.

It also checks the strip's nine row names in order, the presence of the lane traces, and the cards the spec lists.

- *Alternative: execute the JavaScript in a JS engine against fake states.* That is stronger, but it adds a Node or JS-engine dependency to the Python test suite for one docs page. The Docker check covers the rendering.

### DD8. The Docker check is a dev-only compose profile and a mise task

A `dashboard` profile in `compose.yaml` adds a `homeassistant` container (the official image, pinned by tag) beside mosquitto and PierPressure. A mise task, `dashboard-check`, does four things. It prepares a throwaway Home Assistant config under `.workspace/dashboard-check/`, with plotly-graph-card's release file in `www/` and the dashboard YAML in a YAML-mode dashboard. It brings up the stack. It completes onboarding and adds the MQTT integration through Home Assistant's onboarding and config-flow APIs. Then it prints the URL and the login. The person running it opens the dashboard and takes the screenshot. Committing the harness means the check can be repeated when the YAML changes.

- *Alternative: a one-off manual check with nothing committed.* That is less to maintain, but the screenshot then depends on steps no one can repeat.

### DD9. The page shows a pinned plotly-graph-card version

The page says which plotly-graph-card version and which Home Assistant version the YAML was checked against: the ones the Docker check used. Readers then know what "works" means if a later release breaks it.

## Risks / Trade-offs

- [The JavaScript in the YAML is never run in CI] → Keep each `$ex` short and of one kind (DD7). The guard test catches renamed entities and attributes. The Docker check covers the rendering, and is repeatable (DD8).
- [plotly-graph-card changes its API in a later release] → The page names the checked version (DD9). The dashboard uses only documented features: `$ex`, `entity: ""`, `time_zone` and plain plotly traces.
- [`$ex` may not be evaluated for top-level `hours_to_show` and `time_offset`] → Check this first in the Docker check, and fall back to `layout.xaxis.range` (DD5).
- [A dashboard opened offline shows card errors] → Every read uses `?.` and `?? []`, so missing attributes give an empty strip. The Docker check stops PierPressure and looks for card errors.
- [Automating Home Assistant onboarding and the MQTT config flow can break between Home Assistant releases] → Pin the Home Assistant image tag. The harness is dev-only and run by hand, so a break costs a fix, not a failed release.
- [The screenshot goes stale when the YAML changes] → The page names the versions it shows, and the harness makes a new screenshot cheap. The guard test cannot see the image, so a reviewer checks it whenever the YAML changes.
- [Ten target lanes make the strip tall on a phone] → Each lane is thin, and empty ranks leave no lane (D4). Accepted.

## Migration & Rollback

N/A. Nothing published changes shape. Rolling back is reverting the commits; readers who pasted the YAML keep a working dashboard, because it reads only existing entities.
