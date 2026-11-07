## Why

The card's night strip shows the cloud forecast, but not when the night is
dark, so a viewer cannot tell which cloudy hours matter. Darkness on the same
axis is the minimum the card needs to replace the YAML strip (#132, Must).

## What Changes

- A **Sun altitude** row at the top of the strip, above Cloud cover. Each hour
  is shaded by the sun's altitude, in steps through civil, nautical and
  astronomical twilight, darkest in astronomical night (D3 to D6).
- A **Moon up** lane under the cloud rows. It has one grey bar for each run of
  hours when the moon is above the horizon (D7 to D10).
- **Dusk and dawn lines**: dashed grey lines at the ends of the Verdict
  sensor's `dark_window`. The card draws them only when the axis comes from that
  window (D11).
- A **now line**: a red line at the browser's current time, drawn while that
  time is on the axis. It moves every minute on the card's own timer (D12,
  D13, D16).
- The three lines cross the rows and the lane. Hovering over a line shows its
  name and time (D14, D15).
- `docs/night-card.md` describes the new row, the lane and the lines (D18).

Nothing in the core, the verdict document or the MQTT delivery changes. The
Moon altitude row and the moon drawing are later stories.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the strip gains the Sun altitude row, the Moon up lane, and
  the dusk, dawn and now lines, and the docs describe them. The card's height
  grows to fit. Existing requirements keep their meaning.

## Impact

- Changed: `card/src/` (the strip model and the card's rendering and timer),
  `card/test/` (strip tests and harness helpers), `docs/night-card.md` and
  `tests/test_night_card_doc.py`.
- No new dependencies.
- No change to `mise.toml`, CI, the release or `scripts/dashboard_check.py`:
  the dashboard check already shows the locally built card (D19).
