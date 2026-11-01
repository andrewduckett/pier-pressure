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

The palette is the mock's seven blues, `#cde2fb` to `#0d366b`. Each row maps its value onto the ramp with the mock's rules:

- **Cloud cover, low, mid and high:** 0 to 100 %.
- **Wind gust:** 0 to 49 km/h, clamped.
- **Seeing and Transparency:** `1 − value`, so poorer is darker.
- **Sun altitude:** twilight bands: above 0°, 0 to −6°, −6 to −12°, −12 to −18°, and below −18°.
- **Moon altitude:** lightest at or below 0°, then one step darker every 6°.

Each trace's `$ex` turns the value into a band index. Then `zmin`, `zmax` and a stepped colour scale turn the index into a colour. The hover text shows the real value with its unit, not the band index.

- *Alternative: continuous colour scales.* They are simpler, but they lose the twilight bands that make the Sun row readable, and they don't match the reference rendering.

### DD3. Lanes are horizontal bar traces under the heatmap

The "Moon up" lane and one lane per available target are `type: bar` traces with `orientation: h`. Each bar has `base` at the start as a `Date`, and `x` as the duration in milliseconds. That is plotly's Gantt pattern on a date axis. Labels are the bar's `text`, drawn inside the bar. The lanes sit on a second y-axis, in the lower part of the plot's height, so they share the x-axis with the heatmap without mixing with its rows. Moon-up runs come from the Moon altitude forecast: each run of consecutive hours above 0° becomes one bar, from the start of its first hour to the end of its last hour. An unavailable rank, or one without a `window`, gives no trace, so it leaves no lane.

Plotly shares a fixed axis domain among however many categories it has, so two lanes would be drawn far thicker than ten. To keep every lane the same thickness, `$ex` computes the card's `layout.height` and the split between the heatmap's domain and the lanes' domain from the number of lanes. Each lane gets a fixed height of about 18 px, and the heatmap keeps its own fixed height.

- *Alternative: layout shapes with annotations.* Shapes on a category axis need numeric positions and their own label code, and get no hover. Bars give both for free.

### DD4. Dusk, dawn and now are layout shapes

Three vertical lines are layout `shapes` with `xref: x` and `yref: paper`, each with an annotation as its label. Dusk and dawn come from the Verdict's `dark_window`, and are left out when either is null. "Now" is `new Date()`. The card sets `refresh_interval: 300`, so the now line moves every five minutes. The card makes no history requests, so polling costs only a re-render.

### DD5. The time span is an absolute x-axis range

`layout.xaxis.range` is set by `$ex` to two `Date` objects: `dark_window.start − 4 h` and `dark_window.end + 5 h`. Tonight is a fixed pair of instants, so an absolute range neither drifts as the card refreshes nor depends on where now falls. When `dark_window` is null, the range is `now − 6 h` to `now + 18 h`, recomputed on each refresh. `time_zone: server` shows the axis in Home Assistant's time zone (D9).

The card also draws the x-axis from its own relative window, `hours_to_show` and `time_offset`. The README does not say whether an explicit x-axis range overrides it. So the first build step checks this in the Docker check, with the afternoon case, where the whole range is still in the future.

- *Alternative: compute `hours_to_show` and `time_offset` from `dark_window`.* That is the card's own mechanism. But before dusk the range starts in the future, so `time_offset` exceeds `hours_to_show`, which the README never describes. And unless both are recomputed on every refresh, the range slides with the clock. It is the fallback if the Docker check shows that the card overrides an explicit range. The spec does not change either way.

### DD6. The other cards are core cards

- **Tonight card:** a `markdown` card. Jinja reads `state_attr('sensor.pierpressure_backyard_verdict', …)` for `verdict`, `score`, `confidence`, `dark_window` and `reasons`, and lists the reasons as bullets.
- **Moon card:** a `markdown` card reading `moon` from the Verdict, with illumination as a percentage, the phase, and rise and set.
- **Target table:** an `entities` card listing Target 1 to Target 10. Unavailable ranks show as unavailable, which is the published meaning.
- **Health chips:** a `heading` card with one entity badge for each health sensor.

The view is a `sections` view: tonight and the moon first, the strip at full width, then targets and health.

- *Alternative: community cards such as Mushroom chips.* They look better, but each one is another HACS install for the reader.

### DD7. The guard test pairs every attribute read with its entity

The test takes the only ```` ```yaml ```` fence in `docs/night-dashboard.md` as the dashboard. It walks the parsed tree, so it reaches cards nested in stacks, grids and sections:

- **Card types:** every `type` must be in a fixed list of core card types the dashboard uses, or be `custom:plotly-graph`.
- **Entity ids:** every `sensor.pierpressure_backyard_<x>` string, found by a regular expression over all scalar strings, including those inside `$ex` and Jinja, must be an entity the adapter announces. The test builds that set from the discovery builders for pier `backyard`, as the device name `PierPressure backyard` plus the entity name, slugged the way Home Assistant does.
- **Attribute reads:** the YAML reads attributes in three forms only: Jinja `state_attr('<id>', '<key>')`, JavaScript `.attributes?.<key>` or `.attributes.<key>`, and an `entities` row with `type: attribute`. A Jinja or `entities` read names its entity, so the test checks that pair. For a JavaScript read, the test requires the key to be published by **every** PierPressure entity named in the same expression. The YAML therefore keeps each `$ex` to one kind of entity: the nine timeline sensors, the ten Target sensors, or the Verdict. The test fails and names the entity and key when a read is not published.
- **Published keys:** the keys of each attributes payload for a `make_document` document in which all ten ranks hold a target, so `window` is present. For the timeline, Target and health sensors, they come from the adapter's public builders: `timeline_attributes`, `rank_target_attributes` and `health_attributes`. The Verdict has no builder of its own. The adapter publishes `document.model_dump_json(exclude={"timeline"})` inline (`pierpressure/delivery/mqtt.py`, in the publish path). So the test takes the Verdict's keys from the same call. The adapter does not change.

It also checks the strip's nine row names in order, the presence of the lane traces, and the cards the spec lists.

- *Alternative: execute the JavaScript in a JS engine against fake states.* That is stronger, but it adds a Node or JS-engine dependency to the Python test suite for one docs page. The Docker check covers the rendering.

### DD8. The Docker check is a dev-only compose profile and a mise task

A `dashboard` profile in `compose.yaml` adds a `homeassistant` container (the official image, pinned by tag) beside mosquitto and PierPressure. A mise task, `dashboard-check`, does four things. It prepares a throwaway Home Assistant config under `.workspace/dashboard-check/`, with every `.js` file of the pinned plotly-graph-card release in `www/plotly-graph-card/`, as the card's manual install steps say, and the dashboard YAML in a YAML-mode dashboard. It brings up the stack. It completes onboarding and adds the MQTT integration through Home Assistant's onboarding and config-flow APIs. Then it prints the URL and the login. The person running it opens the dashboard and takes the screenshot. Committing the harness means the check can be repeated when the YAML changes.

- *Alternative: a one-off manual check with nothing committed.* That is less to maintain, but the screenshot then depends on steps no one can repeat.

### DD9. The page shows a pinned plotly-graph-card version

The page says which plotly-graph-card version and which Home Assistant version the YAML was checked against: the ones the Docker check used. Readers then know what "works" means if a later release breaks it.

## Risks / Trade-offs

- [The JavaScript in the YAML is never run in CI] → Keep each `$ex` short and of one kind (DD7). The guard test catches renamed entities and attributes. The Docker check covers the rendering, and is repeatable (DD8).
- [plotly-graph-card changes its API in a later release] → The page names the checked version (DD9). The dashboard uses only documented features: `$ex`, `entity: ""`, `time_zone` and plain plotly traces.
- [The card may override an explicit `layout.xaxis.range` with its own relative window] → Check this first in the Docker check, before dusk, and fall back to `hours_to_show` and `time_offset`, recomputed on every refresh (DD5).
- [A dashboard opened offline shows card errors] → Every read uses `?.` and `?? []`, so missing attributes give an empty strip. The Docker check stops PierPressure and looks for card errors.
- [Automating Home Assistant onboarding and the MQTT config flow can break between Home Assistant releases] → Pin the Home Assistant image tag. The harness is dev-only and run by hand, so a break costs a fix, not a failed release.
- [The screenshot goes stale when the YAML changes] → The page names the versions it shows, and the harness makes a new screenshot cheap. The guard test cannot see the image, so a reviewer checks it whenever the YAML changes.
- [Ten target lanes make the strip tall on a phone] → Each lane is thin, and empty ranks leave no lane (D4). Accepted.

## Migration & Rollback

N/A. Nothing published changes shape. Rolling back is reverting the commits; readers who pasted the YAML keep a working dashboard, because it reads only existing entities.
