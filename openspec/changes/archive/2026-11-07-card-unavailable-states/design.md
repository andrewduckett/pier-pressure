## Context

The card's strip model, `card/src/strip.ts`, turns Home Assistant's states into
a plain `Strip` object: the axis, the fifteen rows, the Moon up bars, the
target lanes, the lines and the time labels. `card/src/pierpressure-card.ts`
draws that object as a CSS grid, and draws the verdict, score and confidence
above it.

Today a row's sensor reaches `rowCells` through `forecastOf`, which returns
`undefined` for a missing or `unavailable` entity. Every cause of "nothing to
draw" ends as an empty `cells` list, so the model no longer knows why a row is
empty. The Moon up lane reads the same sensor through the same function.

`darkWindow` returns `undefined` for a null `dark_window`, a missing one and an
unreadable one alike, and `stripAxis` then falls back to the day around now.

The offline and "No PierPressure verdict found" messages already exist in
`renderBody`, and draw no strip (`shownStrip`).

## Goals / Non-Goals

**Goals:**

- Decide why a row is empty in the strip model, where the entity and its
  cells are both in hand, so the rule is tested in one place.
- Keep the drawing a plain read of the model: the card renders a message the
  model hands it.

**Non-Goals:**

- Changing the offline or "No PierPressure verdict found" messages.
- Messages for the target lanes, the axis or the time labels.
- Changing which hours draw a cell, or the axis's fallback rule.

## Test Seams

- **Primary test seam:** the card harness, `card/test/harness.ts`: mount the
  real `pierpressure-card` with a fake `hass`, then read rows, messages, lanes
  and the note from the shadow DOM.
- **Existing seams reused:**
  - `card/test/messages.test.ts` already holds the offline and no-verdict
    messages. It takes the row messages, their hover, the Moon up lane's
    message and the darkness note.
  - `card/test/harness.ts` gains a `rowMessage(card, key)` reader that returns
    the message element of a `.row[data-row=<key>]` or of
    `.row[data-lane="moon_up"]`, and a `note(card)` reader.
  - The "a null hour is blank" tests in `rows.test.ts` mount a single null
    point, so their row now also shows `No forecast`. They assert only that
    the hour has no cell, which still holds; they need no change.
  - The existing tests that assert an empty row's text is its label alone
    (`strip.test.ts`, the Cloud high, Sun altitude and Moon up lane cases;
    `rows.test.ts`, the Humidity case) change with the modified requirements,
    to expect the label and the message.
  - `tests/test_night_card_doc.py` takes the docs scenario.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the card's source and tests in `card/`,
  `docs/night-card.md` and its test. No contract, schema, delivery or build
  change.

## Decisions

### DD1. A row carries why it is empty

`Row` gains an optional `missing: Missing`, where

```ts
interface Missing {
  message: "Not found" | "Unavailable" | "No forecast";
  // What hovering over the message shows.
  text: string;
}
```

`buildStrip` computes each row's cells as now, then sets `missing` only when
`cells` is empty, from the row's entity and its id:

| Entity | `message` | `text` |
|---|---|---|
| `undefined` | `Not found` | `<id> is not in Home Assistant` |
| state `unavailable` | `Unavailable` | `<id> is unavailable` |
| anything else | `No forecast` | `<id> has no forecast for these hours` |

Deciding after the cells, not before, keeps one rule for every way a row can
end up empty: no list, an empty list, all nulls, or every point off the axis.
`forecastOf` and `rowCells` stay as they are.

- Alternative: a separate pass that inspects the entity and the forecast
  before drawing. Rejected: it repeats `rowCells`' filters, and the two could
  disagree on whether a row is empty.

### DD2. The Moon up lane takes the Moon altitude row's `missing`

`Strip` gains `moonUpMissing?: Missing`, set to the Moon altitude row's
`missing`. The lane does not decide on its own, so the spec's rule "the same
message as the Moon altitude row" holds by construction, and a moon that stays
down (cells, but no bar) shows no message.

- Alternative: reshaping `moonUp` into `{ bars, missing }`. Rejected: it
  changes every existing reader of `moonUp` for no gain.

### DD3. The card draws a message as text in the track

In a row's or the lane's `.track`, when `missing` is set, the card draws

```html
<span class="missing" data-missing="unavailable" title="…" aria-label="…">Unavailable</span>
```

`data-missing` is the message in lower case with `-` for a space
(`not-found`, `unavailable`, `no-forecast`), for tests and styling.

The track holds only absolutely placed children today, and has no font size or
line height of its own. An inline span would sit on a line box with Home
Assistant's taller line height, and `text-indent` does nothing on an inline
box. So CSS makes `.missing` a block sized to its text:

```css
.missing {
  display: block;
  width: fit-content;
  max-width: 100%;
  box-sizing: border-box;
  padding-left: 4px;
  color: var(--secondary-text-color);
  font-size: 0.75em;
  line-height: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

The block keeps the row 16 px high, the hover target covers only the text, and
a narrow card cuts the message off with `…`. The lines' overlay sits above the
track with `pointer-events: none`, so hovering reaches the message.

### DD4. The darkness note comes from the strip model

`Strip` gains `noDarkness: boolean`. It is true only when
`asRecord(dark_window)` exists and its `start` and `end` are both exactly
`null`. A missing `dark_window`, one null end, or an unreadable time gives
`false`. `darkWindow` and `stripAxis` do not change.

`renderBody` draws `<p class="note" data-note="no-darkness">No astronomical
darkness tonight</p>` after the confidence's `<dl>` and before the strip when
`strip.noDarkness` is true. The note uses the secondary text colour. Because
the strip draws only beside the verdict, the note never shows under the
offline or no-verdict message.

### DD5. The card's size does not change

`getCardSize()` stays 10 plus the target lanes. The note is one short line,
well under one of Home Assistant's 50 px units, and the row messages fit in
rows that already exist.

### DD6. No ADR

Every decision here is local to the card and cheap to reverse. The display
text is not part of the verdict document or the delivery surface.

## Risks / Trade-offs

- [Every row, Sun and Moon altitude too, says "No forecast" beside a live
  verdict when every weather source fails] → The core still computes the
  verdict, the dark window and the targets offline, but the timeline is empty
  (`pierpressure/core/producer.py`, `_timeline`). That is true and worth
  showing. The docs name this cause and point to the health sensors.
- [A row says "No forecast" because no source in the pier's `providers` gives
  that condition for these hours, such as a provider with no cloud layers or a
  short-range model run] → The docs name this cause and point to the
  `providers` setting. The verdict is unaffected.
- [Before the first verdict, a restored entity reads `unknown` and every row
  says "No forecast"] → The verdict's dashes already say PierPressure has not
  published yet. On a first install there is no entity yet, and the card says
  "No PierPressure verdict found" instead.
- [A sensor the user disabled reads "Not found", though it exists] → Home
  Assistant drops a disabled entity from its states, so the card cannot tell
  the two apart. The hover text names the entity id, and the docs say to check
  it under **Settings** > **Entities**.
- [A forecast whose hours all lie off the axis reads "No forecast", though it
  has values] → This happens with a stale state, or when a short-range source
  covers only other hours. The hover says "for these hours".

## Migration & Rollback

N/A. The card is a display; reverting the change restores empty rows.
