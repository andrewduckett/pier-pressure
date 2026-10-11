## Why

On the add-on's **Configuration** tab, a pier has no telescope or camera. Without
them, the service cannot rank targets on how well they fit the field of view. A
`config.yaml` user gets that ranking for every target with a known size. A form
user does not get it at all.

This story adds equipment to each pier on the form, so both users get the same
ranking.

Story: #71 `addon-form-equipment`, part of epic #67.

## What Changes

- **Four new pier fields on the form.** Each pier gets four optional fields,
  flat because the form nests only two levels deep:
  - `equipment_focal_length_mm`: the telescope's focal length, in millimetres.
  - `equipment_sensor_width_mm`: the camera sensor's width, in millimetres.
  - `equipment_sensor_height_mm`: the camera sensor's height, in millimetres.
  - `equipment_reducer`: an optional reducer or barlow factor, such as 0.8.
- **The same equipment as the file.** The service turns the four fields into the
  pier's `equipment` block, as `config.yaml` would hold it. The core then checks
  it with the same rules: each value is above 0, and the reducer defaults to 1.0.
- **Incomplete equipment skips only its pier.** A pier that sets some equipment
  fields but not focal length, sensor width and sensor height is skipped. The
  logged error names the pier and the missing field. The other piers keep
  publishing. This replaces the story's "startup error" wording, so a form pier
  fails the same way a file pier does. The add-on stops only when no pier is
  left.
- **No equipment fields means no equipment.** A pier with none of the four
  fields set ranks targets as it does today, without a field-of-view term.
- **Labels and documentation.** The four fields get English labels.
  `ha-addon/DOCS.md` and the README's add-on section show an equipment example.
  `DOCS.md` maps each field to its `config.yaml` name, because the log uses the
  file's names.

Out of scope:

- Any change to how equipment affects ranking.
- Any change to `config.yaml` or to Docker and source installs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the Configuration form gains four equipment fields for each pier,
  and the service turns them into the pier's equipment.

## Impact

- **Changed files:**
  - `ha-addon/config.yaml`: four optional pier fields in `schema`.
  - `ha-addon/translations/en.yaml`: labels and descriptions for the four fields.
  - `pierpressure/addon_options.py`: turns the four form fields into the
    `equipment` block a `config.yaml` pier would hold.
  - `ha-addon/DOCS.md` and `README.md`: an equipment example on the form.
- **Unchanged:** the core (`pierpressure/core/`), the `config.yaml` format, and
  Docker and source installs.
- **Tests:** the manifest's new fields and labels, turning form values into
  equipment, incomplete equipment, and an end-to-end ranking with equipment from
  the form.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
