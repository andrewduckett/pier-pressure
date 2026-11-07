## Why

Home Assistant hides an unavailable entity's attributes, and a timeline sensor
can have no forecast. Today the card then draws a row with only its label, and a
night with no astronomical darkness moves the axis to a day around now without
saying why. The viewer cannot tell a broken sensor from a clear sky (#132,
Should). The card tolerates missing data by design, so each missing case needs
a defined look.

## What Changes

- The offline message and the "No PierPressure verdict found" message stay as
  they are (D3, D4).
- A row that would draw no cell says why in its track: "Not found",
  "Unavailable" or "No forecast" (D5, D6). Hovering over the message names the
  entity id and the cause (D7). A row with some cells keeps its blank hours.
- The Moon up lane says the same as the Moon altitude row when that row has no
  cell (D8). The target lanes do not change (D9).
- When the Verdict sensor's `dark_window` has a null `start` and `end`, the card
  shows the note "No astronomical darkness tonight" above the strip. The strip
  still draws on its fallback axis (D10). A missing or unreadable `dark_window`
  shows no note (D11).
- `docs/night-card.md` describes the row messages and the darkness note, and
  its "If something looks wrong" section covers each missing case (D13).

Nothing in the core, the verdict document or the MQTT delivery changes, and no
version attribute is added (D14).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the requirements that leave a row or the Moon up lane empty
  for a missing, unavailable or forecastless sensor now say what the row or
  lane shows instead. New requirements add the darkness note and the
  troubleshooting docs.

## Impact

- Changed: `card/src/strip.ts` (why a row or the Moon up lane is empty),
  `card/src/pierpressure-card.ts` (drawing the row messages and the darkness
  note), `card/test/` (tests and harness helpers), `docs/night-card.md` and
  `tests/test_night_card_doc.py`.
- No new dependencies.
- No change to `mise.toml`, CI, the release or `scripts/dashboard_check.py`
  (D16).
