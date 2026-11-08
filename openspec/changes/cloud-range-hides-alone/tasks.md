## 1. Hide the Cloud range row with one cloud forecast

- [ ] 1.1 [medium] A Cloud range row with no column says `No forecast`, marked `no-forecast`, with the hover text `No hour on the strip has cloud cover from two or more forecasts`. Update the range tests that expect `Needs two forecasts`, and drop that message from the card (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.2 [medium] When both Cloud range sensors are available and their whole forecasts have no paired hour, the strip leaves the row out. Update the range tests for null forecasts and the first verdict (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.3 [easy] A `Not found` or `Unavailable` Cloud range sensor keeps the row with its message, even with no paired hour (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.4 [easy] A paired hour counts whichever value is larger, so forecasts whose only paired hour has min above max keep the row, with `No forecast` (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.5 [easy] The range tests for an hour without a readable pair hold a paired hour elsewhere, so they check a drawn row (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.6 [easy] Panning past the end of the shorter Cloud range forecast keeps the row, under Cloud cover, with `No forecast` (verify: npm --prefix card test -- test/pan.test.ts)
- [ ] 1.7 [easy] With the row left out, the strip has fifteen rows in order, and its grid and lines overlay still end at the last target lane. The row-order tests give the Cloud range sensors a paired hour (verify: npm --prefix card test -- test/strip.test.ts test/rows.test.ts)
- [ ] 1.8 [medium] In `docs/night-card.md`, "If something looks wrong" has an item for a strip with no Cloud range row, and the first-verdict note says the row is left out. Update `tests/test_night_card_doc.py` to match (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.9 [medium] The strip section of `docs/night-card.md` says when the row is left out and gives the hover text of its `No forecast`. The page no longer names `Needs two forecasts`, and `tests/test_night_card_doc.py` checks that (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.10 [easy] The project's checks pass (verify: mise run check)
