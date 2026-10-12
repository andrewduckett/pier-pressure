## Why

The add-on makes some setting checks of its own, which repeat or replace the
core's checks. For example, the add-on rejects `horizon_points` that is not text
or not valid YAML. Its spec explains this by saying the service "does not rely
on the Supervisor's check."

We want a stronger rule: the core validates every setting, from every
interface. Then the Supervisor's check does not matter. The add-on keeps less
code. Users of every install get the same check, and an error that names the
same setting.

Story: #83 `addon-options-core-validates`.

## What Changes

- **The core reads horizon points written as text.** `horizon.points` accepts
  YAML text, such as `"[[0, 10], [90, 20]]"`, as well as a list. The core
  parses the text when it validates the pier. The pier fails, with an error that
  names `horizon.points`, when the text:
  - cannot be parsed
  - does not hold a list of points
  - holds nothing, such as empty text or only a comment

  A list still works as before.
- **The add-on only renames the horizon fields.** `horizon_points` becomes
  `horizon.points`, and `min_altitude` becomes `horizon.min_altitude`. The
  add-on does not parse or type-check either value.
- **The add-on passes on any value it does not expect** in the settings the
  form declares, and the core rejects it. The add-on reads only those settings
  and ignores any other top-level key, as the Supervisor does. This covers:
  - a pier entry that is not a mapping (passed on today)
  - an `mqtt` value that is not a mapping (passed on today)
  - a pier that holds an `equipment` value beside the `equipment_*` fields. The
    add-on leaves the set `equipment_*` fields in place, and the core rejects
    them as fields it does not know. The add-on writes no error of its own.
  - a pier that holds a `horizon` value beside `min_altitude` or
    `horizon_points`. The add-on leaves the set horizon fields in place, and
    the core rejects them as fields it does not know. Today the add-on silently
    replaces the `horizon` value.
- **The add-on no longer drops a pier.** Every form pier reaches the core, which
  logs and skips a bad one as it does for a file pier.
- **The add-on removes its own setting checks and their tests:**
  `horizon_points` must be text, `horizon_points` must be valid YAML, and the
  error for an `equipment` value beside the `equipment_*` fields.
- **The add-on keeps the checks it needs to do its job.** These check the shape
  it needs to run, not whether a setting is valid:
  - `options.json` is valid JSON and holds a mapping.
  - Its `piers` is a list, because the add-on loops over it.
  - A `config.yaml` pier is a mapping with a text `id`, because the add-on
    matches form piers to file piers by `id`.
  - A setting given on the form and in `config.yaml` is an error. This rule is
    about combining two sources, which only the add-on has.
- **`ha-addon/DOCS.md` says that an error about `horizon.points` refers to the
  form's `horizon_points` field.**
- **An ADR records the rule:** the core is the only place that validates
  settings, whatever the interface. An interface layer reads, renames and
  combines settings. For the settings it reads, it passes on any value it does
  not expect.

Out of scope:

- New rules in the core. The core already enforces one horizon source, complete
  equipment, positive values and value ranges.
- The rule about a partial broker connection, which #72 moved onto `ConfigFile`.
- Hiding secrets in configuration errors, which #89 did.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `horizon-mask`: inline points may be written as YAML text, which the core
  parses. Text that cannot be parsed or holds no list of points makes the pier
  invalid.
- `ha-addon`: the core makes every setting check. The Supervisor's save check is
  a convenience, not a guarantee. A bad `horizon_points` gives an error that
  names `horizon.points`. An `equipment` value beside the `equipment_*` fields is
  rejected by the core as unknown `equipment_*` keys.

## Impact

- **Changed files:**
  - `pierpressure/core/config.py`: `HorizonConfig` parses text in `points`.
  - `pierpressure/addon_options.py`: `_with_horizon_block` only renames and
    leaves a pier with a `horizon` value unchanged, `_with_equipment_block`
    leaves a pier with an `equipment` value unchanged,
    and `_config_piers` no longer drops a pier.
  - `pierpressure/addon_settings.py`: docstrings that describe a pier the
    translation skipped.
  - `ha-addon/DOCS.md`: one line about `horizon.points`.
  - `docs/decisions/`: a new ADR.
- **Tests:** new core tests for horizon text. The add-on tests for its removed
  checks are replaced by tests that show the core's error.
- **Changed error text:** a bad `horizon_points` now gives the core's error,
  which names `horizon.points`, not `horizon_points`. An `equipment` value
  beside the `equipment_*` fields gives an unknown-field error that names each
  `equipment_*` key, not `equipment`. A `horizon` value beside the horizon
  fields now fails the pier, with an unknown-field error that names each set
  horizon field.
- **Unchanged:** the add-on's form, the verdict document, MQTT topics,
  entities and entity mapping.
