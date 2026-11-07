## Why

The card's strip shows only the sun and the cloud, while the YAML strip it
replaces shows nine rows. A viewer who installs the card loses the moon, wind,
seeing and transparency rows, so the card cannot yet replace the YAML strip
(#132, Must).

## What Changes

- Ten rows join the strip, one per timeline sensor it lacks: Moon altitude,
  Wind gust, Seeing, Transparency, Temperature, Dew point, Humidity, Wind
  speed, Wind direction and Rain chance (D3, D5). The strip then has fifteen
  rows and the Moon up lane.
- The rows run in the YAML strip's order, then the new ones. Moon altitude
  sits between Sun altitude and Cloud cover, so the cloud rows move down one
  (D4).
- Moon altitude, Wind gust, Seeing and Transparency take the YAML strip's
  shades. For Seeing and Transparency, darker means worse (D7).
- Temperature and Dew point share one scale in 5 °C steps, so matching shades
  show an hour near the dew point. Humidity and Rain chance step like cloud,
  and Wind speed like Wind gust (D8, D9).
- A Rain chance value fills the hour before its time, because that is the
  hour its chance is for (D6).
- Wind direction shows an arrow per hour, pointing the way the wind blows to
  (D10).
- Hovering over any cell shows the sensor's unit, and for Wind direction also
  an 8-point compass name (D11).
- A missing, unavailable or null sensor leaves its row labelled and blank, as
  for the cloud rows (D13). The dusk, dawn and now lines cross every row (D14).
- `docs/night-card.md` describes every row (D17).

Nothing in the core, the verdict document or the MQTT delivery changes. The
card gets no option to choose its rows (D15).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the strip's row requirements widen from the cloud rows to every
  row, the cloud rows move below a new Moon altitude row, and new requirements
  give the added rows their shades, the Rain chance hour, the wind arrows and
  their hover text. The docs requirement grows to cover every row.

## Impact

- Changed: `card/src/strip.ts` (the row list, shades and the Rain chance hour),
  `card/src/pierpressure-card.ts` (the wind arrows and the card's height),
  `card/test/` (strip tests and harness constants), `docs/night-card.md` and
  `tests/test_night_card_doc.py`.
- No new dependencies.
- No change to `mise.toml`, CI, the release or `scripts/dashboard_check.py`:
  the dashboard check already shows the locally built card (D18).
