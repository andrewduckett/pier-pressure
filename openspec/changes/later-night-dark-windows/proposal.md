## Why

The night strip pans across about 72 hours of forecast, but only tonight has
dusk and dawn lines. On the second and third nights, Andrew and the adopter see
weather rows with no frame, so they cannot tell which hours are dark. This is
the first story of epic #299. It carries later nights through the core, the
verdict document, the delivery and the card with the smallest payload, one dark
window per night, so the targets story (#319) only adds fields.

## What Changes

- The core computes up to three **later nights** after the selected night, one
  per local solar day, while the timeline holds an hour that starts inside that
  solar day (D1, D2). With no provider data there are no later nights.
- Each later night has a dark window: the whole astronomical night inside its
  solar day, however short, or null bounds when it has no astronomical
  darkness (D4). On a day when polar night starts or ends, the window stops at
  the solar day's edge (D14).
- The verdict document gains a `later_nights` list after `observation`. Each
  entry holds a `dark_window` in the top-level shape (D3). This is additive:
  every existing field keeps its meaning and position.
- The Verdict sensor's attributes leave out `later_nights`, as they already
  leave out `timeline` (D5).
- Each pier gets three new sensors, Night 2 to Night 4
  (`sensor.pierpressure_<slug>_night_<n>`). The state is that night's dusk as a
  timestamp, and the attributes hold its entry. The sensor is unavailable when
  its night is not in `later_nights`, and shows unknown when the night has no
  darkness (D6, D7).
- The card draws dusk and dawn lines from each Night sensor's `dark_window`,
  whenever their time is on the axis (D8). It adds no darkness note for later
  nights (D9). Tonight's lines and the opening axis do not change (D13).
- A decision record settles the document shape and the delivery (D12).
- The README and `docs/night-card.md` describe the Night sensors and the
  later-night lines (D12). The README's entity table, MQTT topics, verdict
  document and "Removing the entities" sections all name them.

No change is **BREAKING**. The narrative is unchanged (D11). Tonight's
`dark_window` is unchanged too; a separate bug covers the faults the plan
review found in it (D16).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `night-verdict`: the document structure gains `later_nights`. New requirements
  say which later nights exist and what each one's dark window is.
- `ha-delivery`: the Verdict attributes also leave out `later_nights`. New
  requirements cover the Night 2 to Night 4 sensors: discovery, state,
  attributes and availability.
- `night-card`: new requirements make the card draw each later night's dusk and
  dawn lines from the Night sensors, and make the docs describe them.

## Impact

- **Core:** `pierpressure/core/sky.py` (a later night's solar day and dark
  window), `pierpressure/core/model.py` (`VerdictDocument`, a later-night entry
  model), `pierpressure/core/producer.py` (fills `later_nights`).
- **Delivery:** `pierpressure/delivery/mqtt.py` (Night sensor discovery, state
  and attributes; the Verdict attributes leave out `later_nights`).
- **Card:** `card/src/strip.ts` and `card/src/pierpressure-card.ts` (read the
  Night sensors and draw their lines), with tests in `card/test/`.
- **Docs:** decision records in `docs/decisions/`; `README.md`'s
  "Home Assistant entities", "MQTT topics", "The verdict document" and
  "Removing the entities" sections; `docs/night-card.md`.
- **Contract:** additive only. Home Assistant gains three entities per pier, and
  existing topics, entities and fields are unchanged.
- **Dependencies:** none.
