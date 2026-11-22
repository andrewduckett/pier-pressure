<!-- Plain language: Each task must make sense to an agent and reviewer without the planning conversation. Name an observable outcome, its location when needed, and how to verify it. Preserve checkbox syntax and tags. -->

Read `design.md` (DD1 to DD7) and the three delta specs in `specs/` before
starting. Exact expected values for every core scenario are in
`specs/night-verdict/spec.md`.

## 1. Core: later nights in the verdict document

- [ ] 1.1 [medium] `sky.solar_day_dark_window(pier, day_start, day_end)` returns the astronomical night inside one solar day (design DD1). For London (51.5, −0.12, 30 m) on the solar day from 2026-11-22T11:46:35Z, it is `2026-11-22T18:01:39Z` to `2026-11-23T05:32:17Z`, the same as `dark_window` gives for that night. At 88° N in December it is the whole solar day. On the Scotland (55.0, −3.0, 0 m) solar day from about 2026-08-04T12:18Z it is `(None, None)`. A day that starts dark is clamped to `day_start`. (verify: `uv run pytest tests/test_sky_later_nights.py`)
- [ ] 1.2 [easy] `VerdictDocument` gains `later_nights: list[LaterNight]` as its last key, empty by default, where `LaterNight` holds only `dark_window: DarkWindow` (design DD4). A document with two entries round-trips through JSON unchanged. (verify: `uv run pytest tests/test_model.py`)
- [ ] 1.3 [complex] `produce_verdict` fills `later_nights` (design DD2, DD3). Days chain from the selected night's solar day by `sky.next_solar_day`, up to three. Each day counts only while a timeline hour starts inside it, and no forecast value is read. Pin every scenario of the night-verdict requirements "Later nights follow the selected night…", "A later night counts only while the timeline holds…", "A later night's dark window is the whole…", "A later night with no astronomical darkness…" and "The later nights read only the timeline's hours". Also pin the modified "The document carries the observation" scenario: `later_nights` is the only key after `observation`. (verify: `uv run pytest tests/test_producer_later_nights.py`)
- [ ] 1.4 [easy] Regenerate the committed goldens with `PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py`, and check that the diff only appends a `later_nights` key to each golden document. (verify: `uv run pytest tests/test_golden_verdict.py`)

## 2. Delivery: the Night sensors [depends-on: 1]

- [ ] 2.1 [easy] The Verdict sensor's attributes payload leaves out `later_nights` as well as `timeline`. With both empty, the payload is byte-identical to the document's JSON without those two keys (ha-delivery "The verdict attributes leave out the timeline and the later nights"). (verify: `uv run pytest tests/test_publish.py`)
- [ ] 2.2 [medium] Every publish sends retained discovery for `Night 2`, `Night 3` and `Night 4` (design DD5). Each is a timestamp sensor with unique id `<node>_night_<n>` and the rank sensors' two-entry availability on an `available` flag, and passes the repository's discovery schema. Re-publishing reuses the same topics and ids. (verify: `uv run pytest tests/test_night_sensors.py tests/test_discovery.py`)
- [ ] 2.3 [medium] Every publish writes all three Night sensors' state and attributes (design DD5). A present night has its dusk as `+00:00` ISO 8601 and the attributes `{"available": true, "night": n, "dark_window": {...}}`. A night with a null dusk has the state `None` and keeps its entry. An absent night has the state `None` and `{"available": false, "night": n}`, which also replaces a retained earlier night. (verify: `uv run pytest tests/test_night_sensors.py`)

## 3. Card: later nights' dusk and dawn lines

- [ ] 3.1 [medium] `buildStrip` adds `dusk` and `dawn` lines from each of `sensor.pierpressure_<slug>_night_2` to `_night_4` (design DD6). It reads them through `darkWindow()`, keeps only lines on the axis, and draws them even on the fallback opening axis. It skips a missing, `unavailable` or `unknown` sensor, or an unreadable window, with no message or note. Hover text is `Dusk, HH:MM`. Pin every scenario of night-card "Dusk and dawn lines mark each later night's dark window", "A Night sensor without a readable dark window draws no line" and "The next night with its Night sensor". (verify: `npm --prefix card test -- test/pan.test.ts test/strip.test.ts`)
- [ ] 3.2 [medium] A strip line carries its night, which is 1 for tonight. The tap key is `line:<kind>` for tonight and `line:<kind>:<n>` for a later night, so an open tap box stays on the Night 3 dusk line when the Night 2 dusk line shares the axis (night-card "An item is the same after a redraw…", scenario "Two dusk lines on one axis"). (verify: `npm --prefix card test -- test/tap.test.ts`)

## 4. Docs and the full gate [depends-on: 2, 3]

- [ ] 4.1 [easy] The README's "Home Assistant entities" table has a **Night 2** to **Night 4** row. The row says the state is that night's dusk, the attributes hold its dark window, the sensor is unavailable when the forecast does not reach the night, and it shows unknown when the night has no astronomical darkness. (verify: `uv run pytest tests/test_docs.py`)
- [ ] 4.2 [easy] `docs/night-card.md` says each later night has its own dusk and dawn lines from Night 2 to Night 4, and names `sensor.pierpressure_<pier>_night_2`. It no longer says another night has no dusk or dawn line, and its "No astronomical darkness tonight" help allows for a later night's lines (night-card docs requirements in this change). (verify: `uv run pytest tests/test_night_card_doc.py`)
- [ ] 4.3 [easy] The whole CI gate passes. (verify: `mise run check`)

## Deviations Ledger
