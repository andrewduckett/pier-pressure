## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required
behaviour. This design covers where the form and the file combine, how the
conflict checks see both sources, and what happens to the wording that assumed
one source.

Facts that shape the approach:

- **The edge translates the form into the file's shape.** "The edge" means the
  code outside the pure core that reads the add-on's form.
  `read_addon_options` in `pierpressure/addon_options.py` reads
  `/data/options.json`. It returns the mapping a `config.yaml` would hold, or
  `None` when the form lists no piers (ADR-0020).
- **The translation drops bad piers.** A form pier whose `horizon_points` cannot
  be parsed, or that mixes an `equipment` mapping with equipment fields, is
  logged and left out of the returned mapping. Its id is then lost.
- **`load_app_config` picks one source.** In `pierpressure/__main__.py`, it uses
  the form when the form lists piers, and otherwise reads `config.yaml` through
  `read_config`.
- **`read_config` checks the broker rule on the file alone.** It builds a
  `ConfigFile`, whose construction rejects `mqtt.port`, `mqtt.username` or
  `mqtt.password` without `mqtt.host` (addon-form-broker D3). It also expands
  `${VAR}` from the environment.
- **The wording assumes one source.** `FORM_PLACE`, `FORM_NOTE` and
  `FORM_LOGIN_ADVICE` in `__main__.py`, and `CONFIG_FILE_PLACE` in
  `pierpressure/supervisor.py`, name either the tab or the file. `FORM_NOTE`
  says that `config.yaml` is not read, which stops being true.
- **The form's schema does not change.** This story adds no form field, so the
  Supervisor's save check is unaffected. Unlike #70 and #72, it needs no live
  check on a Home Assistant instance.

## Goals / Non-Goals

**Goals:**

- The merge and its checks live in the add-on edge. The pure core gains at most
  a small, Home Assistant-free reading helper.
- The conflict check sees every pier the form lists, including piers the
  translation later skips.
- A new flat form field needs no change to the conflict check, unless it is
  flattened from a nested block.

**Non-Goals:**

- A rule that pier ids are unique across every source. Issue #86 covers it.
- `${VAR}` expansion in form values. Today the form's values are not expanded,
  and that stays.
- A new message format for configuration errors. The existing
  `Configuration error: ...` log line carries the combined error.

## Decisions

### D1. A new edge module combines the two sources

A new module, `pierpressure/addon_settings.py`, takes the form's raw saved values
and the file's raw mapping. It returns one config-shaped mapping, or raises one
`ConfigError` that lists every problem.

`addon_options.py` keeps its single job: translating form fields into the file's
shape. `load_app_config` calls the new module, then wraps the result in a
`ConfigFile` as it does today.

Alternatives considered:

- **Add the merge to `addon_options.py`.** It would mix two jobs in one module,
  and the module's docstring and tests already describe the translation only.
- **Merge inside the core's `build_config`.** The core would need to know that a
  form exists and which of its fields group together. ADR-0020 rules this out.

### D2. Conflicts are found on the raw form values, before translation

The conflict check reads the form's raw saved values, not the translated
mapping. A small function names the settings a raw form pier sets:

- `min_altitude` or `horizon_points` set → `horizon`
- any field in `EQUIPMENT_FIELDS`, or an `equipment` value → `equipment`
- any other key that is set → that key

"Set" uses the rule the translation already uses: not absent, not `None`, and
not empty or blank text. The function lives in `addon_options.py`, beside
`EQUIPMENT_FIELDS`, so the field lists are not duplicated.

The listed ids also come from the raw values. Every raw pier that is a mapping
with a text `id` counts as listed. So a pier the translation skips still
matches its file entry, as the spec's "A skipped form pier still counts as
listed" scenario requires.

After the checks pass, the translation runs as today. A file entry whose form
pier was skipped is then dropped silently, because its pier is not published.

Alternatives considered:

- **Compare keys on the translated mapping.** The groups would fall out for free,
  because the translation already builds `horizon` and `equipment` blocks. But
  skipped piers are gone by then. A file entry for a skipped pier would be
  reported as "not on the Configuration tab", which is misleading.
- **Make the translation keep skipped piers.** Their blocks cannot be built,
  which is why they are skipped, so there is nothing to compare.

A new flat field, such as `go_threshold` in #74, falls into "any other key". So
the check covers it with no code change.

### D3. The four groups and the top-level settings

The merge compares settings at these levels:

| Setting | Form side | File side |
|---|---|---|
| a pier's horizon | `min_altitude`, `horizon_points` | `horizon` |
| a pier's equipment | `equipment_*`, `equipment` | `equipment` |
| any other pier key | the key | the key |
| the broker connection | any of `mqtt.host`, `port`, `username`, `password` | any of the same four |
| any other `mqtt` key | the key | the key |
| the recompute interval | `interval_seconds` | `recompute` |
| `explainer` and any other top-level key | the key | the key |

When nothing conflicts, the merge is a plain union at each level:

- each form pier gets its file entry's keys;
- the `mqtt` block gets the file's keys;
- the top level gets the file's other keys.

The form's piers keep their order. The file cannot add a pier.

An unknown key from the file passes through. The core rejects it as it does
today, because its models forbid extra keys.

When the form lists the same id twice, the file entry for that id applies to
both piers. This keeps today's behaviour for duplicate form ids until #86
decides the rule.

### D4. The file is read without the broker rule, then checked as one whole

The core gains `read_config_mapping(path)`. It parses the YAML, checks that the
root is a mapping, and expands `${VAR}`. `read_config` then becomes
`ConfigFile(raw=read_config_mapping(path), base_dir=...)`, so Docker and source
installs behave exactly as before.

The add-on path reads the file with `read_config_mapping`. It builds the
`ConfigFile` only after the merge, so the broker rule checks the combined
settings.

This order gives the clearer error. Take a form that sets `mqtt.host` and a file
that sets only `mqtt.password`. Checked alone, the file would fail with
"mqtt.password is set without mqtt.host", which is false for the combined
settings. Checked after the conflict check, the user sees that the broker
connection is set in both places.

Alternatives considered:

- **Catch the file's `ConfigError` and re-check.** This leans on the wording of
  an exception, and still needs the raw mapping afterwards.
- **Add a flag to `read_config` that skips the rule.** It is one more parameter
  on a function every install type uses, and it is easy to call wrongly.

The new helper reads a file and the environment, as `read_config` already does.
It holds no Home Assistant code, so the core boundary test still passes.

### D5. One error lists every problem, on one line, by name only

The combine step collects problems in a list, and raises one `ConfigError` when
the list is not empty. The problems are joined with `; ` so the existing log
line stays on one line, as earlier changes keep it.

Each problem names a setting by its `config.yaml` name, and names the pier by
its id. For example:

- `horizon of pier 'backyard' is set on the Configuration tab and in config.yaml`
- `pier 'roof' in config.yaml is not on the Configuration tab`
- `pier 'backyard' is listed more than once in config.yaml`
- `the broker connection (mqtt.host, mqtt.port, mqtt.username, mqtt.password) is set on the Configuration tab and in config.yaml`

The code that builds a problem receives only key names and ids, never values.
So no message can contain the broker password or an explainer API key. A test
puts a sentinel password in both sources and checks every log line and error.

The exact wording above is a sketch. The spec fixes only what each message
names.

### D6. An empty form stops the add-on, and names the file's piers when it can

When the form lists no piers, `load_app_config` no longer reads `config.yaml` as
a full config. It raises the "Nothing is set up" error instead.

Before raising, it tries `read_config_mapping` on the file. When the file exists
and its `piers` list holds mappings with text ids, the error names those ids. It
then tells the user to add each pier on the Configuration tab with the same id,
and to keep only the extra settings in `config.yaml`.

When the file is missing, unreadable or lists no usable ids, the error is the
short form. It says nothing is set up and tells the user to add a pier on the
Configuration tab. A broken file does not hide the main cause, which is the
empty form.

A missing `/data/options.json` counts as an empty form. The Supervisor always
writes that file, so this happens only in tests or a broken install.

### D7. One place phrase and one login advice for the add-on

Inside the add-on, the settings always come from the form plus the file. So the
two-way wording collapses to one phrase:

- `supervisor.py` replaces `CONFIG_FILE_PLACE` with one constant that reads
  `on the Configuration tab or in config.yaml`. The `settings_place` parameter
  goes, because there is only one place.
- `__main__.py` drops `FORM_PLACE`, `FORM_NOTE` and `FORM_LOGIN_ADVICE`, and the
  code that appended the note to a `SupervisorError`.
- `SUPERVISOR_LOGIN_ADVICE` says to restart the Mosquitto add-on, or to set
  `mqtt.host` on the Configuration tab or in `config.yaml`.
- `LoadedConfig.from_form` and the `from_form` parameter of
  `build_delivery_and_explainer` go. Only `broker_from_supervisor` still decides
  the advice.

The Supervisor is asked only when neither source sets `mqtt.host`. In that case
both places really are open to the user, so the phrase is always true.

### D8. The log names where the settings and the broker came from

`load_app_config` logs one settings line:

- `Settings from the Configuration tab and config.yaml` when the file adds at
  least one setting;
- `Settings from the Configuration tab` otherwise.

"Adds at least one setting" means the merged mapping differs from the
translated form mapping. A file pier that holds only an `id` adds nothing.

The broker line names the Supervisor's `mqtt` service, the Configuration tab
when the form sets `mqtt.host`, or `config.yaml` when the file sets it. Outside
an add-on, both lines stay as they are today.

### D9. Docs and add-on comments describe the merge

`ha-addon/DOCS.md` replaces "The form or the file" with a section on how they
combine. That section covers:

- which settings each source owns;
- the conflict rule and its four groups;
- a horizon file example.

It drops "Set up with config.yaml instead". "More settings" points to
`config.yaml` for settings the form does not show. The error table gains rows
for a conflict, an unknown pier and an empty form.

The README's add-on section follows the same rule. Comments in
`ha-addon/config.yaml` that say the file is read only while the form is empty
are updated.

## Risks / Trade-offs

- [Someone follows an old copy of the README and writes only `config.yaml`] →
  The empty-form error names their piers and says exactly what to move (D6).
- [A future flattened form field is missed by the conflict check] → Flattened
  fields are listed beside the translation that builds their block (D2). A test
  checks that every field in the form's schema is either a known group member
  or maps to itself.
- [The form always sets `interval_seconds`, so a file `recompute` block is
  always an error] → The error names the recompute interval and both places, so
  the fix is plain. This is the "form owns what it shows" rule, applied as is.
- [A file entry for a skipped form pier is dropped without a message] → The
  pier's own skip error is already logged. A second message would add noise
  without a new fix.
- [Removing `settings_place` touches `supervisor.py` tests] → Those tests check
  the wording. They switch to the one phrase in the same commit.
- [The combined error can grow long] → Each problem is short, and a real setup
  has few piers. One line still beats one restart per problem.

## Migration Plan

Nobody runs the add-on yet, so no setup needs to move. A user who already has a
`config.yaml` with piers sees the empty-form error on upgrade, and follows it.

Rollback is a revert of this change. The older version reads `config.yaml` alone
while the form is empty, and ignores the file while the form lists piers.
