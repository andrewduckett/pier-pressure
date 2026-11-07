## 1. The rows

- [x] 1.1 [medium] The strip has fifteen labelled rows in the spec's order, each reading `sensor.pierpressure_<slug>_<key>` (Rain chance reads `precipitation_probability`), with `data-row` set to the key; a value fills the hour that starts at its `datetime`, cut off at the axis ends; a missing, `unavailable` or forecast-less sensor leaves its row labelled and empty; the `strip.test.ts` assertions that depend on the row count (row order, the row above the Moon up lane, the lines' `grid-row`, `grid-template-rows`) now expect fifteen rows (design DD1, DD5; test: the card harness, `card/test/rows.test.ts`) (verify: mise exec -- npm --prefix card test -- rows strip) (✓ npm test -- rows strip passed)
- [x] 1.2 [easy] A Rain chance value fills the hour that ends at its `datetime`: a value at 22:00 UTC fills 21:00 to 22:00, and the spec's axis-end scenario holds (design DD1) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [x] 1.3 [easy] Moon altitude, Wind gust and Wind speed cells take the spec's shades: −10, 0, 3, 6, 12, 18, 24, 30 and 60 for the moon; 0, 6.9, 7, 41 and 42 for gusts; 21 for wind speed (design DD2) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [x] 1.4 [easy] Seeing and Transparency cells are darker when worse: 1, 0.8, 0.5 and 0 give `#cde2fb`, `#9ec5f4`, `#256abf` and `#0d366b`, and 1.2 gives `#cde2fb` (design DD2) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [x] 1.5 [easy] Temperature and Dew point share one scale, −8 to 25 °C from the spec, and Humidity and Rain chance step by 15% (design DD2) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [x] 1.6 [medium] A Wind direction cell has no shade and no `data-shade`, carries `data-arrow` with `(v + 180) mod 360` (225 gives 45, 0 gives 180), and holds an `<svg>` whose group is rotated by that angle; a null hour has no cell; shaded cells have no `data-arrow` (design DD2, DD3) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)

## 2. Hover and size [depends-on: 1]

- [x] 2.1 [easy] Hovering shows each row's unit: `Wind gust, the hour from 21:00: 12.5 km/h`, `Temperature, the hour from 21:00: 4.2 °C`, `Seeing, the hour from 21:00: 0.62`, and `Rain chance, the hour from 21:00: 40%` for a value at 22:00 (design DD1) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [x] 2.2 [easy] Hovering over a Wind direction cell names the compass point: 225 reads `225° from SW`, 22.5 reads `22.5° from NE`, and 350 reads `350° from N` (design DD2) (verify: mise exec -- npm --prefix card test -- rows) (✓ npm test -- rows passed)
- [ ] 2.3 [easy] `getCardSize()` returns 10 (design DD4) (verify: mise exec -- npm --prefix card test -- register)

## 3. Docs and the whole path [depends-on: 2]

- [ ] 3.1 [easy] `docs/night-card.md` lists the fifteen rows and their sensors, gives each shaded row's lightest and darkest and says darker means worse for Seeing and Transparency, says Temperature and Dew point share the same scale, that a Rain chance cell fills the hour before its time, and that a Wind direction arrow points the way the wind blows to; its opening no longer says a later release adds the other conditions (test: `tests/test_night_card_doc.py`) (verify: uv run pytest tests/test_night_card_doc.py -k rows)
- [ ] 3.2 [complex] The whole path works: `mise run check` is green, and `mise run dashboard-check` shows the fifteen rows, their shades and the wind arrows beside the YAML strip in a real Home Assistant, checked by eye (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-07: in task 1.1, the ten new rows start with the cloud shade and no unit, so each later task's test goes red first. The Seeing null-hour test passed on its first run, because a missing row has no cells either; it stays as a guard.
- 2026-11-07: in task 1.4, the Transparency-above-1 test passed on its first run, because the cloud shade also gives 1.2 the lightest blue. It stays as a guard for the clamp.
- 2026-11-07: in task 1.5, the Humidity and Rain chance shade tests passed on their first run, because task 1.1 gave those rows the cloud shade they keep. They stay as guards.
- 2026-11-07: in task 1.6, the tests that a shaded cell has no arrow and a null Wind direction hour has no cell passed on their first run, since no arrow existed yet. They stay as guards.
- 2026-11-07: in task 2.1, the Seeing and Transparency hover tests passed on their first run, because those rows have no unit from the start.
- 2026-11-07: the row table's hover writer, design DD1's `value(v)`, is named `reading`, so it does not read as the cell's own `value`.
