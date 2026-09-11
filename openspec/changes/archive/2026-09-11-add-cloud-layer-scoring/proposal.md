## Why

The shipped verdict scores cloud as a single total-cloud percentage. For
astronomy that conflates two very different skies: low cloud simply blocks the
view, while high, thin cirrus can leave a "clear" total reading yet wreck
transparency for deep-sky work. Open-Meteo already reports the low/mid/high
split (the base provider fetches it), and a discarded early attempt at M3 scored
high, thin cloud on its own term — capability the shipped verdict lacks. This
change adds that cloud-layer detail to the score.

## What Changes

- Carry the cloud-component split (low / mid / high) through the conditions model
  and the provider layer, alongside the existing total cloud cover.
- Add a **high/thin-cloud** term to the banded score: a distinct, itemized
  `reasons[]` penalty for high cirrus, separate from the total-cloud term, so a
  low total with high cirrus is scored honestly rather than as a clear night.
- Keep this **additive**: no new gate, no change to existing field meanings or the
  delivery surface. Existing verdicts move only by the new term; gates, bands, and
  confidence are otherwise unchanged and covered by tests.

Depends on **M3.5** (`add-per-source-conditions-seam`): the per-source group model
lands first, and this change extends `CloudHour`/`CloudGroup` with the component
split. Do not start this change until M3.5 is merged.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `conditions`: the cloud group carries the low/mid/high component split in
  addition to total cloud cover, each component independently present-or-absent.
- `night-verdict`: the score gains an itemized high/thin-cloud penalty term,
  distinct from the total-cloud term, reported as its own `reasons[]` line.

## Impact

- **Core:** `pierpressure/core/conditions.py` (cloud-component fields),
  `core/scoring.py` (the high-cloud term and its reason).
- **Provider layer:** `pierpressure/conditions/open_meteo.py` already fetches the
  components; the parser carries them through instead of collapsing to total.
- **Tests:** conditions-model, scoring, and verdict fixtures gain component data
  and the new term; the M3.5 golden output is re-based once (the score legitimately
  changes here).
- **No change** to MQTT topics/entities, gates, the document's existing fields, or
  dependencies.
