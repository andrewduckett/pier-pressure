## Why

To set up the add-on today, a Home Assistant OS user must write `config.yaml` in
the add-on's config folder. Home Assistant has no file editor of its own. So the
user first installs a second add-on, such as Samba share or Studio Code Server,
only to write one file. This story lets the user enter the recompute interval and
their piers on the add-on's **Configuration** tab instead, and get a verdict
without writing any file.

It is the first story of epic #67. It proves the whole path from the form to a
verdict, and each later story in the epic adds fields to that path.

Story: #69 `addon-options-form`.

## What Changes

- **The add-on shows a form.** `ha-addon/config.yaml` declares `options` and a
  `schema`. The form has two settings: `interval_seconds`, and a list of piers.
  Each pier has an `id`, a `latitude`, a `longitude` and an `elevation_m`. The
  names match the keys in `config.yaml`. The defaults are 900 seconds and no
  piers.
- **The form fields have labels.** A new `ha-addon/translations/en.yaml` gives
  each field a name and a short description with its unit. Without it, the form
  shows bare keys such as `elevation_m`.
- **The service reads the form inside the add-on.** When the user saves the form,
  the Supervisor writes the values to `/data/options.json`. Inside an add-on only,
  the service reads that file at startup. It builds the same settings, with the
  same checks, as it does from `config.yaml`.
- **The form or the file, not both.** When the form lists at least one pier, the
  service uses only the form. When the form lists no piers, the service reads
  `config.yaml` exactly as it does today.
- **The form uses the Supervisor's broker.** A form setup has no broker settings
  of its own, so the service always asks the Supervisor's `mqtt` service for the
  broker. Topics use their defaults.
- **A warning when a file is ignored.** When the form lists piers and
  `config.yaml` also exists, the service logs a warning that names the ignored
  file. It then starts as usual.
- **A clearer error when nothing is set up.** When the form lists no piers and
  `config.yaml` is missing, the add-on stops. Its error names the missing file
  and tells the user to add a pier on the Configuration tab.
- **Document it.** `ha-addon/DOCS.md` and the README's add-on section describe the
  form as the main way to set up the add-on, and `config.yaml` as the alternative.

Out of scope:

- Horizon, equipment, broker, gate and explainer fields. Later stories in #67
  (#70 to #75) add them.
- Merging the form and the file. #73 replaces the "form or file" rule.
- Any change outside the add-on. Docker and source installs read `config.yaml`
  exactly as today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the add-on offers a Configuration form for the interval and piers,
  and reads it before `config.yaml`. This replaces the requirement "The add-on
  reads config from its own config folder", which says the add-on offers no
  options of its own.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: adds `options` and `schema`.
  - `pierpressure/__main__.py`: inside an add-on, reads the form first, and
    falls back to `config.yaml` when the form lists no piers.
  - `pierpressure/core/config.py`: may gain a small pure helper that builds the
    config from a mapping rather than a file. It stays free of Home Assistant
    code.
  - `ha-addon/DOCS.md` and `README.md`: the add-on setup.
- **New files:**
  - A small module outside `pierpressure/core/` that reads `/data/options.json`
    and turns it into the same shape as `config.yaml`.
  - `ha-addon/translations/en.yaml`: field labels and descriptions.
- **Tests:** the add-on manifest's `options` and `schema`, reading the form, the
  "form or file" rule, the warning, the missing-setup error, and that Docker
  behaviour is unchanged.
- **No change** to the verdict document, MQTT topics, entities, or entity mapping.
