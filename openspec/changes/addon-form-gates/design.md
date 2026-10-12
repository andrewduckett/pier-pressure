## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required
behaviour. This design covers how two flat form fields reach a pier without any
change to the core or the `config.yaml` format.

Facts that shape the approach:

- **The names already match.** In `config.yaml`, `go_threshold` and `max_gust`
  are flat keys of a pier. Unlike the horizon and the equipment, they need no
  block, so the form can use the file's names as they are (ADR-0020).
- **The edge passes other pier keys through.** Here, "the edge" means the code
  outside the pure core that reads the add-on's form. `translate_form` in
  `pierpressure/addon_options.py` rebuilds the horizon and equipment blocks. It
  copies every other pier key, with its value, unchanged.
- **The core already has every rule.** `PierConfig` in
  `pierpressure/core/config.py` makes `go_threshold` a whole number from 0 to
  100, with a default of 65. It makes `max_gust` a number above 0, or absent for
  no wind gate. `validate_piers` logs a pier that fails these checks and keeps
  the others.
- **A null value breaks the core's default.** The core uses the default only
  when the key is absent. A key saved as `null` reaches the core as `None`. The
  core then rejects the pier, because `None` is not a whole number.
- **The combine step already covers the two keys.** `pier_settings` in
  `pierpressure/addon_options.py` names each pass-through key after itself, and
  ignores a value that is not set. So `combine_settings` already reports a
  `go_threshold` set in both places, and lets `config.yaml` fill an empty one
  (addon-form-horizon-file D2, ADR-0021).

## Goals / Non-Goals

**Goals:**

- The core and its rules stay unchanged. Form values pass the same checks as
  file values.
- A field the user leaves empty behaves as a key the file leaves out.

**Non-Goals:**

- A general rule that drops every unset pass-through pier key. Today the only
  other pass-through keys are `id`, `latitude`, `longitude` and `elevation_m`,
  and all four are required.
- Form-specific wording for the core's error messages.

## Decisions

### D1. The edge drops an unset gate field

For each pier, the translation removes `go_threshold` and `max_gust` when
`is_set` says the value is not set. A set value passes through unchanged:

```
form pier                                config-shaped pier
{"id": "backyard", ...,                  {"id": "backyard", ...,
 "go_threshold": 75,             -->      "go_threshold": 75,
 "max_gust": null}                        }

{"id": "backyard", ...,                  {"id": "backyard", ...}
 "go_threshold": "",             -->
 "max_gust": "  "}
```

`is_set` is the single rule for a set form value (addon-form-horizon-file D2).
It treats `null`, empty text and blank text as not set, and 0 as set. Reusing it
keeps the translation and the combine step in agreement. `pier_settings` says a
null `max_gust` is not set, and the translation then removes it, so the value
from `config.yaml` is what the core sees.

The two names live in one constant beside `HORIZON_FIELDS` and
`EQUIPMENT_FIELDS`.

- *Why only these two:* they are the only optional pass-through keys. The user
  chose to keep the fix to this story's fields.
- *Alternative:* drop every unset pass-through key. Rejected for now: no other
  key needs it, and a future flat field can add itself to the constant.
- *Alternative:* turn a null into the default at the edge, such as 65. Rejected:
  the edge would then own a copy of the core's default, and `config.yaml` could
  no longer fill the field.

### D2. The manifest's gate fields

```yaml
schema:
  piers:
    - ...
      go_threshold: int(0,100)?
      max_gust: float(0,)?
```

Neither field appears in `options`, so a new pier starts with neither set.

- *Why `int(0,100)`:* it matches the core's range, so the Supervisor refuses an
  out-of-range threshold on save. The core checks it again.
- *Why `float(0,)`:* the Supervisor's lower bound is inclusive, so it cannot say
  "above 0". A bound of 0 still rejects negative numbers on save. The core
  rejects 0 itself. The equipment fields use the same pattern
  (addon-form-equipment D4).
- *Alternative:* a small positive bound, such as `float(0.1,)`. Rejected: the
  number is arbitrary, and it would be a second rule beside the core's.

### D3. No default value on the form

The form shows both fields empty. Their descriptions say what an empty field
means.

- *Why:* a field on a pier in a list cannot have a default in `options`. A
  pre-filled 65 would also count as set. `config.yaml` could then never set the
  threshold without a "set in both places" error.

### D4. Labels and documentation

`ha-addon/translations/en.yaml` gains the two fields under `piers.fields`:

- "GO threshold": the score from 0 to 100 a night needs for `GO`, with no unit.
  The description says to leave it empty for 65.
- "Wind-gust limit": the gust in km/h above which the night is `NO-GO`. The
  description says to leave it empty for no wind gate.

`ha-addon/DOCS.md` lists the two fields with the other pier fields. Its list of
what `config.yaml` can add uses other examples, such as a horizon file and
`explainer`. The README's add-on section says the form sets them.

## Risks / Trade-offs

- [The core's error for a bad value quotes the value] → The value is a number,
  not a secret, so the log may show it.
- [A future optional flat field can hit the null problem] → The constant from D1
  sits beside the other field lists. A test with a null value for each optional
  form field catches a field missing from it.
- [The Supervisor may save a cleared number as `null` or leave it out] → D1
  handles both, and the tests cover absent, `null` and blank text.

## Migration Plan

None. Both fields are optional and start empty. A saved form without them loads
as before, and so does every `config.yaml`.
