## Why

The verdict document already gives, for each hour, the lowest and highest cloud
cover any forecast gave (#158), but nothing publishes those two values, so no
card can read them. Confidence sums up forecast agreement for the whole night;
it cannot show Andrew which hours the forecasts disagree on. The card is now
far enough along (#181, #185) to draw them.

## What Changes

- Two new timeline sensors per pier, **Cloud cover min** and **Cloud cover
  max**, published like the other fifteen and placed last in the sensor table
  (D3, D4, D5). The core and the verdict document do not change (D2).
- A new **Cloud range** row on the card, directly under Cloud cover. Each hour
  with both values draws a shaded bar from the lowest to the highest value on a
  0 to 100% scale; other hours stay blank (D6, D7, D8). Hovering shows the two
  values (D9).
- When the row has no bar at all it says why: `Not found`, `Unavailable`, or
  `Needs two forecasts` (D10, D11). It is never hidden (D12).
- Docs: the sensors in `docs/night-timeline.md` and the README, and the row in
  `docs/night-card.md`, including how to add a second cloud provider (D15).
- Not changed: the Cloud cover row (D6), the YAML dashboard (D16), and how
  agreement and confidence are measured (D17).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ha-delivery`: the further timeline sensors gain `cloud_cover_min` and
  `cloud_cover_max`, with their names, unit and place in the publish order.
- `night-card`: the strip gains the Cloud range row, its drawing, hover text and
  messages, and `docs/night-card.md` describes it.

## Impact

- `pierpressure/delivery/mqtt.py`: two rows appended to `TIMELINE_SENSORS`.
  Every publish sends six more retained messages per pier (two discovery
  configs, two states, two attribute payloads).
- `card/src/strip.ts` and `card/src/pierpressure-card.ts`: the new row, its
  drawing and its messages.
- Tests: `tests/test_timeline_sensors.py` and the card's Vitest suite; tests that
  count the timeline sensors or rows change their expected numbers.
- Docs: `docs/night-timeline.md`, `docs/night-card.md`, `README.md`.
- Home Assistant: two new entities per pier. Users who exclude the timeline
  sensors from the recorder need to add the two new ones.
