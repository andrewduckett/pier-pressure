## Why

A pier on the add-on's Configuration tab opens in one dialog of 13 fields with
nothing to show where one topic ends and the next begins. That makes "Describe
my site" the hardest part of setup. Andrew tried a flat, a grouped and a
labelled flat layout in real Home Assistant, and chose the labelled flat one
(D14).

## What Changes

- Each pier field's label names its section: Location, Horizon, Equipment or
  Verdict, as in "Horizon: floor". The Pier ID stays first, with no prefix
  (D15).
- The first field of each section opens its help text with a one-sentence
  introduction to the section (D16).
- Every pier field's help text is rewritten to explain the field more fully.
  Each number still names its unit or says it has none (D9).
- The field names, their order, their types and the save checks stay as they
  are. The service, saved settings and every verdict are unchanged (D17).
- The `ha-addon` spec stops saying a form cannot nest a block inside a pier,
  because the Supervisor allows it now. The flat names are a choice made after
  the trial (D18).
- `DOCS.md` uses the new labels where it names a pier field (D12).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the requirement "The add-on offers a Configuration form for the
  interval and piers" gains section-prefixed labels and section introductions.
  It also gives the flat field names a new reason.

## Impact

- `ha-addon/translations/en.yaml`: the pier field names and descriptions.
- `ha-addon/DOCS.md`: the label tables that name pier fields.
- `tests/test_ha_addon.py`: the label checks.
- `docs/decisions/`: a new decision record on keeping the pier fields flat.
- No change to `ha-addon/config.yaml`, `pierpressure/`, the verdict document or
  the MQTT entities.
