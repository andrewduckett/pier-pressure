## Context

See proposal.md for why, and `specs/ha-addon/spec.md` for the required behaviour.
This design covers how form values reach the existing config path without adding
Home Assistant code to the core.

Facts that shape the approach:

- **How the form reaches the add-on.** When the user saves the Configuration tab,
  the Supervisor checks the values against the add-on's `schema`. It then writes
  them to `/data/options.json` inside the container. `/data` is always mounted.
- **The form can show a list of piers.** The Supervisor turns a list of mappings
  into a UI entry `{type: schema, multiple: true}` (`UiOptions` in
  `supervisor/apps/options.py`). The frontend shows that entry as an object
  selector: a list of items, each with its own fields
  (`supervisor-app-config.ts`). It switches the whole form to YAML only for a type
  outside `string`, `select`, `boolean`, `integer`, `float` and `schema`.
- **Range limits apply on save, not while typing.** The frontend shows numbers as
  plain boxes. The Supervisor rejects a value outside `float(-90,90)` when the
  user saves.
- **Labels come from a translation file.** The frontend looks up a field's name
  and description in `translations/<language>.yaml`, under `configuration`. A
  field inside a list is found under its parent's `fields` key. Without an entry,
  the form shows the bare key.
- **The config path already takes a mapping.** `build_config(read, broker)` in
  `pierpressure/core/config.py` validates a `ConfigFile`, which holds a raw
  mapping and a base folder. It does not care where the mapping came from. It
  already merges the Supervisor's broker when the mapping names no `mqtt.host`.
- **Add-on detection exists.** `__main__.load_app_config` treats a set
  `SUPERVISOR_TOKEN` as "inside an add-on" (ha-addon-mqtt-service D1).
- **Today a missing file is an `OSError`.** `read_config` calls `read_text`, so a
  missing file surfaces as `[Errno 2] No such file or directory`.

## Goals / Non-Goals

**Goals:**

- One validation path. A pier from the form goes through the same `PierConfig`
  checks, and the same per-pier skip, as a pier from the file.
- The core gains no Home Assistant knowledge. It never sees `options.json` or a
  form field name.
- Later stories in #67 add fields by extending one small translation step.

**Non-Goals:**

- Merging form and file values. #73 replaces the "form or file" rule.
- Watching `options.json` for changes. Saving the form restarts the add-on, which
  rereads it at startup.
- Checking for duplicate pier ids. The file path does not check this either.

## Decisions

### D1. A new edge module turns the form into the file's shape

A new module, `pierpressure/addon_options.py`, sits beside `supervisor.py`,
outside the core. It exposes one function that reads `options.json`. It returns
the mapping a `config.yaml` with the same settings would hold, or `None` when the
form lists no piers:

```
options.json                          config-shaped mapping
{"interval_seconds": 900,      -->    {"recompute": {"interval_seconds": 900},
 "piers": [{"id": ..., ...}]}          "piers": [{"id": ..., ...}]}
```

The interval is the only setting that moves. Pier entries pass through unchanged,
because the form's pier keys are the file's keys. `PierConfig` forbids unknown
keys, so an unexpected key fails the pier's check rather than being dropped.

`__main__` wraps the mapping in a `ConfigFile` and hands it to `build_config`.
The base folder is the folder that holds `config.yaml`. No form field uses it
yet, but #73 will resolve horizon file paths against it.

- *Why:* the core already validates a mapping. Translating at the edge reuses
  every check and keeps Home Assistant names out of the core.
- *Alternative:* teach `build_config` the form's field names. Rejected: the core
  would hold Home Assistant knowledge, against the import boundary's intent.
- *Alternative:* write the form out as a generated `config.yaml`. Rejected: it
  adds a file the user did not write, and confuses the rule for when the file is
  read.

### D2. `load_app_config` picks the source, then runs the existing broker step

Inside an add-on, `load_app_config` reads the form first:

```
SUPERVISOR_TOKEN set?
  no  --> read_config(config.yaml)                       (unchanged)
  yes --> read form
            form lists piers?
              yes --> config.yaml exists? --yes--> log warning naming it
                      ConfigFile(form mapping, base folder)
              no  --> read_config(config.yaml)
                      missing? --> ConfigError naming the file and the
                                   Configuration tab
then, as today:
  names no mqtt.host and inside an add-on --> fetch_mqtt_broker
  build_config(read, broker)
```

A form mapping never names `mqtt.host`, so the existing broker step always asks
the Supervisor for it. No new broker code is needed.

`load_app_config` takes the `options.json` path as an argument, defaulting to
`/data/options.json`, so tests use a temporary file. It logs one line that names
the settings' source: the Configuration tab, or the file name.

- *Why:* the source choice happens before the broker lookup, so the broker logic
  and its tests stay as they are.
- *Alternative:* read the form outside `load_app_config`, in `main`. Rejected:
  `load_app_config` is already the tested seam for add-on behaviour.

### D3. A missing or unreadable `options.json`

The Supervisor always writes `options.json` before it starts the add-on. So
reading it should not fail. When it does:

- A missing file counts as an empty form. The service falls back to
  `config.yaml`, so an older Supervisor or a test harness still works.
- A file that is not valid JSON, or whose root is not a mapping, raises a
  `ConfigError` that names the file. A silent fallback would hide a broken form.
- A `piers` value that is not a list raises a `ConfigError` too.

### D4. The missing-setup error is raised only inside an add-on

Inside an add-on, when the form lists no piers, `load_app_config` turns a missing
`config.yaml` into a `ConfigError`. The error names the file and tells the user
to add a pier on the Configuration tab. Outside an add-on, a missing file keeps
today's `OSError` message, as the spec requires.

### D5. The manifest's `options` and `schema`

```yaml
options:
  interval_seconds: 900
  piers: []
schema:
  interval_seconds: int(1,)
  piers:
    - id: str
      latitude: float(-90,90)
      longitude: float(-180,180)
      elevation_m: float
```

Every pier field is required, matching `PierConfig`. `map: addon_config` and
`PIERPRESSURE_CONFIG` stay, because the file remains the fallback. The test
`test_addon_offers_no_options` is replaced by tests for these keys.

- *Why top-level `interval_seconds`, not `recompute.interval_seconds`:* the
  frontend shows a nested mapping as a collapsed section. A top-level number is
  easier to find, and D1 moves it in one line.

### D6. `ha-addon/translations/en.yaml`

The file gives a `name` and a `description` for `interval_seconds` and `piers`.
It gives each pier field one under `piers.fields`. Each number's description
names its unit: seconds, degrees, or metres. Latitude and longitude also say
which sign means north and east. A test checks that every key in `schema` has an
entry, so a later story cannot add a field without a label.

## Risks / Trade-offs

- [The frontend changes how it shows a list of mappings] → The add-on would still
  work, because the user could switch to YAML mode. The finding comes from the
  current frontend source. A manual check on a real instance during
  verification confirms it.
- [A user adds a pier on the form while an old `config.yaml` sets `mqtt.host`]
  → The file's settings stop applying. The warning names the ignored file.
  Nobody runs the add-on yet (epic #67). #72 and #73 bring those settings to the
  form.
- [A form user's broker fails, and the existing errors say to set `mqtt.host` in
  `config.yaml`] → That advice does nothing while the form lists piers. The fix
  has two parts, because the errors arise at two times:
  - **At startup lookup.** On the form path, `load_app_config` adds a note to a
    `SupervisorError`. The note says the file is not read while the form lists
    piers.
  - **At connect, or a later reconnect.** A rejected login arises in the
    delivery adapter, after `load_app_config` returns. `load_app_config` also
    reports that the form was the source. `main` passes that to
    `build_delivery_and_explainer`, which picks login advice for form users
    instead of `SUPERVISOR_LOGIN_ADVICE`.
- [The form has no topic settings] → A form user gets the default discovery
  prefix and base topic. Users who need others can use `config.yaml` until a
  later story adds them.

## Migration Plan

None. Existing setups keep working: a fresh form lists no piers, so the add-on
reads `config.yaml` as before. A rollback restores the previous add-on version,
which ignores `options.json`.
