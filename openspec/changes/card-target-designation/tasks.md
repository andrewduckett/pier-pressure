## 1. Target bars show the catalog id

- [x] 1.1 [easy] A named target's bar text is `<name> (<id>)`, read from the Target sensor's `name` and `id` attributes, such as `Andromeda Galaxy (M31)` (verify: npm --prefix card test -- targets) (✓ npm --prefix card test -- targets passed)
- [x] 1.2 [easy] A target whose `name` attribute is null or empty has the bar text `<id>` alone, such as `IC2184` (verify: npm --prefix card test -- targets) (✓ npm --prefix card test -- targets passed)
- [x] 1.3 [easy] A Target sensor whose attributes hold no `id` keeps its state as the bar text, as an older PierPressure publishes (verify: npm --prefix card test -- targets) (✓ npm --prefix card test -- targets passed)
- [x] 1.4 [easy] Hovering over a target bar, and its accessible name, give the bar's text with the window, such as `Andromeda Galaxy (M31) from 21:00 to 02:00`, and the text alone for a window of 24 hours or more or with both ends at the same time (verify: npm --prefix card test -- targets) (✓ npm --prefix card test -- targets passed)
- [ ] 1.5 [medium] A target bar draws the name and `(<id>)` as two parts: only the name shortens and ends in `…` when the bar is narrow, the id never shrinks, and the bar keeps its 4px indent without padding (verify: npm --prefix card test -- targets)
- [ ] 1.6 [easy] `docs/night-card.md`'s target lanes section says the bar holds the name and catalog id, that a short bar shortens the name and keeps the id, and gives the hover as `Andromeda Galaxy (M31) from 21:00 to 02:00` (verify: uv run pytest tests/test_night_card_doc.py)
- [ ] 1.7 [easy] The whole gate passes with the change in place (verify: mise run check)
