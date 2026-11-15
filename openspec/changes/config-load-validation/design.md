## Context

- `pierpressure/core/config.py` reads YAML in two places, both with
  `yaml.safe_load`, which follows YAML 1.1:
  - `read_config_mapping` reads the whole `config.yaml`, for Docker, source and
    the add-on.
  - `HorizonConfig._parse_points_text` reads horizon points written as text. The
    add-on form's `horizon_points` arrives here as text, so the form and the file
    share this reader on purpose (addon-options-core-validates D1).
- By the time a pier is checked, `045` is already the integer 37 and `1:30` is
  already 90. A check on the parsed value cannot tell them from a real 37 or 90.
  So the fix has to be in the reader.
- PyYAML first matches a plain scalar against a pattern to pick its tag, such as
  `int`, then calls that tag's constructor. In YAML 1.1, `045` and `-045` match
  the `int` pattern as octal, and `1:30` matches it as base 60. `1:30.5` matches
  the `float` pattern as base 60. `08` and `090` match no number pattern, so they
  stay text, and a number setting's check then converts them to 8 and 90.
- `build_config` checks that `piers` is a list, then hands the raw entries to
  `validate_piers`, which checks each pier on its own and skips a bad one. No
  step compares ids.
- Inside the add-on, `combine_settings` already stops on an id repeated in the
  add-on's `config.yaml` (`_file_piers`), then passes the combined settings to
  `build_config`. A form that lists an id twice passes the combine today.

## Goals / Non-Goals

**Goals:**

- One YAML reader for the core, used by both read sites, so the file and the
  form cannot drift apart.
- A repeated pier id stops startup in `build_config`, the one place every
  install type passes through.

**Non-Goals:**

- No other YAML 1.1 rule changes, such as `yes` and `no` read as true and false.
- No change to the add-on's combine step or its error text.
- No change to the per-pier error text for a bad horizon point.

## Test Seams

- **Primary test seam:** the core's configuration loaders, driven from a
  `config.yaml` written to a temporary folder: `load_config` in
  `tests/test_config.py` and `tests/test_horizon_config.py`. A real file is the
  only way to prove the whole-file reader, because a mapping built in Python
  never passes through YAML.
- **Existing seams reused:** `load_app_config` in `tests/test_main.py`, with
  `SUPERVISOR_TOKEN` set and a saved form, for the two add-on scenarios (a
  repeated form id, and padded or base-60 form horizon points).

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** configuration loading in `pierpressure/core/config.py`, for
  every install type. The reader change touches every value in `config.yaml`,
  but only values written with leading zeros or colons change. No topic, entity,
  or verdict field changes.

## Decisions

### DD1: Change two constructors, not the YAML patterns

A private loader class in `config.py` extends `yaml.SafeLoader` and replaces only
the `int` and `float` constructors. A private `_read_yaml(text)` helper loads with
it. `read_config_mapping` and `_parse_points_text` both call the helper.

- `int`: a value that holds a colon is returned as the text written. A value
  that, after its sign, starts with `0` followed by more digits or underscores
  is read as a decimal number, keeping its sign. Any other value goes to the
  safe loader's own constructor, so `0`, `0x1A`, `0b11` and `1_000` keep their
  meaning (D5).
- `float`: a value that holds a colon is returned as the text written. Any other
  value goes to the safe loader's own constructor.

Because the patterns do not change, `08` and `090` still reach the settings as
text, as they do today. A number setting converts them, and a text setting such
as `id` keeps them as text (D6).

Alternatives:

- Replace the patterns with the YAML 1.2 core schema. This also changes
  booleans, `0o17`, underscores and other forms the brief left alone (D5), and
  it would make `id: 08` a number.
- Add a YAML 1.2 library, such as ruamel.yaml. A new dependency for two rules,
  with its own differences from PyYAML to test.
- Walk the parsed result and fix numbers afterwards. Impossible: `045` and `37`
  are the same integer once parsed.

### DD2: Leave the base-60 error to the settings check

`1:30` reaches `horizon.points` as text. The points field takes numbers, so the
settings check rejects it with its own message and a location under
`horizon.points`, and `validate_piers` logs the skip with the pier's id. This
needs no new error text, and it is the same path a form pier takes (D3).

Alternative: a custom message such as "`1:30` is not a decimal number". Clearer,
but it adds a check that duplicates the type check and words one case
differently from every other bad value.

### DD3: Check for repeated ids in `build_config`, before any pier is checked

A private helper takes the raw piers list and returns each text `id` that
appears more than once, in the order of its first repeat. Entries that are not
mappings, or whose `id` is missing or not text, are ignored here; the per-pier
check reports them. Ids are compared exactly, so letter case counts (D8, D9).

If the helper returns any id, `build_config` raises one `ConfigError`:
`Pier ids must be unique; listed more than once: 'backyard'`. Each id is written
with `repr`, as `addon_settings.py` already does, so a line break shows as `\n`
and the error stays on one line. Several ids are joined with `, ` (D11).

The check sits before `validate_piers`, because the error belongs to the whole
list, not to one pier, and because the add-on and the plain file both pass
through `build_config` (D7, D10).

Alternative: check inside `validate_piers`. That function's contract is "skip
the bad pier, keep the rest", and it returns a list rather than raising.

### DD4: No add-on code change

A form that lists `backyard` twice passes `combine_settings`, and its two piers
reach `build_config`, which stops. When the add-on's `config.yaml` also repeats
an id, the combine stops first with its own error, as today. The add-on's
behavior is covered by tests through `load_app_config` (D10).

### DD5: Document the rules in the README

The configuration table's `id` row says that each pier needs its own id. The
`horizon` row, or a short note under the table, says that a zero-padded number
such as `045` reads as 45, and that `1:30` is not a number (D12).

## Risks / Trade-offs

- [A setup that runs today with a repeated id stops after the upgrade] → The
  error names the id. Such a setup was already publishing one pier's verdict over
  the other's.
- [A number setting written with a leading zero takes a new value, such as
  `port: 01883`, which YAML 1.1 already read as text and still does] → Only
  values YAML 1.1 read as octal change, and each now means what was written.
- [Adding constructors to the subclass changes `yaml.safe_load` for the whole
  process] → PyYAML copies the constructor table on a subclass's first
  `add_constructor`. A test asserts that `yaml.safe_load("045")` is still 37.
- [`1:30` in a text setting now loads where it used to fail] → It is text, which
  is what the user wrote. The settings check still judges it.

## Migration & Rollback

N/A. No stored data or delivery surface changes. Rollback is a revert of the
change's commits. The release notes should say that a repeated pier id now
stops startup.
