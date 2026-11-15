## Context

Home Assistant draws the add-on's Configuration tab from two files:
`ha-addon/config.yaml` (the schema) and `ha-addon/translations/en.yaml` (each
field's label and help text). Piers are a list, so each pier opens in a dialog
built from a plain list of fields. Neither the add-on schema nor the frontend
offers a heading or a divider inside that dialog. Collapsible sections exist
only at the top level of the tab (D13).

The service reads the saved values by field name. It never reads a label or a
description. So a change to `translations/en.yaml` alone cannot change how a
pier is read or what verdict it gets.

`tests/test_ha_addon.py` already checks that every schema key has a name and a
description, that each number names its unit, and that the gate descriptions
name their defaults.

## Goals / Non-Goals

**Goals:**

- Show a pier's four sections inside the one dialog, using only labels and help
  text.
- Ship the help text Andrew tried in the labelled trial. The one change is that
  a description which names another field uses that field's new label or plain
  lower-case words, never an old label such as "Focal length".

**Non-Goals:**

- Any change to `config.yaml`, the service, saved settings or the verdict.
- The interval, Piers and broker text, and the `DOCS.md` walkthrough (#101).

## Test Seams

- **Primary test seam:** `tests/test_ha_addon.py`, which loads both add-on files
  as YAML and checks them. The three new scenarios become tests there.
- **Existing seams reused:** the same file's `addon` fixture and `_load` helper.
  The form-to-verdict tests in `tests/test_addon_options.py` and
  `tests/test_addon_settings.py` stay as they are and prove D17.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** two add-on text files, one test file, `DOCS.md` and one new
  decision record. No Python module under `pierpressure/` changes.

## Decisions

### D1. The section lives in the label, as `<Section>: <field>`

Each pier field's label starts with its section's name, a colon and a space.
The field part is lower case after the colon, as in `Equipment: sensor width`.
`GO` stays upper case, because it is the verdict's own value.

- *Alternative: a fake heading field before each section* (an optional toggle
  or text box labelled as a heading). It looks like a heading, but people can
  click or type in it, the Supervisor saves it, and the service would have to
  drop it. Rejected.
- *Alternative: nested groups per pier* (the grouped trial). Each group became
  a row that opens another dialog, and the Supervisor requires every group to
  be present on save. Andrew rejected its first view (D14).

### D2. The section's introduction opens its first field's help text

The help text of `latitude`, `min_altitude`, `equipment_focal_length_mm` and
`go_threshold` starts with `<Section>:` and one sentence about the section. The
test finds a section's introduction by that prefix, so no other description may
start with a section name and a colon.

### D3. The section map lives in the test, not in the add-on files

The test holds one ordered table of sections and their fields. It checks the
schema's order and every label against it. The add-on files carry no section
key, because Home Assistant would show or save one. A new pier field then needs
a row in this table, as it already needs a label.

### D4. The schema keeps its flat names, by choice

The Supervisor has accepted nested blocks inside a list item since Supervisor
pull request #6171 (September 2025). So the `ha-addon` spec's reason for flat
names, "a form cannot nest", is no longer true. The fields stay flat because the
trial chose the flat layout. That choice is costly to reverse: nesting later
would change every saved pier and the translation in `addon_options.py`. It
gets a decision record (see adr.md), and ADR 0020 stays as written.

### D5. `DOCS.md` takes the new label wherever it names a pier field's label

`DOCS.md` names pier fields by their labels in bold text, in its field tables
and in its label-to-`config.yaml` tables. Each of those takes the new label,
such as **Horizon: points**. Text that names a setting as an idea, such as the
heading "Set a pier's GO threshold and wind-gust limit", stays. Every other
change to `DOCS.md` waits for #101.

## Risks / Trade-offs

- [A long label is cut off in a narrow dialog, such as `Equipment: reducer or
  barlow` on a phone.] → Andrew saw the labels in the trial. The help text below
  each field still names the field in full.
- [The section prefix repeats on every field. Some may read it as noise.] →
  It is the only grouping the dialog can show. Andrew preferred it to the plain
  list.
- [A later pier field is added without a section.] → The test's section table
  fails until the field has a row.

## Migration & Rollback

N/A. No field name, type or saved value changes, so saved settings load as
before. To roll back, revert the commit that changes `translations/en.yaml`.
