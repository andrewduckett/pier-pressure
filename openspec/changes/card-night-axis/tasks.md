## 1. The Sun altitude row

- [x] 1.1 [medium] The strip's top row is Sun altitude, read from `sensor.pierpressure_<slug>_sun_altitude`, above the four cloud rows; it uses the cloud rows' hour, clipping, blank-hour and empty-row rules, including an `unavailable` sensor that kept its forecast; the cloud-row tests now expect five rows, with four cloud rows when no cloud sensor exists (design DD1; test: the card harness) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 1.2 [easy] A Sun altitude cell is shaded `#cde2fb` above 0°, `#9ec5f4` above −6°, `#6da7ec` above −12°, `#3987e5` above −18°, and `#0d366b` at −18° or below: 10, 0, −6, −12, −18 and −30 from the spec (design DD2) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 1.3 [easy] A Sun altitude cell's `title` and `aria-label` read `Sun altitude, the hour from 21:00: -14.235°`, while cloud cells keep `%` (design DD1) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)

## 2. The Moon up lane [depends-on: 1]

- [x] 2.1 [medium] Under Cloud high, a lane labelled Moon up, with `data-lane="moon_up"`, draws one grey `#898781` bar per run of consecutive hours above 0° from `sensor.pierpressure_<slug>_moon_altitude`, cut off at the axis ends, with `data-start`, `data-end`, `data-from` and `data-to`: the "Three runs" and "A missing hour" scenarios; the lane keeps its label with no bars when the moon stays down, or when the sensor is missing, `unavailable` or has no forecast list (design DD3, DD6) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 2.2 [medium] A Moon up bar's `title` and `aria-label` read `Moon up from 16:00 to 18:00` when the forecast shows both rise and set, `Moon up until 02:00` or `Moon up from 07:00` when it shows only one, and `Moon up` when it shows neither or the run lasts 24 hours or more (design DD3) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)

## 3. The lines [depends-on: 2]

- [x] 3.1 [medium] When the axis comes from `dark_window`, dashed `#898781` lines with `data-line="dusk"` and `data-line="dawn"` sit at its start and end inside `.lines`, the strip's last child, whose style has its grid placement from the Sun altitude row to the Moon up lane, `inset: 0` and `z-index: 1`; labels `dusk` and `dawn` carry `data-mark` above the top row; hovering shows `Dusk, 20:30` and `Dawn, 03:25`; the fallback axis has neither line (design DD4, DD5, DD8) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 3.2 [medium] A solid red `#e66767` line with `data-line="now"` and label `now` sits at the browser's time while it is on the axis, with `Now, 22:00` on hover, and is missing when the time is before the axis start (design DD5) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 3.3 [medium] With `Date`, `setInterval` and `clearInterval` faked, the now line moves from 22:00 to 22:01 after 60 seconds with no new `hass`, and removing the card leaves `vi.getTimerCount()` at 0 (design DD7) (verify: mise exec -- npm --prefix card test -- strip) (✓ npm test -- strip passed)
- [x] 3.4 [easy] `getCardSize()` returns 6 (design DD9) (verify: mise exec -- npm --prefix card test -- register) (✓ npm test -- register passed)

## 4. Docs and the whole path [depends-on: 3]

- [ ] 4.1 [easy] `docs/night-card.md` describes the Sun altitude row and its sensor, the civil, nautical and astronomical twilight steps, that each altitude is for the start of the hour, the Moon up lane and its sensor and that its hover names only a rise or set inside the forecast, the dusk and dawn lines and their absence with no astronomical darkness, and the now line that moves every minute; its opening no longer says a later release adds dusk, dawn and the moon (test: `tests/test_night_card_doc.py`) (verify: uv run pytest tests/test_night_card_doc.py -k axis)
- [ ] 4.2 [complex] The whole path works: `mise run check` is green, and `mise run dashboard-check` shows the Sun altitude row, the Moon up lane and the dusk, dawn and now lines crossing the strip in a real Home Assistant, beside the YAML strip, checked by eye (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-07: the harness's `cloudEntity` is now `forecastEntity`, since the sun and moon sensors share its shape.
- 2026-11-07: task 3.1's test that the fallback axis has no dusk or dawn line passed on its first run, because the lines did not exist yet. It stays as a guard rather than a red step.
