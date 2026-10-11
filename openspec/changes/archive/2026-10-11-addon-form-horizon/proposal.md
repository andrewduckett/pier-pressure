## Why

On the add-on's **Configuration** tab, every pier gets an open, flat horizon at
0°. Trees and houses make that wrong for most real piers, and the horizon decides
which targets are visible. Today an add-on user who wants a horizon has to stop
using the form and write `config.yaml` instead.

This story adds a horizon to each pier on the form. Most hand-measured horizons
then need no file at all.

Story: #70 `addon-form-horizon`, part of epic #67.

## What Changes

- **Two new pier fields on the form.** Each pier gets two optional fields:
  - `min_altitude`: a flat floor, in degrees from 0 to 90.
  - `horizon_points`: points typed as text, in the same syntax as `config.yaml`,
    such as `[[0, 10], [90, 25], [180, 5]]`.
- **One syntax, one parser.** The service reads `horizon_points` with the same
  YAML parser it uses for `config.yaml`. It then passes the points to the
  existing horizon checks, so the same rules and error messages apply.
- **The same "exactly one source" rule.** A pier that sets both fields breaks
  the rule that a horizon has exactly one source. The service skips that pier,
  exactly as it skips a file pier with two horizon sources.
- **A bad horizon skips only its pier.** Text that is not valid YAML, points out
  of range, and both fields set all skip the pier with a logged error. The other
  piers keep publishing. The add-on stops only when no pier is left.
- **A blank field means "not set".** When the user clears `horizon_points`, the
  form may save it as empty text. The service treats empty or blank text as
  unset.
- **A quick check on save.** The form rejects `horizon_points` text that is not
  wrapped in square brackets, so the user sees the most common mistake before
  saving. Empty text still passes this check.
- **Labels and documentation.** The two fields get English labels.
  `ha-addon/DOCS.md` and the README's add-on section show a horizon example. They
  no longer list a horizon as something only `config.yaml` can hold.

Out of scope:

- Horizon files, such as a NINA `.hrz`. Story #73 covers them.
- A different text syntax for points. Epic #67 lists it as a Won't.
- Any change to `config.yaml` or to Docker and source installs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the Configuration form gains `min_altitude` and `horizon_points`
  for each pier, and the service turns them into the pier's horizon.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: two optional pier fields in `schema`.
  - `ha-addon/translations/en.yaml`: labels and descriptions for both fields.
  - `pierpressure/addon_options.py`: turns the two form fields into the
    `horizon` block a `config.yaml` pier would hold, and parses the points text.
  - `ha-addon/DOCS.md` and `README.md`: a horizon example on the form.
- **Unchanged:** the core (`pierpressure/core/`), the `config.yaml` format, and
  Docker and source installs.
- **Tests:** the manifest's new fields and labels, turning form values into a
  horizon, blank text, invalid text, both fields set, and an end-to-end horizon
  from the form.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
