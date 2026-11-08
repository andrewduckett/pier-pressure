## 1. The Open-Meteo hour window

- [x] 1.1 [easy] Every Open-Meteo request asks for `past_hours` 4 and `forecast_hours` 72, names no `forecast_days`, and keeps `timezone` UTC. This holds for `open_meteo`, the five model providers and `open_meteo_air_quality`, with the fetch clock at 00:05 or 18:05 UTC. A new test in `tests/test_conditions_provider.py` builds each provider through `build_provider` and covers both clock times. The four existing `params["forecast_days"] == "2"` asserts in that file become asserts on the two hour parameters and on `"forecast_days" not in params` (brainstorm D2, D3, D8). (verify: `uv run pytest tests/test_conditions_provider.py`) (✓ `uv run pytest tests/test_conditions_provider.py` passed, 151 tests)
- [x] 1.2 [easy] The "Panning the strip" section of `docs/night-card.md` says Open-Meteo forecasts about three days ahead, not two. A test in `tests/test_night_card_doc.py` pins "about three days" in that section (brainstorm D10). (verify: `uv run pytest tests/test_night_card_doc.py -k pan`) (✓ `uv run pytest tests/test_night_card_doc.py -k pan` passed)
- [ ] 1.3 [easy] The README's "Adding the air-quality forecast" section says the forecast gives two values for each hour from 4 hours before now to 72 hours ahead, not "the next 2 days". A fact added to `test_the_air_quality_section_explains_its_variables` in `tests/test_docs.py` pins it (brainstorm D10). (verify: `uv run pytest tests/test_docs.py -k air_quality`)
- [ ] 1.4 [easy] In the README's "Choosing Open-Meteo models" section, the model limits say PierPressure asks every model for the 4 hours before now and the 72 after, not 2 days. The model table says `open_meteo_icon` and `open_meteo_gfs` reach more than 3 days. A test in `tests/test_docs.py` pins both (brainstorm D10). (verify: `uv run pytest tests/test_docs.py -k model`)
- [ ] 1.5 [easy] The full gate is green. (verify: `mise run check`)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
