## Why

The card shows tonight's verdict, but not why. Cloud decides most nights, so the
first thing the card's night strip needs is the four cloud rows, hour by hour,
across the judged night. Every later drawing story in epic #132 adds to the
same time axis.

## What Changes

- Below the verdict, score and confidence, the card draws a night strip with a
  time axis and four rows: Cloud cover, Cloud low, Cloud mid and Cloud high
  (D3, D5). It shows only when the verdict does.
- The axis runs from 4 hours before dusk to 5 hours after dawn, from the
  Verdict sensor's `dark_window`. On a night with no astronomical darkness it
  falls back to 6 hours before now to 18 hours after, as the YAML strip does
  (D4). Labels every 3 hours, in Home Assistant's time zone, on a 24-hour clock
  (D10, D11).
- Each row reads its cloud sensor's `forecast` attribute. Each value is one
  hour's cell, shaded in the YAML strip's seven blues from clear to overcast
  (D6, D7).
- A null or absent hour is a blank cell. A missing or unavailable cloud sensor
  leaves an empty, labelled row; the card never throws (D8).
- Hovering over a cell shows the row, the hour and the value (D9).
- `docs/night-card.md` describes the cloud rows (D14).

Nothing in the core, the verdict document or the MQTT delivery changes. Dusk,
dawn, moon and "now" marks, and the other condition rows, are later stories.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the card gains a night strip with a time axis and the four
  cloud rows, and the docs describe it. Existing requirements stay as they are.

## Impact

- Changed: `card/src/` (the strip and the cloud entity ids), `card/test/`
  (strip tests and harness helpers), `docs/night-card.md`.
- No new dependencies.
- No change to `mise.toml`, CI, the release or `scripts/dashboard_check.py`:
  the dashboard check already shows the locally built card (D15).
