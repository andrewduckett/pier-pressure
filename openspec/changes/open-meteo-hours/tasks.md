## 1. The Open-Meteo hour window

- [ ] 1.1 [easy] Every Open-Meteo request, from `open_meteo`, each of the five model providers and `open_meteo_air_quality`, asks for `past_hours` 4 and `forecast_hours` 72, names no `forecast_days`, and keeps `timezone` UTC, whether the fetch clock reads 00:05 or 18:05 UTC. A new test in `tests/test_conditions_provider.py` builds each provider through `build_provider` and covers both clock times. The four existing `params["forecast_days"] == "2"` asserts in that file become asserts on the two hour parameters (brainstorm D2, D3, D8). (verify: `uv run pytest tests/test_conditions_provider.py`)
- [ ] 1.2 [easy] The "Panning the strip" section of `docs/night-card.md` says Open-Meteo forecasts about three days ahead, not two. A test in `tests/test_night_card_doc.py` pins "about three days" in that section (brainstorm D10). (verify: `uv run pytest tests/test_night_card_doc.py -k pan`)
- [ ] 1.3 [easy] The README's "Adding the air-quality forecast" section says the forecast gives two values for each hour from 4 hours before now to 72 hours ahead, not "the next 2 days". A fact added to `test_the_air_quality_section_explains_its_variables` in `tests/test_docs.py` pins it (brainstorm D10). (verify: `uv run pytest tests/test_docs.py -k air_quality`)
- [ ] 1.4 [easy] The full gate is green. (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
