## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required
behaviour. This design covers how four flat form fields become a pier's
equipment without changing the core or the `config.yaml` format.

Facts that shape the approach:

- **The edge already rebuilds nested blocks.** The edge is the code outside the
  pure core that reads the add-on's form. `pierpressure/addon_options.py` turns `/data/options.json` into the mapping a `config.yaml` would hold
  (ADR-0020). It already moves each pier's flat `min_altitude` and
  `horizon_points` into a `horizon` block (addon-form-horizon D1).
- **The core already has every equipment rule.** `Equipment` in
  `pierpressure/core/config.py` requires focal length, sensor width and sensor
  height. It makes each value, and the optional reducer, strictly positive, and
  it defaults the reducer to 1.0. It forbids unknown keys.
- **The core already skips a bad pier.** `validate_piers` logs a pier that fails
  validation with `Skipping invalid pier %r: %s`, and keeps the others. The
  message holds the validation error, which names the failing key by its path,
  such as `equipment.sensor_height_mm`.
- **`PierConfig` forbids unknown keys.** A pier that still holds an
  `equipment_*` key when it reaches the core fails its check.
- **The form cannot nest an `equipment` block.** Home Assistant allows options
  nested at most two levels deep. `piers` and its items already use both.

## Goals / Non-Goals

**Goals:**

- The core and its equipment rules stay unchanged. Form equipment passes the
  same checks as file equipment.
- One pier's bad equipment never stops the other piers.

**Non-Goals:**

- Form-specific wording for the core's error messages.
- A check on save that the three required fields are set together. The
  Supervisor's schema cannot express "all or none".

## Decisions

### D1. The edge rebuilds each pier's `equipment` block

For each pier, `read_addon_options` removes the four `equipment_*` fields and
puts the ones that are set into an `equipment` block. Each key loses its
`equipment_` prefix:

```
form pier                                  config-shaped pier
{"id": "backyard", ...,                    {"id": "backyard", ...,
 "equipment_focal_length_mm": 400,  -->     "equipment": {"focal_length_mm": 400,
 "equipment_sensor_width_mm": 23.5,                       "sensor_width_mm": 23.5,
 "equipment_sensor_height_mm": 15.7}                      "sensor_height_mm": 15.7}}

{"id": "backyard", ...}             -->    {"id": "backyard", ...}
```

The edge removes only these four names. Any other key passes through, and the
core rejects it as unknown.

- *Why:* the core keeps one copy of every equipment rule and gains no form
  names. This is the horizon pattern again.
- *Alternative:* a general rule that turns any `<block>_<key>` field into a
  nested block. Rejected: `elevation_m` and `interval_seconds` would need
  exceptions, and a typo would build a block the user never meant.

### D2. Incomplete equipment is left to the core

The edge builds the block from whichever fields are set, and does not check that
all three required fields are there. The core's `Equipment` check then rejects
an incomplete block, and `validate_piers` skips the pier. Its log line names the
missing key:

```
Skipping invalid pier 'backyard': 1 validation error for PierConfig
equipment.sensor_height_mm
  Field required ...
```

When every pier is skipped, `build_config` raises its usual "No valid pier"
`ConfigError`, and the add-on stops.

- *Why:* a file pier with incomplete equipment fails the same way, so both
  sources follow one rule. This replaces the story's wording, which asked for a
  startup error. The user chose the skip in exploration.
- *Alternative:* stop the service from the edge. Rejected: one incomplete pier
  would stop every other pier, unlike any other bad pier field.
- *Alternative:* check completeness at the edge, with an error that uses the form
  names. Rejected: it copies a core rule into a second place (see Risks).

### D3. Unset values

A field that is absent or `null` is unset. The edge does no other type work on
the four fields. A saved value of the wrong type goes into the block unchanged,
and the core checks it under the file's rules. Those rules turn numeric text,
such as `"400"`, into a number, as they do for `config.yaml`, and reject other
text. Unlike `horizon_points`, these fields are numbers, so there is no blank
text to handle.

### D4. The manifest's equipment fields

```yaml
schema:
  piers:
    - ...
      equipment_focal_length_mm: float(0,)?
      equipment_sensor_width_mm: float(0,)?
      equipment_sensor_height_mm: float(0,)?
      equipment_reducer: float(0,)?
```

None of the fields appears in `options`, so a new pier starts with no equipment.

- *Why `float(0,)`:* the Supervisor's lower bound is inclusive, so it cannot say
  "above 0". A bound of 0 still rejects negative numbers on save. The core
  rejects 0 itself.
- *Alternative:* a small positive bound, such as `float(0.001,)`. Rejected: the
  number is arbitrary, and it would be a second rule beside the core's.

### D5. Labels and documentation

`ha-addon/translations/en.yaml` gains the four fields under `piers.fields`:

- "Focal length", "Sensor width" and "Sensor height". Each description gives the
  unit, millimetres, and says the three go together.
- "Reducer or barlow". Its description says the factor has no unit, gives 0.8
  and 2 as examples, and says an empty field means 1.0.

`ha-addon/DOCS.md` gains an equipment example. It also lists each form label
beside its `config.yaml` name, such as "Sensor height" and
`equipment.sensor_height_mm`. The log uses the file's names, so this list lets a
user find the field to fix. The README's add-on section gets a short example.

The existing test that every schema key has a label covers the four fields.

## Risks / Trade-offs

- [The log names `equipment.sensor_height_mm`, not the form's label] → The error
  still names the pier and the missing key. `DOCS.md` maps each key to its form
  label (D5). Form-specific wording would need a second copy of the rule (D2).
- [The core's log line spans several lines] → This is how every core validation
  skip is logged today, for file and form piers alike. It is outside this change.
- [Four more fields make each pier longer on the form] → All four are optional,
  and their labels say the three sizes go together. The manual check below
  records how the live form shows them.
- [The schema tests prove only the manifest, not the live form] → A manual check
  on a real Home Assistant instance records its Home Assistant and Supervisor
  versions. It passes when all of these hold:
  1. A pier shows the four equipment fields, with their labels.
  2. A pier with focal length, sensor width and sensor height saves. After a
     restart, the log shows no error for it.
  3. A negative focal length does not save, and the form shows an error.
  4. Clearing all four fields saves. The saved values hold none of the four
     fields, and after a restart the pier has no equipment.

## Migration Plan

None. All four fields are optional, so a saved form without them keeps working
and its piers keep ranking without a field-of-view term. A rollback restores the
previous add-on version. Its schema lacks the new fields. We have not checked
what the Supervisor does with their saved values. It may warn and keep them, or
drop them. If it keeps them, the older service rejects each pier that holds them
as an unknown key. In either case, the user should clear the four fields before
rolling back, and may need to enter them again after upgrading.
