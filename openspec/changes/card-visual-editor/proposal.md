## Why

Today the only way to set up the PierPressure card is to type its `pier` key in
YAML, and to know the pier's id. An adopter who never edits card YAML should be
able to add the card from Home Assistant's card picker, see a preview, and pick
the pier from a list.

## What Changes

- The card gets a visual editor with one field, **Pier**. It lists every pier
  whose Verdict sensor Home Assistant has (D3), sets a `pier` value that finds
  that sensor (D4), and keeps every other configuration key (D9).
- The editor keeps a configured pier that is not in the list (D6), accepts a
  typed pier (D7), and says so when it finds no pier at all (D8).
- The card's entry in the card picker asks for a preview. The card offers a
  starting configuration with the first listed pier, or with no pier when none
  is found (D10, D11).
- `docs/night-card.md` says how to add the card with the picker and the editor,
  with YAML as the other route (D13).

No new data: the Verdict sensor already carries the pier id (D2).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the card registers with a picker preview and a starting
  configuration, has a visual editor that sets `pier`, and its docs describe
  the editor.

## Impact

- Code: `card/src/` (a new editor element, the card's picker entry and its
  starting configuration) and `card/test/`.
- Docs: `docs/night-card.md`.
- No change to the core, the verdict document, MQTT delivery, the add-on or the
  YAML dashboard. No new dependency: the card already bundles Lit.
