## Context

- The card is one Lit element, `pierpressure-card`, in
  `card/src/pierpressure-card.ts`, built by Vite into one file
  (`pierpressure-card.js`). The same file pushes the card's entry onto
  `window.customCards`, guarded so a second load adds nothing.
- `card/src/entity.ts` holds the slug rule (`pierSlug`) and the entity id
  builders. `pierSlug` of a slug is the slug itself, so a slug works as a `pier`
  value.
- `setConfig` keeps only `type` and `pier`, and throws "pier is required" when
  `pier` slugs to nothing. The editor does not change that.
- The design follows Home Assistant's card API as its dashboard editor uses it.
  The version is 2026.10, which `compose.yaml` pins for
  `mise run dashboard-check`.
  - A picker entry with `preview: true` makes the picker draw the card. If the
    card throws while the picker builds it, the picker shows the entry's
    description instead.
  - `static getStubConfig(hass)` gives the starting configuration. The picker
    sets `type` itself and merges what the card returns.
  - `static getConfigElement()` returns the editor element. Home Assistant sets
    its `hass` property and calls its `setConfig(config)`.
  - The editor reports a change with a `config-changed` event that carries
    `detail.config`, bubbles and is composed.
- The Verdict sensor's attributes are the verdict document without `timeline`,
  so `attributes.pier` is the pier id (ledger D2).
- Tests run in Vitest with happy-dom, through `card/test/harness.ts`. Home
  Assistant's own elements, such as `ha-form`, do not exist there.

## Goals / Non-Goals

**Goals:**

- One pure function turns Home Assistant's states into the list of piers, so the
  editor and the starting configuration agree on the list and its order.
- The editor stays inside the one built file and adds no dependency.
- The editor field looks and behaves like Home Assistant's own fields.

**Non-Goals:**

- Fields for anything but `pier`.
- Reading the device or entity registry (ledger D3).
- Changing what `setConfig` accepts, or the card's messages.

## Test Seams

- **Primary test seam:** the card's Vitest suite under `card/test/`. A new
  `editor.test.ts` mounts `pierpressure-card-editor` with a stand-in `ha-form`
  element. Like Home Assistant's, it shows each field's label from its
  `computeLabel` callback, records the `schema` and `data` it is given, and can
  fire `value-changed`. The pier list function and `getStubConfig` are tested
  as plain functions.
- **Docs seam:** `tests/test_night_card_doc.py`, which already tests every
  `docs/night-card.md` requirement, gains the visual editor scenario.
- **Existing seams reused:** `card/test/harness.ts` (`verdictEntity`, the
  `HomeAssistant` shape), and `card/test/register.test.ts` for the picker entry.
  The real Home Assistant in `mise run dashboard-check` is the by-eye check
  (ledger D14), not an automated seam. Its two PierPressure dashboards are in
  YAML mode and cannot be edited, so the check uses the Overview dashboard at
  `/lovelace`, which Home Assistant keeps in storage mode.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. One package on established patterns, but it adopts a new
  part of Home Assistant's card API and one of Home Assistant's own elements.
- **Blast radius:** `card/`, `docs/night-card.md` and its test,
  `tests/test_night_card_doc.py`. The card's
  rendering is unchanged. The core, the verdict document and MQTT delivery are
  untouched.

## Decisions

### D-1. The pier list is a pure function in `entity.ts`

`listPiers(states)` returns `{ value, label }[]`. It keeps each state id that
matches `^sensor\.pierpressure_(.+)_verdict$` and whose entity is not
`undefined`, and takes `<slug>` from the match. `label` is `attributes.pier` when it is a non-empty string, else
`<slug>`. `value` is `attributes.pier` when `pierSlug(attributes.pier)`
equals `<slug>`, else `<slug>` (ledger D4). Sorting uses
`label.localeCompare(other.label)`, then `value` for a tie, so the order is
alphabetical as a reader expects and stable.

The regular expression's `.+` is greedy, so
`sensor.pierpressure_a_verdict_verdict` gives the slug `a_verdict`, which is
what Home Assistant would name a pier called `a verdict`.

*Alternatives:* reading `hass.entities` or `hass.devices` for MQTT devices
named "PierPressure …". Rejected: the card reads only published states, and a
renamed device would break it (ledger D3). Building the list inside the editor
element: rejected, because `getStubConfig` needs the same list.

### D-2. The editor is a second Lit element in the same file

`pierpressure-card-editor` is a `LitElement` in a new `card/src/editor.ts`,
imported by `pierpressure-card.ts`, so Vite still bundles one file. It is
defined with the same "only if not defined yet" guard as the card.
`PierPressureCard.getConfigElement()` creates it.

The editor keeps the whole configuration it was given, not only `type` and
`pier`, so a key it does not edit survives (ledger D9).

### D-3. The field is Home Assistant's `ha-form` with a select selector

The editor renders `<ha-form>` with one schema entry: `name: "pier"` and
`selector.select` with `custom_value: true`. Its `options` are exactly
`listPiers(hass.states)`, and nothing else, so no other value joins the list.
`ha-form` takes labels from a callback, not from the schema, so the editor
passes `computeLabel` returning **Pier**.

Home Assistant draws that selector as its combo box. The open list shows each
pier's label, and the field takes typed text (ledger D7). The closed field
shows the stored `pier` value itself, such as `dong_jing` for `東京`, so the
user sees exactly what the configuration holds. It shows a value that is not in
the list just the same, so the editor passes
`data = { pier: <config.pier when it is a string, else ""> }` and never adds
options (ledger D6).

On `value-changed`, the editor reads `detail.value.pier`. Clearing the field
gives `undefined`, which the editor treats as `""`. If the result differs from
the current `pier`, the editor dispatches `config-changed` with
`{ ...config, pier }`. An unchanged value reports nothing, so opening the editor
never rewrites the configuration (ledger D6). An emptied field reports
`pier: ""`, and the edit dialog's preview then shows the card's
"pier is required".

*Alternatives:* a native `<input list>` with a `<datalist>`. Rejected:
browsers filter a datalist by the text already in the field, so once a pier is
set the list shows only that pier. A native `<select>` with a separate text
field: rejected, because it is two controls for one key, and it does not look
like Home Assistant. `static getConfigForm()`, Home Assistant's declarative
form: rejected, because it is static and gets no state, so it cannot list the
piers.

### D-4. The editor makes sure `ha-form` is loaded

Home Assistant loads `ha-form` lazily. When the editor connects and
`ha-form` is not defined, it asks a built-in card that has a form editor,
`hui-entities-card`, for its config element, which loads `ha-form`. It then
re-renders when `customElements.whenDefined("ha-form")` resolves. Other HACS
cards use the same step. If neither element exists, the editor still shows its
message and nothing breaks.

### D-5. The "no piers" message is the editor's own text

When `listPiers` is empty, the editor shows "No PierPressure piers found" above
the field, as plain text styled with `--secondary-text-color`. The field stays,
so a pier can still be typed (ledger D8).

### D-6. The picker entry and the starting configuration

The `window.customCards` entry gains `preview: true`.
`PierPressureCard.getStubConfig(hass)` returns
`{ type: "custom:pierpressure-card", pier: listPiers(hass.states)[0].value }`,
or only the `type` when the list is empty (ledger D10, D11). Returning `type`
as well is harmless, since the picker sets the same value.

### D-7. Docs

`docs/night-card.md`, "Add the card to a dashboard": pick **PierPressure** in
the card picker, then pick the pier from the **Pier** list, or type it. YAML
stays as the other route, unchanged. "Find your pier's entity id" adds that the
**Pier** list already uses the real id, so the step is needed only for YAML.
The "If something looks wrong" section does not change: it lists the card's
messages, and "No PierPressure piers found" is the editor's.

## Risks / Trade-offs

- [`ha-form` and its select selector are Home Assistant's internal elements,
  not a published API, and can change] → The editor depends on three shapes
  only: the selector schema, `computeLabel` and the `value-changed` event. The
  check in `mise run dashboard-check` runs against the pinned Home Assistant.
  If the editor ever breaks, the card's YAML route keeps working.
- [Forcing `ha-form` to load relies on `hui-entities-card` having a form editor]
  → It is a fallback only for when `ha-form` is not already defined. The
  by-eye check confirms the editor draws on a fresh page load.
- [A sensor named `sensor.pierpressure_<x>_verdict` that is not PierPressure's
  would be listed] → Only PierPressure creates that prefix; a stray match
  appears as one extra list item and changes nothing else.
- [Sorting with `localeCompare` follows the browser's locale] → Only the
  order of the list depends on it; the tests use plain ASCII names whose order
  is the same in every locale.

## Migration & Rollback

N/A. A card configured in YAML keeps working unchanged. Rolling back removes the
editor; Home Assistant then shows its YAML editor for the card, as today.
