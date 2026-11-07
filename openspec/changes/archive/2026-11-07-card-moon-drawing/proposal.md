## Why

The card shows tonight's verdict and the hour-by-hour strip, but not the moon's
phase or brightness, which most astronomy apps show at a glance. The Verdict
sensor already carries the moon's illumination, phase, moonrise and moonset, so
the card can show them without any new data (D3). The cloud strip it sits beside
(#181) is in place.

## What Changes

- A **Moon** section on the card, beside the Verdict, Score and Confidence lines
  and above the strip (D5). It holds a drawing of the moon and, beside it, the
  phase name, the illumination as a whole percent, moonrise and moonset (D4,
  D9, D10, D11).
- The drawing lights the illumination's share of the disc, up to a terminator
  (D6). Waxing phases are lit on the right and waning on the left, mirrored
  when Home Assistant is south of the equator (D7). `new` is unlit and `full`
  is fully lit (D8).
- Each text shows a dash when its value is missing; the drawing shows only when
  both illumination and phase are valid (D13). The drawing has a text
  alternative (D14). An offline PierPressure or a missing Verdict sensor shows
  no moon (D15).
- Docs: `docs/night-card.md` describes the Moon section and how to read it
  (D17).
- Not changed: the verdict document, the sensors (D2), the Moon up lane (D12)
  and the YAML dashboard (D17).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the card gains the Moon section, its drawing, its texts and
  their dashes, and `docs/night-card.md` describes it.

## Impact

- `card/src/`: the Moon section's reading of the `moon` attribute, its drawing
  and its layout beside the verdict lines.
- Tests: the card's Vitest suite.
- Docs: `docs/night-card.md`.
- Home Assistant: no new entities. The card reads Home Assistant's latitude to
  choose which side is lit (D7).
