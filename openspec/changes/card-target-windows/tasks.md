## 1. The target lanes

- [x] 1.1 [medium] Under the Moon up lane, the strip has one lane per rank from Target 1 to Target 10 that has a target tonight, in rank order with no gap: `.row[data-lane="target_<n>"]` labelled `Target <n>`, reading `sensor.pierpressure_<slug>_target_<n>`, with one bar carrying `data-start`, `data-end`, `data-from` and `data-to` from the window's `start` and `end`; `pier: Back-Yard` reads `sensor.pierpressure_back_yard_target_1` (design DD1, DD2; test: the card harness, new `card/test/targets.test.ts`, with `targetEntity` and `targetLanes` in `card/test/harness.ts`) (verify: mise exec -- npm --prefix card test -- targets) (✓ npm test -- targets passed)
- [x] 1.2 [easy] A rank leaves no lane, and the card does not throw, when its sensor is missing, or its state is `unavailable` (even with a stale `window`), `unknown` or empty, or its `window` ends before it starts, has no `end`, or has a `start` of `soon`; with no Target sensor at all the rows and the Moon up lane draw as usual (design DD1) (verify: mise exec -- npm --prefix card test -- targets) (✓ npm test -- targets passed)
- [x] 1.3 [easy] A bar is cut off at an axis end (a window from 06:00 to 10:00 on an axis ending 08:25 gives a bar from 06:00 to 08:25), and a window wholly off the axis, or one that only touches an axis end, keeps its lane with no bar (design DD1) (verify: mise exec -- npm --prefix card test -- targets) (✓ npm test -- targets passed)
- [x] 1.4 [easy] A target bar's text is the Target sensor's state, such as `Andromeda Galaxy`, and the bar carries `data-target`, drawn violet `#6250d6` with white text indented 4 px and cut short with an ellipsis (design DD2) (verify: mise exec -- npm --prefix card test -- targets) (✓ npm test -- targets passed)
- [x] 1.5 [easy] Hovering over a target bar shows `Andromeda Galaxy from 21:00 to 02:00`; a bar cut off at the axis end still shows the window's own `Orion Nebula from 06:00 to 10:00`; a window of 24 hours or more, or with both ends at the same `HH:MM`, shows the name alone, such as `IC2184` (design DD1) (verify: mise exec -- npm --prefix card test -- targets) (✓ npm test -- targets passed)

## 2. The lines and the size [depends-on: 1]

- [ ] 2.1 [easy] With three target lanes, the strip's `grid-template-rows` is `repeat(21, auto)` and the lines' overlay has `grid-row: 2 / 21`, so dusk, dawn and now reach the bottom of the lane labelled `Target 3`; with none the numbers stay 18 and `2 / 18` (design DD3) (verify: mise exec -- npm --prefix card test -- targets strip)
- [ ] 2.2 [easy] `getCardSize()` returns 10 with no target lane, 12 with four and 14 with ten, and 10 before `setConfig`, before `hass`, and while the Verdict sensor is missing or unavailable (design DD4) (verify: mise exec -- npm --prefix card test -- targets register)

## 3. Docs and the whole path [depends-on: 2]

- [ ] 3.1 [easy] `docs/night-card.md` describes the target lanes: the sensors `sensor.pierpressure_<pier>_target_1` to `sensor.pierpressure_<pier>_target_10`, the label `Target 1`, the bar over the observable window with the target's name, the hover text, that a rank with no target tonight leaves no lane, and that the lines cross the lanes; its opening paragraph names the ranked targets (test: `tests/test_night_card_doc.py`) (verify: uv run pytest tests/test_night_card_doc.py -k targets)
- [ ] 3.2 [complex] The whole path works: `mise run check` is green, and `mise run dashboard-check` shows the target lanes beside the YAML strip's in a real Home Assistant, with the name on each bar and the window on hover, checked by eye (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->

- 2026-11-07: in task 1.1, the test that a rank with no lane leaves no gap passed on its first run, because with no lanes both sides of its check were empty. It stays as a guard, and checks real lanes from then on.
- 2026-11-07: in task 1.2, the tests for a window with no end, a start that is not a time, no window and no Target sensors passed on their first run, because task 1.1 already needed both times. They stay as guards.
- 2026-11-07: in task 1.4, the test that a Moon up bar carries no mark and no text passed on its first run, since no bar carried either yet. It stays as a guard. `cardStyles` moved from `strip.test.ts` into the harness, in its own `refactor:` commit, so both test files read the stylesheet one way.
- 2026-11-07: in task 1.5, the three name-alone hover tests passed on their first run, because the bar's text was still the bare name. The `from … to …` text went in first, which turned them red, and the 24-hour and same-time rule then turned them green.
