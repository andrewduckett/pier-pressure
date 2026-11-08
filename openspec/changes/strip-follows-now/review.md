# Plan review: strip-follows-now

## Round 1

- **Reviewed commit:** e800195
- **Reviewer:** gemini/gemini-3.8-flash, through the t3 resolver
- **Reviewer context:** fresh context, other family
- **Verdict:** REVISE

### Findings

| # | Label | Concern | Check |
|---|---|---|---|
| 1 | Critical | A verdict left over after dawn lets the opening axis follow now into the day. | REFUTED as Critical. A stopped process fires its last-will message, which makes the Verdict sensor unavailable (`openspec/specs/ha-delivery/spec.md:88-94`). The card then draws no strip (`openspec/specs/night-card/spec.md:199-204`). An online process that publishes nothing new is the only way left. In that case, a strip about now beats one about a past night. |
| 2 | Critical | When the opening axis catches up with a later pan, `Back to tonight` hides for a minute and then comes back, and the strip stays a minute behind. | CONFIRMED |
| 3 | Critical | The range, targets, rows and messages suites also mount the card on the real clock. Task 1.1 left them out. | CONFIRMED |
| 4 | Moderate | D11 changed the panning text, which the doc test `tests/test_night_card_doc.py:452-453` asserts. | CONFIRMED |
| 5 | Moderate | On a window close to 48 hours long, the sliding axis ends past the forecast, so its last hours are blank. | REFUTED. Blank hours past a sensor's forecast are already defined behavior ("A null hour is blank"; "A row with no cell says why"). The dusk-based opening axis of such a window already ends 53 hours after dusk, past a 48-hour forecast. D2 accepts this trade-off. |
| 6 | Suggestion | A 32-word requirement sentence, and two names for the browser's clock. | CONFIRMED |
| 7 | Suggestion | Task 1.7's verify command does not check the comment in `card/src/strip.ts`. | CONFIRMED |

### Rebuttals and fixes

1. Rebutted as above. The spec delta adds the scenario "A verdict left over after dawn" (08:00–23:55), and D7 now names the case.
2. Fixed. "The strip stays where the user panned it" adds the rule and the scenario "The opening axis catches up with a pan". The ledger adds D12, and the task list adds task 1.7.
3. Fixed. Task 1.1 pins the clock in `mountCard` for every suite that mounts the card, and D10 says so.
4. Fixed. D11 keeps "opens on the judged night". Task 1.8 adds a doc test and verifies with pytest.
5. Rebutted as above.
6. Fixed. The requirement now uses two sentences, and "the browser's clock" throughout.
7. Fixed. The comment is its own task (1.9). The docs task (1.8) verifies with the doc tests.

## Round 2

- **Prior round:** round 1 gave REVISE at e800195. Two findings were refuted and five fixed.
- **Reviewed commit:** cb67049
- **Reviewer:** gemini/gemini-3.8-flash, through the t3 resolver
- **Reviewer context:** fresh context, other family
- **Verdict:** REVISE. The reviewer accepted both round 1 rebuttals. After two REVISE verdicts the user chose to apply these fixes and run a third round.

### Findings

| # | Label | Concern | Check |
|---|---|---|---|
| 1 | Critical | The plan does not say how the card tells a later pan from an earlier one, so a catch-up check could clear an earlier pan or miss a skipped minute. | CONFIRMED |
| 2 | Critical | The now-line test "is missing after the axis ends" (`card/test/strip.test.ts:885-891`) fails once an unpanned strip with a dark window always holds now. | CONFIRMED |
| 3 | Moderate | A clock pinned in `mountCard` leaks fake timers into suites that never restore real timers. | CONFIRMED |
| 4 | Moderate | Tasks 1.4 and 1.9 check comments with commands that ignore comments. | CONFIRMED |
| 5 | Suggestion | A 33-word bullet in "The page covers the strip". | Declined. The bullet is unchanged text from the main spec. This change only adds a bullet after it. |

### Fixes

1. "The strip stays where the user panned it" defines a later pan, and keeps an earlier pan's start. The catch-up fires when the opening axis reaches or passes the start of a later pan. D12 says the card remembers that a pan was later. Task 1.8 tests a skipped minute.
2. Task 1.2 names the now-line test, which moves to a panned or fallback axis.
3. Task 1.1 has the harness restore real timers after each test.
4. The comment changes are tasks 1.5 and 1.10, each verified by a negative `grep`.
