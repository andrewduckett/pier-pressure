## Why

On the add-on's **Configuration** tab, a user cannot set a pier's GO threshold
or its wind-gust limit. A user who wants a stricter GO, or a wind gate for a long
focal length, must write these two settings in `config.yaml` instead.

Both settings are plain numbers, so they fit the form. This story adds them.

Story: #74 `addon-form-gates`, part of epic #67.

## What Changes

- **Two optional fields for each pier on the form.** Their names match
  `config.yaml`:
  - `go_threshold`: the score a night needs for `GO`, from 0 to 100. Without it,
    the pier uses the default of 65.
  - `max_gust`: the wind-gust limit, in km/h. Without it, the pier has no wind
    gate, so no forecast gust can cause a `NO-GO`.
- **The file's rules check the form's values.** The service passes both values
  to the core unchanged. The core checks them exactly as it checks a
  `config.yaml` pier. A pier whose value fails a check is skipped with a logged
  error that names the pier. The other piers are still published.
- **An empty field counts as not set.** A field the user clears is treated as
  absent, not as an empty value. The pier then uses the default, or the value
  `config.yaml` gives it. This rule covers only these two fields.
- **A setting comes from one place.** When the form and `config.yaml` both set
  `go_threshold` or `max_gust` for the same pier, the add-on stops with a
  configuration error. This is the existing rule from story #73.
- **Documentation.** `ha-addon/DOCS.md` and the README's add-on section describe
  the two fields. The DOCS list of what `config.yaml` can add no longer uses
  these two settings as its examples.

Out of scope:

- New gates or thresholds.
- Any change to what the GO threshold or the wind gate means.
- Dropping empty values for pier fields other than these two.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the Configuration form gains each pier's `go_threshold` and
  `max_gust`.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: the two fields in each pier's `schema` entry.
  - `ha-addon/translations/en.yaml`: labels and descriptions for the two fields.
  - `pierpressure/addon_options.py`: leaves out either field when it is not set.
  - `ha-addon/DOCS.md` and `README.md`: the two fields.
- **Unchanged:** the `config.yaml` format, the core's checks, and Docker and
  source installs. A `config.yaml` that loads today loads the same way.
- **Tests:** the manifest's new fields and labels, both values from the form,
  empty fields, a bad value, and a value set in both the form and the file.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
