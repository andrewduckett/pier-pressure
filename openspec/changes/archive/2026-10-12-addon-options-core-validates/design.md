## Context

See proposal.md for why, and the two delta specs for the required behaviour.
This design covers how the core reads horizon points written as text, and how
the add-on stops making setting checks of its own.

Facts that shape the approach:

- **The add-on parses `horizon_points` today.** `_with_horizon_block` in
  `pierpressure/addon_options.py` calls `yaml.safe_load` on the text. It raises
  `ValueError` when the value is not text or not valid YAML. `_config_piers`
  catches that error, logs the core's skip message, and drops the pier.
- **The add-on replaces a `horizon` value beside the horizon fields.** When a
  pier holds a `horizon` value and sets `min_altitude` or `horizon_points`,
  `_with_horizon_block` writes a new `horizon` block over the old one. No error
  is logged.
- **The add-on rejects an `equipment` value beside the `equipment_*` fields.**
  `_with_equipment_block` raises `ValueError` in that case, and `_config_piers`
  drops the pier. A null `equipment` beside the fields counts as unset, and the
  fields build the block. A test covers that null case.
- **The Supervisor drops undeclared keys inside a pier.**
  `_nested_validate_dict` in `supervisor/apps/options.py` skips any key that is
  not in the schema and logs `Unknown option`. So an `equipment` key on a form
  pier can only reach `options.json` if someone writes the file another way.
- **`HorizonConfig.points` accepts only a list today.** Its type is
  `list[tuple[float, float]] | None`. The core already imports `yaml` in
  `pierpressure/core/config.py`.
- **Pydantic names the nested location.** We tested this on Pydantic 2.13.5. A
  `ValueError` raised in a `mode="before"` validator on `points` gives an error
  located at `horizon.points`. Text such as `"5"` parses to a number, and the
  list check then fails with "Input should be a valid list", also at
  `horizon.points`.
- **A pier error spans several lines today.** `validate_piers` logs the
  `ValidationError` text, which Pydantic writes over several lines. This holds
  for every pier error, such as a latitude of 95.
- **The YAML reader's message spans several lines.** The add-on joins it onto
  one line today, with `" ".join(str(exc).split())`.
- **`combine_settings` runs the translation before it merges.** `_merge` says
  that "a file entry whose form pier the translation skipped is dropped."

## Goals / Non-Goals

**Goals:**

- The core holds every setting check. The add-on reads, renames and combines
  settings, and keeps only the checks it needs to run.
- A form pier and a `config.yaml` pier with the same bad value get the same
  error.

**Non-Goals:**

- Reading top-level keys the form does not declare. The add-on reads only
  `piers`, `interval_seconds` and `mqtt` from the saved values.

- Writing pier errors on one line. They span several lines today, for every
  setting, and this change keeps that.
- Changing the form's save check on `horizon_points`. It still helps the user,
  even though nothing depends on it.

## Decisions

### D1: The core parses text in `points` with a before-validator

`HorizonConfig` gets a `field_validator("points", mode="before")`. When the
value is a `str`, the validator parses it with `yaml.safe_load`, the same reader
the core uses for `config.yaml`. It returns the result, and Pydantic then checks
it as the list it checks today. Any other value passes through unchanged.

The validator raises `ValueError` in two cases:

- The text is not valid YAML. The message joins the reader's message onto one
  line, as the add-on does today.
- The text parses to `None`. Empty text, blank text, `null`, `~` and a
  comment-only line all parse to `None`. Without this check, `None` would mean
  "no points given". The pier would then quietly fall back to another horizon
  source, or to open sky.

Text that parses to some other value that is not a list, such as `5` or
`{a: 1}`, gets Pydantic's own list error. The validator needs no case for it.

Alternatives considered:

- **Parse the text in `ConfigFile` or `build_config`.** This splits the
  `horizon` rules across two places, and the error would not carry the
  `horizon.points` location for free.
- **Treat text that holds nothing as unset.** This is more lenient. But a
  typo, or a stray comment, would silently give the pier open sky. The add-on
  never sends blank text, because it drops unset fields with `is_set` before it
  renames them.

### D2: The add-on renames the horizon fields and nothing more

`_with_horizon_block` first drops each horizon field that `is_set` counts as
unset. That rule says what an empty form field means, not whether a value is
valid, so it stays in the add-on.

Then:

- When the pier's `horizon` value is set, the add-on leaves the set horizon
  fields where they are. The core's `PierConfig` forbids extra keys, so it
  rejects each one by name.
- Otherwise, a set `horizon_points` becomes `horizon.points` with its value
  unchanged, whatever its type. A set `min_altitude` becomes
  `horizon.min_altitude`.

The function no longer raises. A list in `horizon_points` reaches the core and
is accepted, as a list is in `config.yaml`.

### D3: The equipment fields follow the same rule

`_with_equipment_block` works as D2 does. It drops each `equipment_*` field that
`is_set` counts as unset. When the pier's `equipment` value is set, it leaves the
set `equipment_*` fields where they are, and the core rejects each one by name.
Otherwise, it builds the `equipment` block from the set fields. It no longer
raises.

Both functions use `is_set` to decide whether `horizon` or `equipment` is set,
because `pier_settings` uses it to decide whether a pier sets either one. A null
`horizon` or `equipment` counts as unset, so the flat fields build the block.

### D4: The translation keeps every pier

`_config_piers` no longer catches `ValueError`, because neither helper raises.
Every form pier that is a mapping goes to the core after renaming. The core logs
and skips a bad one with the same skip message as before.

`combine_settings` then merges the `config.yaml` settings into every form pier,
including one the core will skip. That changes no result, because the core
skips the pier either way. The docstrings of `translate_form`, `_config_piers`
and `_merge`, and the module docstring of `pierpressure/addon_settings.py`, drop
the wording about a pier the translation skipped.

The import of `SKIP_PIER_MESSAGE` in `pierpressure/addon_options.py`, and its
`logger`, go if nothing else uses them. So does its `yaml` import.

### D5: The add-on keeps the checks it needs to run

`read_form_values` keeps its three checks: valid JSON, a mapping at the root,
and a `piers` list. `_file_piers` keeps its checks on `config.yaml` pier
entries. `_check_piers`, `_check_broker` and the interval check keep the rule
against a setting given in both sources. Each of these checks the shape the
add-on needs, or a rule about combining two sources. None decides whether a
setting's value is valid.

### D6: Tests

The tests follow the delta specs, test first:

- **Core, in `tests/test_horizon_config.py`:** text points equal the same list.
  Unreadable text fails its pier, with `horizon.points` in the error and the
  YAML message on one line. The texts `"5"`, `"{a: 1}"`, `""`, `"   "` and
  `"# none"` each fail their pier with `horizon.points` in the error.
- **Add-on translation, in `tests/test_addon_options.py`:**
  - `horizon_points` text passes through unchanged as `horizon.points`.
  - A number in `horizon_points` passes through unchanged.
  - A pier with an `equipment` mapping beside set `equipment_*` fields keeps
    those fields.
  - A pier with a `horizon` mapping beside a set `min_altitude` or
    `horizon_points` keeps those fields.
  - A `horizon` mapping beside blank `horizon_points`, and an `equipment`
    mapping beside a null `equipment_*` field, each pass through without the
    unset field.
  - The tests for the removed checks go: the two `horizon_points` errors, the
    one-line YAML log, the empty list after every pier is skipped, and the
    `equipment` conflict error.
- **End to end, through `combine_settings` and the core:** form piers with a
  latitude of 95, a `go_threshold` of 101 and a numeric `horizon_points` each
  get the same error as a `config.yaml` pier with the same value. An `equipment`
  mapping beside `equipment_focal_length_mm` gives an error that names
  `equipment_focal_length_mm`, and the add-on logs nothing of its own. A
  `horizon` mapping beside `horizon_points` gives an error that names
  `horizon_points`.
- **The test in `tests/test_addon_settings.py` that uses a skipped pier** still
  passes. Its form pier now reaches the core, which skips it.

## Risks / Trade-offs

- [A bad `horizon_points` now logs over several lines, not one.] → Every other
  pier error already does this, so the add-on's log becomes consistent. The
  YAML reader's own message still sits on one line inside it.
- [An error about the form's `horizon_points` now says `horizon.points`.] →
  `ha-addon/DOCS.md` gets one line that links the two names.
- [An error about an `equipment` mapping beside the `equipment_*` fields no
  longer names `equipment`.] → It names each set `equipment_*` field, which is
  the field to remove.
- [The YAML reader's message can quote part of the text it could not read.] →
  Pier errors show their values on purpose, so a user can fix them, as
  config-secrets-hidden-in-errors decided.
- [The add-on ignores top-level keys the form does not declare, such as a
  hand-written `explainer`.] → The Supervisor drops those keys on save, and the
  core ignores unknown top-level keys in `config.yaml`. Such settings belong in
  `config.yaml`, where the core checks them.
