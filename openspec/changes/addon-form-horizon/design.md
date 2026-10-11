## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required
behaviour. This design covers how the two form fields become a pier's horizon
without changing the core or the `config.yaml` format.

Facts that shape the approach:

- **The edge already translates the form.** `pierpressure/addon_options.py`
  turns `/data/options.json` into the mapping a `config.yaml` would hold
  (addon-options-form D1, ADR-0020). Today it passes pier entries through
  unchanged.
- **The core already has every horizon rule.** A pier's `horizon` block takes
  `points`, `min_altitude` or `file`. `_resolve_horizon` in
  `pierpressure/core/config.py` enforces "exactly one source". `from_points` and
  `flat` in `pierpressure/core/horizon.py` check the ranges and duplicates. Each
  failure is a `ValueError`, which `validate_piers` logs and turns into a
  skipped pier.
- **`PierConfig` forbids unknown keys.** A pier that still holds
  `horizon_points` when it reaches the core fails its check.
- **The form cannot nest a `horizon` block.** Home Assistant allows options
  nested at most two levels deep. `piers` and its items already use both.
- **The file is read with `yaml.safe_load`.** `read_config` uses it, so "the same
  parser" means `yaml.safe_load` on the field's text.
- **How the Supervisor checks `match(...)`.** In `supervisor/apps/options.py`,
  a `match(REGEX)` type runs `vol.Match(REGEX)(str(value))`. `vol.Match` uses
  `re.match`, which anchors at the start only, so the pattern must end with
  `$`. The frontend shows a `match` field as a plain text box. The `?` suffix
  makes a field optional.

## Goals / Non-Goals

**Goals:**

- The core and its horizon rules stay unchanged. A form horizon passes the same
  checks as a file horizon.
- One bad horizon never stops the other piers.

**Non-Goals:**

- Accepting text for `horizon.points` in `config.yaml`. The file format stays as
  it is.
- Form-specific wording for core error messages.

## Decisions

### D1. The edge rebuilds each pier's `horizon` block

`read_addon_options` stops passing pier entries through unchanged. For each
pier, it removes `min_altitude` and `horizon_points`, and puts what is set into
a `horizon` block:

```
form pier                              config-shaped pier
{"id": "backyard", ...,                {"id": "backyard", ...,
 "min_altitude": 15}           -->      "horizon": {"min_altitude": 15}}

{"id": "backyard", ...,                {"id": "backyard", ...,
 "horizon_points": "[[0,10]]"} -->      "horizon": {"points": [[0, 10]]}}

{"id": "backyard", ...}        -->     {"id": "backyard", ...}
```

When both fields are set, the block holds both keys. The core's "exactly one
source" rule then rejects the pier and the pier is skipped.

- *Why:* the core keeps one copy of every horizon rule, and gains no form names.
- *Alternative:* check "both set" at the edge, with an error that uses the form's
  names. Rejected: it copies a core rule into a second place. See the first
  risk below.

### D2. A points-text YAML error skips the pier at the edge

The edge reads `horizon_points` with `yaml.safe_load`. When the text is not valid
YAML, the edge logs an error and leaves that pier out of the mapping. The error
uses the same wording as the core's skip, and names the field:

```
Skipping invalid pier 'backyard': horizon_points is not valid YAML: <parser message>
```

Any other parse result, such as a number or a flat list, goes into
`horizon.points` unchanged. The core then rejects it with its own message.

When every pier is skipped, the mapping holds an empty `piers` list. The form did
list piers, so the service does not fall back to `config.yaml`. `build_config`
then raises its usual "No valid pier" `ConfigError`, and the add-on stops.

- *Why:* a YAML error is the one horizon error the core never sees. Skipping the
  pier at the edge gives it the same result as every other bad horizon.
- *Alternative:* raise a `ConfigError` and stop. Rejected: one typo on one pier
  would stop every other pier. A YAML error in `config.yaml` itself does stop
  the service, but there it breaks the whole file, not one pier.
- *Alternative:* pass the raw text to the core as `points`. Rejected: the core
  would report "Input should be a valid list", which hides the parser's
  message.
- *Alternative:* let `HorizonConfig.points` accept a string. Rejected: it changes
  the `config.yaml` format, which epic #67 rules out.

### D3. Blank and missing values mean "not set"

A key that is absent or `null` is unset. A `horizon_points` value that is empty
or blank after stripping whitespace is unset too. The frontend may save a cleared
text field as `""`, and that must not count as a second horizon source.

### D4. The manifest's horizon fields

```yaml
schema:
  piers:
    - id: str
      latitude: float(-90,90)
      longitude: float(-180,180)
      elevation_m: float
      min_altitude: float(0,90)?
      horizon_points: 'match(^\s*(\[.*\])?\s*$)?'
```

Neither field appears in `options`, so a new pier starts with no horizon.

The pattern accepts blank text, or one bracketed span with only whitespace
around it. It ends with `$` because the Supervisor anchors only the start. A
test reads the pattern from the manifest and applies it with `re.match`, as the
Supervisor does.

- *Why a loose pattern:* it catches the most common mistake, missing outer
  brackets, while the user can still fix it before saving. Checking the full
  structure with a regex would be hard to read, and the parser checks it anyway.
- *Why accept blank text:* a pattern that needs brackets would reject a cleared
  field. The user could then not save the form.
- *Why `float(0,90)`:* it is the range `flat` accepts. The Supervisor then
  rejects a bad floor on save.

### D5. Labels

`ha-addon/translations/en.yaml` gains both fields under `piers.fields`:

- `min_altitude`: name "Horizon floor". The description says the floor is in
  degrees, applies in every direction, and cannot be used with horizon points.
- `horizon_points`: name "Horizon points". The description gives the syntax with
  an example, says azimuth and altitude are in degrees, and says the field cannot
  be used with a horizon floor.

The existing test that every schema key has a label covers both fields.

## Risks / Trade-offs

- [The core's message for two sources names `points`, not `horizon_points`] →
  The error still names the pier, and it says "exactly one source (points,
  min_altitude, or file)". `DOCS.md` says that the two fields cannot be used
  together. Form-specific wording would need a second copy of the rule (D1).
- [A pattern with `.*` does not match a line break] → Text pasted across several
  lines fails the save check. The form shows a single-line text box, so this
  should be rare. `DOCS.md` shows the points on one line.
- [The Supervisor may treat a cleared optional number as `null` and refuse to
  save] → This is how Home Assistant handles any optional number, and is outside
  this change. The manual check during verification clears both fields and
  saves.
- [The frontend changes how it shows a `match` field] → The finding comes from
  the current Supervisor source. The manual check on a real instance confirms
  it.

## Migration Plan

None. Both fields are optional, so a saved form without them keeps working and
its piers keep an open horizon. A rollback restores the previous add-on version.
Its schema lacks the new fields, so the Supervisor drops their values and warns
about them in its log. The piers then fall back to an open horizon.
