## Why

Inside the add-on, the service uses either the Configuration tab or
`config.yaml`, never both. A user with a horizon file, such as a NINA `.hrz`
export, cannot put that file on the form. Today they must give up the form, or
give up the horizon file.

The same split hides every other setting the form does not show yet. Today,
`go_threshold`, `max_gust`, the explainer and the topic names are reachable only
by moving every pier into `config.yaml`.

This story sets the final rule from epic #67: `config.yaml` adds the settings
the form leaves unset. The epic and issue #73 say "settings the form does not
show". This change reads that as "settings the form leaves unset", so it also
covers optional fields the form shows but the user left empty, such as a
pier's horizon.

Story: #73 `addon-form-horizon-file`, part of epic #67.

## What Changes

- **`config.yaml` adds to the form.** Inside the add-on, when the form lists
  piers, the service also reads `config.yaml` if it exists. The file may add any
  setting the form leaves unset:
  - per pier: a horizon file (`horizon.file` and `format`), `go_threshold`,
    `max_gust`, or any other pier key the form leaves unset. A pier's `id`
    only matches the two sources, so it is not a setting;
  - overall: `explainer`, and `mqtt.discovery_prefix` and `mqtt.base_topic`.

  A file pier matches a form pier by `id`. A relative horizon `file:` path is
  read from the add-on's config folder, as today.
- **A setting given in both is a startup error.** The error names each setting
  and its pier, and the add-on stops. These count as one setting each, so they
  come from one place only:
  - a pier's horizon (the form's floor or points, or the file's `horizon` block);
  - a pier's equipment (the form's equipment fields, or the file's `equipment`
    block);
  - the broker connection (host, port, username and password).

  A form field left empty counts as not set. The form always sets the interval,
  so a `recompute` block in the file is always an error.
- **A file pier the form does not list is a startup error.** The error names the
  pier. A pier the form lists but skips, such as one with unreadable horizon
  points, still counts as listed. A pier id listed twice in `config.yaml` is
  also a startup error.
- **One error lists every problem.** The user can fix them all before the next
  restart.
- **Errors never quote setting values.** An error names settings, piers and, for
  a YAML mistake, the line and column. It never quotes the file, so a broker
  password on a broken line stays out of the log.
- **BREAKING (add-on only): the file alone no longer sets up the add-on.** When
  the form lists no piers, the service stops with "Nothing is set up", even if
  `config.yaml` exists. When the file lists piers, the error names them, and
  tells the user to add each one on the Configuration tab and keep only the
  extra settings in the file. Nobody runs the add-on yet, so no setup breaks in
  practice.
- **Log and error wording follow the new rule.**
  - The warning that `config.yaml` is ignored goes away.
  - The log says the settings came from the Configuration tab, or from the
    Configuration tab and `config.yaml`.
  - Errors about the Supervisor's broker tell the user to set `mqtt.host` on the
    Configuration tab or in `config.yaml`. They no longer say that `config.yaml`
    is not read.
  - When the form sets no broker host and the file does, the file's broker is
    used, not the Supervisor's.
- **Documentation.** `ha-addon/DOCS.md` and the README describe how the form and
  the file combine. They drop "Set up with config.yaml instead".

Out of scope:

- Docker and source installs. They keep reading the whole `config.yaml`.
- Stellarium and Telescopius horizon files. No install supports them yet.
- New form fields. Stories #74 and #75 add the gate and explainer fields; this
  rule then covers them with no new code.
- A rule that pier ids are unique for every install type. A separate issue
  covers it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-addon`: the rule that chooses between the Configuration form and
  `config.yaml` becomes a merge with conflict errors. The "empty form falls back
  to the file" behavior is removed. Broker errors on the form path change their
  advice.

## Impact

- **Changed files:**
  - `pierpressure/addon_options.py`, or a new module beside it: merges the form
    and the file, and finds conflicts and unknown piers.
  - `pierpressure/__main__.py`: reads both sources inside the add-on; new log
    lines, the "Nothing is set up" error, and the Supervisor error advice.
  - `ha-addon/config.yaml`: comments that describe the old rule.
  - `ha-addon/DOCS.md` and `README.md`: how the form and the file combine.
- **New decision record:** ADR-0020 left "letting the file add settings to a
  form setup" as a separate decision. This change records it.
- **Core change:** the core gains one file-reading helper with no Home
  Assistant code. Its YAML error names only the file, line and column. Docker
  and source installs see this safer error message too. It is their only
  change.
- **Unchanged:** the `config.yaml` format. A file that loads today loads the
  same way on Docker and source installs, and the core still validates one
  settings object.
- **Tests:** the merge, each conflict, unknown and duplicate pier ids, a skipped
  form pier with a file entry, the empty-form error, and a form pier with a
  horizon file end to end.
- **No change** to the verdict document, MQTT topics, entities, or entity
  mapping.
