## 1. The reasons list

Card tests go in a new `card/test/reasons.test.ts`; leave `card/test/harness.ts` as it is (brainstorm D12).

- [x] 1.1 [easy] A Verdict sensor whose `reasons` is a list of strings shows a list named `Reasons`, one item per reason, in order, under the summary and before the strip (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [x] 1.2 [easy] A `reasons` attribute that is missing, null, empty, not a list, or holds a non-string item shows no list, and the card still shows the verdict and the strip (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [x] 1.3 [easy] No `Reasons` list shows before the first verdict, when PierPressure is offline or when the Verdict sensor is missing (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [x] 1.4 [easy] On a night with no astronomical darkness, the list comes before the note `No astronomical darkness tonight`, and the `Back to tonight` place stays directly above the strip (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [x] 1.5 [medium] Each `YYYY-MM-DDTHH:MM:SSZ` time in a reason shows as `HH:MM` in Home Assistant's time zone, using the strip's clock; a time that `Date.parse` cannot read stays as written and never reaches the clock, which throws a `RangeError` on an invalid time (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [x] 1.6 [easy] Ten reasons all show in full, with no button or `details` element in the list, and the list is styled in the secondary text colour (verify: npm --prefix card test -- reasons) (✓ npm --prefix card test -- reasons passed)
- [ ] 1.7 [easy] `getCardSize()` adds 1 for every two reasons shown, rounding up, on top of the target-lane size, and counts no reason when the card shows no verdict, such as when PierPressure is offline (verify: npm --prefix card test -- reasons targets)
- [ ] 1.8 [easy] `docs/night-card.md`'s "What the card shows" table has a **Reasons** line that names `NO-GO`, gate, time zone and equipment, checked by a new test in `tests/test_night_card_doc.py` (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.9 [easy] The whole gate passes (verify: mise run check)
