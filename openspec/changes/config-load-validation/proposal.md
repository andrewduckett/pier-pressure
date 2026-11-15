## Why

PierPressure can load a pier with settings the user did not write, and log
nothing. A zero-padded horizon azimuth such as `045` is read as the octal
number 37 (#81), and two piers that share an `id` both publish to the same MQTT
topics, so one verdict silently overwrites the other (#86). Both errors happen
while the core loads the piers, so one change fixes both (D1).

## What Changes

- A zero-padded integer, such as `045` or `-045`, is read as a decimal number
  (D2). A base-60 value, such as `1:30`, is read as text, not as a number, so a
  horizon point that holds one is rejected and its pier skipped (D3).
- The rule applies to every value in `config.yaml`, in every install type, and
  to horizon points written as text, such as the add-on form's **Horizon
  points** field (D4). No other way YAML reads a value changes (D5).
- **BREAKING**, in a narrow case: a number setting written in base-60 form,
  such as `go_threshold: 1:05`, used to load as 65 and now skips its pier (D3).
  A text setting such as `id: 08` keeps working (D6).
- A pier `id` that appears more than once in the piers list stops startup with
  a configuration error that names the id (D7, D8, D11). Ids that differ only
  in letter case stay distinct (D9).
- The add-on's Configuration tab gets the repeated-id rule from the core. The
  add-on's own check of its `config.yaml` stays (D10).
- The README's configuration table states both rules (D12).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: configuration loading adds two rules. A repeated pier id is
  a configuration error that stops startup, and a zero-padded integer anywhere
  in the configuration file is read as a decimal number.
- `horizon-mask`: inline points, as a list or as text, read a zero-padded
  azimuth as a decimal number and reject a base-60 value.
- `ha-addon`: a pier id repeated on the Configuration form stops the add-on.

## Impact

- Code: `pierpressure/core/config.py` (the YAML reader used by
  `read_config_mapping` and `HorizonConfig`; the piers-list check in
  `build_config`). `pierpressure/addon_options.py` and
  `pierpressure/addon_settings.py` need no new rule, only tests that the form
  reaches it.
- Docs: `README.md` configuration table.
- Delivery surface: unchanged. No topic, entity or verdict field changes.
- Dependencies: none. The reader stays PyYAML's safe loader, with its number
  rules adjusted.
