## 1. Hide the Cloud range row with one cloud forecast

- [ ] 1.1 [medium] With both Cloud range sensors in Home Assistant and available, and no readable pair in their whole forecasts, the strip leaves the Cloud range row out: before the first verdict too, while a `Not found` or `Unavailable` sensor still keeps the row with its message (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.2 [easy] A paired hour whose min is above its max is not a readable pair, so forecasts holding only such hours leave the row out (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.3 [medium] A Cloud range row with a readable pair, but none on the axis, says `No forecast`, marked `no-forecast`, with the hover text `No hour on the strip has cloud cover from two or more forecasts`; `Needs two forecasts` is gone from the card (verify: npm --prefix card test -- test/range.test.ts)
- [ ] 1.4 [easy] Panning past the end of the shorter Cloud range forecast keeps the row, under Cloud cover, with `No forecast` (verify: npm --prefix card test -- test/pan.test.ts)
- [ ] 1.5 [easy] With the row left out, the strip draws fifteen rows in order, and its grid and the lines overlay still end at the last target lane (verify: npm --prefix card test -- test/strip.test.ts)
- [ ] 1.6 [medium] The strip section of `docs/night-card.md` says the strip leaves the Cloud range row out with one cloud forecast, keeps it for `Not found` or `Unavailable`, and gives the hover text of its `No forecast`; the page no longer names `Needs two forecasts` (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.7 [easy] The "If something looks wrong" section of `docs/night-card.md` has an item for a strip with no Cloud range row, naming `conditions`, `providers`, Open-Meteo, the add-on and the health sensor, and its first-verdict note says the Cloud range row is left out (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.8 [easy] The project's checks pass (verify: mise run check)
