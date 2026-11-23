<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

- `pierpressure/core/sky.py` has `later_night_windows(pier, instant, window,
  reach_end)`, which chains the later nights' local solar days and returns only
  their dark windows. The solar-day bounds it computes are thrown away, but a
  later night's moon needs them (D3).
- `moon_info(pier, window, instant)` takes illumination and phase at `instant`,
  and rise, set and up-during-dark within `window`, null when the window is
  null. It already does what a later night needs, given the right instant.
- `rank_targets(pier, instant, window, moon)` ranks over
  `scored_window(instant, window)`. For a later night the instant is before
  dusk, so the scored window is the whole dark window and every
  `remaining_window` equals `window` (D5). It reads only `moon.illumination`.
- The ranking caches one catalog scan per pier and dark window in
  `_scan_cache`, a bounded LRU of `_CACHE_MAXSIZE = 8`. A cold scan takes
  about 5 s on the dev machine (4.6 s to 5.6 s measured for London nights in
  September and November).
- Measured while planning: ranking the 28-minute dark window at 52° N on
  2026-05-19 took 41 s and returned no target. Every candidate is refined and
  fails the 60-minute minimum, because a target's window cannot be longer than
  the dark window.
- `pierpressure/delivery/mqtt.py` builds a Night sensor's attributes as
  `{"available": true, "night": n, **entry}` from the entry's JSON, so new
  entry keys reach the attributes with no code change (D8).
- `card/src/strip.ts`: `targetLanes()` builds one `TargetLane` per rank from
  the Target sensors, with a single optional `bar`, and the lane holds the
  target's `name` and `id`. `tipKey.target(rank)` keys a bar by rank alone.
  `laterNightLines()` already reads the Night sensors.
- Open story #277 also edits the target lanes. Whichever merges second adapts.

## Goals / Non-Goals

**Goals:**

- One ranking for every night: a later night goes through the same
  `rank_targets` path as tonight, with only its window and moon changed.
- Tonight's fields stay byte-identical to what they are without later nights.
- A recompute rescans no night it scanned before, for any number of piers.
- The card treats a later night's target like tonight's, with one bar per
  night in each lane.

**Non-Goals:**

- A verdict, score, confidence or reasons for a later night, and no
  equipment notes for a later night's top pick.
- Rank sensors or any new entity for later nights.
- A faster scan. The cold first verdict stays about 5 s per night (D6).
- Changing how tonight's moon is computed.

## Test Seams

- **Primary test seam:** `produce_verdict` with a `FixedClock` and a built
  `Conditions` value, asserting on the document, as in
  `tests/test_producer_later_nights.py`. Every night-verdict and
  target-ranking scenario is a test here. The cache scenarios count calls by
  monkeypatching `ranking._scan_night`, as `tests/test_ranking_pipeline.py`
  already does.
- **Existing seams reused:**
  - `MqttDelivery.publish_verdict` with `FakeMqttClient`, as in
    `tests/test_night_sensors.py`, for the ha-delivery scenarios.
  - The card harness in `card/test/harness.ts` with Home Assistant states, as
    in `card/test/targets.test.ts`, `card/test/pan.test.ts` and
    `card/test/tap.test.ts`, for the night-card scenarios.
  - `tests/test_docs.py` and `tests/test_night_card_doc.py` for the docs.
  - `tests/test_golden_verdict.py`. Its fixtures reach no later night, so the
    goldens should not change; check that they do not.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the core's sky, ranking and producer modules, the verdict
  document (two additive keys per later night), the Night sensors' attributes
  (no code change in delivery), and the card's target lanes and tap keys. No
  configuration, provider, scoring rule or entity changes. The cache change
  touches every ranking, tonight's included.

## Decisions

### DD1. Return each later night's solar day with its window

Add `later_nights(pier, instant, window, reach_end)` to `sky.py`, returning a
list of a small frozen dataclass `LaterNightSky(solar_day, dark_window)`. It
holds the loop that `later_night_windows` has today.
`later_night_windows` becomes `[night.dark_window for night in
later_nights(...)]`, so its tests stand unchanged.

- *Alternative:* recompute each solar day in the producer. Rejected: two
  lookups of the same noon can differ by a fraction of a second (the
  later-night-dark-windows design, DD1), and the chained bounds are already
  in hand.

### DD2. A later night's moon is `moon_info` at its solar day's middle

The moon instant is `start + (end - start) / 2` of the later night's solar
day, floored to the whole second (D3). Then call `moon_info(pier, dark_window,
that instant)` unchanged. A null dark window gives null rise, set and
up-during-dark, as tonight's does (D4). For London's first later night after
2026-09-08T18:00Z, the day runs 11:57:48Z to 11:57:27Z next day, so the
instant is 2026-09-09T23:57:37Z.

Flooring keeps the instant a whole second, like every other instant in the
document. It moves illumination by far less than the 0.01 the document
rounds to.

### DD3. Rank several nights in one call

Add `rank_nights(pier, instant, nights)` to `ranking.py`, where `nights` is a
sequence of `(window, moon)` pairs, tonight first. It returns one target list
per pair, in order, by calling the existing per-night path for each.
`rank_targets(pier, instant, window, moon)` becomes
`rank_nights(pier, instant, [(window, moon)])[0]`.

The producer computes tonight's moon and each later night's moon, then calls
`rank_nights` once with tonight and the later nights. It fills each
`LaterNight` with its window, moon and list. Equipment notes still use
tonight's first target only.

- *Alternative:* the producer calls `rank_targets` once per night. Rejected:
  the cache then cannot tell which nights a pier still needs (DD4).

### DD4. The cache keeps the nights of each pier's latest ranking

Replace the bounded LRU with a dictionary keyed by pier id. Each value maps a
scan key (the existing `_cache_key`) to its `_NightScan`. When `rank_nights`
finishes, the pier's map holds exactly the scans of the nights it ranked in
that call; any other scan of that pier is dropped. Other piers' scans are not
touched. Remove `_CACHE_MAXSIZE`.

So the cache holds at most four scans per configured pier (D7). A night that
rolls into the past is dropped on that pier's next recompute, and a new later
night is the only one scanned. Two piers never evict each other, whatever
their number.

- *Alternative:* raise `_CACHE_MAXSIZE` to 32. Rejected: an LRU smaller than
  the number of scans in one pass misses every time, so nine piers or more
  would rescan every night on every recompute.
- *Alternative:* size the LRU from the configured pier count. Rejected: the
  core would need the pier count passed in from the service, for no gain over
  DD4.

### DD5. Skip a night too short for any target

In the per-night path, return an empty list before scanning or looking up the
cache when the scored window is shorter than `MIN_USABLE_WINDOW`. Every
target's remaining window lies inside the scored window and must span that
minimum, so this changes no result. It stops one short later night from
costing 41 s, the case measured above. It also applies to tonight, with the
same result as before.

### DD6. `LaterNight` gains a required `moon` and a `targets` list

In `model.py`, `LaterNight` gets `moon: Moon` (required, with no default) and
`targets: list[Target] = Field(default_factory=list)`, after `dark_window`.
Both reuse the top-level models, so the shapes and serialization match by
construction (D2). Tests that build a `LaterNight` by hand pass a moon.

### DD7. Delivery needs no code change

The Night sensors' attributes already spread the entry's JSON. With ten
targets, an entry is about 4 KB, well under Home Assistant's 16 KB limit for
recorded state attributes. The Verdict attributes keep leaving out
`later_nights`. Only the tests and the README change.

### DD8. A target lane holds one bar per night

In `strip.ts`:

- `TargetLane` becomes `{ rank, label, bars: TargetBar[] }`, and
  `TargetBar` is `Bar` plus `night` (1 for tonight, 2 to 4 for a later night),
  `name` and `id?`. The name and id move from the lane to the bar, because
  each night names its own target.
- `targetLanes()` collects, for each rank, tonight's candidate from the Target
  sensor by today's rule, and each later night's candidate from the entry at
  `rank - 1` of that Night sensor's `targets` attribute by the new rule (D10).
  A rank with any candidate gets a lane. Each candidate whose window is not
  wholly off the axis adds a bar.
- A later night's text comes from a shared helper: `<name> (<id>)`, `<id>`
  alone without a name, `<name>` alone without an id. Its hover text uses
  `targetText()` (D11).
- `tipKey.target(rank, night)` becomes `target:<rank>:<night>`, so a tap box
  follows the bar of the same night in the same lane.
- `renderBar()` takes the bar's own name and id, and the bar gains
  `data-night`, so tests can find a night's bar.

The card's size still counts lanes. A lane filled only on a later night
counts, so the card can be taller on its first draw than before.

### DD9. One decision record

A later night's moon being taken at its local solar midnight, and its targets
ranked over its whole window, gives two new fields a meaning that the frozen
contract then keeps. The ADR step records it, building on ADR-0036 and
ADR-0043. DD1 to DD8 are recoverable from the code and the specs.

## Risks / Trade-offs

- [Risk] The cold first verdict after a restart takes about 20 s per pier,
  and piers run one after another (D6). → Accepted by the user. DD5 stops a
  short night adding about 40 s more. Later recomputes that night use the
  cache.
- [Risk] Python tests that produce a verdict with a forecast reaching later
  nights now rank them, at about 5 s a night, and the suite slows. → Tests
  that do not assert on later nights' targets scan an empty catalog, by
  monkeypatching `ranking._scan_night` with `objects=()` as
  `tests/test_ranking_pipeline.py` does. Scenario tests that share a pier and
  instant share one module-scoped document. The integration task compares the
  suite's run time with `origin/main`'s and records it.
- [Risk] Memory: four scans per pier instead of eight shared. A scan is about
  19 MB on a polar night (the existing estimate of 150 MB for eight) and less
  on shorter nights. → About 75 MB per pier at worst, bounded by the pier
  count. Accepted for a container that serves a few piers.
- [Risk] A recompute right after a night rollover finds tonight's window
  recomputed by `dark_window`, which might differ by a second from the later
  night's chained window in continuous polar night, and rescan it once. →
  Harmless: it costs one scan and changes no result. London's windows match
  exactly, as checked while planning.
- [Trade-off] `rank_targets` called alone for one night drops that pier's
  other cached nights. → Only the producer ranks in production, and it always
  passes every night.
- [Risk] #277 changes the target lanes too. → Whichever story merges second
  rebases onto the other and keeps both behaviours.

## Migration & Rollback

No data migration, no new entity. On the first publish the Night sensors'
attributes gain `moon` and `targets`. An older card ignores them. A newer card
with an older PierPressure finds no `targets` attribute and draws no later
night bars. To roll back, deploy the earlier image: the next publish writes
the Night sensors' attributes without the two keys.
