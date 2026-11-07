## 1. The strip model and its entities

- [x] 1.1 [easy] `pierEntityId("Back-Yard", "cloud_cover")` gives `sensor.pierpressure_back_yard_cloud_cover`, and `verdictEntityId` gives the same ids as before through it (design DD8) (verify: mise exec -- npm --prefix card test -- entity) (✓ npm test -- entity passed)
- [x] 1.2 [medium] The strip's axis runs from 4 hours before `dark_window.start` to 5 hours after `dark_window.end`, and falls back to 6 hours before `Date.now()` to 18 hours after for a missing, null, unreadable, inverted or over-48-hour window, and for a Verdict sensor with no attributes (design DD1, DD7; test: the card harness with `vi.setSystemTime`, reading `data-axis-start` and `data-axis-end`) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)

## 2. The cloud rows [depends-on: 1]

- [x] 2.1 [medium] Below the verdict lines, the card draws the rows Cloud cover, Cloud low, Cloud mid and Cloud high, in that order, each with its label; it draws no strip when the Verdict sensor is missing or unavailable, or before `hass` is set (design DD2, DD3) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 2.2 [medium] Each forecast point fills the hour from its `datetime` as one cell, positioned in percent of the axis; hours wholly outside the axis get no cell, and a cell cut off at an axis end is flush with it, with `data-from` and `data-to` giving its drawn bounds (design DD2, DD3) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 2.3 [easy] A cell is shaded in the seven blues by shade step `min(6, floor(v / 15))`, clamped at 0: 0 gives `#cde2fb`, 44 gives `#6da7ec`, 100 gives `#0d366b` (design DD7) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 2.4 [medium] A null or non-number value, an hour with no point, a point without a readable `datetime`, a sensor that is missing or `unavailable` (even with a `forecast`), and a `forecast` that is missing or not a list each leave blank hours or an empty labelled row, and the card never throws (design DD7) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 2.5 [medium] Each cell's `title` and `aria-label` read `<row>, the hour from <HH:MM>: <value>%` in `hass.config.time_zone` on a 24-hour clock with Latin digits: `21:00` for 12:00 UTC in `Asia/Tokyo`, and `21:00` in a browser set to `ar-EG`; a missing or invalid time zone falls back to the browser's (design DD4, DD5) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)

## 3. The time labels [depends-on: 2]

- [ ] 3.1 [medium] The axis carries a time label at each whole hour strictly inside it whose local hour is a multiple of 3, or of 6 on an axis over 24 hours, dropping a repeat of the previous label less than 3 hours after it: the UTC, Kolkata, polar-night and Athens scenarios from the spec (design DD6) (verify: mise exec -- npm --prefix card test -- strip)
- [ ] 3.2 [easy] `getCardSize()` returns 5, `getGridOptions()` returns `columns: "full"`, and the card picker's description is "Tonight's verdict and night strip for one pier." (design DD9) (verify: mise exec -- npm --prefix card test -- register)

## 4. Docs and the whole path [depends-on: 3]

- [ ] 4.1 [easy] `docs/night-card.md` describes the cloud rows and `sensor.pierpressure_<pier>_cloud_cover`, the axis span and its fallback, clear to overcast shades, blank hours, what hovering shows, and Home Assistant's time zone (test: `tests/test_night_card_doc.py`) (verify: uv run pytest tests/test_night_card_doc.py -k strip)
- [ ] 4.2 [complex] The whole path works: `mise run check` is green, and `mise run dashboard-check` shows the card's four cloud rows beside the YAML strip in a real Home Assistant, checked by eye (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-07: each cell also carries its shade in `data-shade` (design DD3 named only `style`), so the tests read the hex colour without depending on how happy-dom rewrites `background-color`.
- 2026-11-07: task 2.3 skips a value that is not a finite number, because a shade needs a number. Some of task 2.4's cases therefore pass on their first run, as guards rather than red steps.
- 2026-11-07: the Tokyo hover test reads 21:00 UTC as `06:00`, not 12:00 UTC as `21:00` as in the spec scenario, because 12:00 UTC falls outside the test night's axis. It proves the same rule.
