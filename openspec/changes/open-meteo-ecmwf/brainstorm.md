**Why:** PierPressure's cloud agreement only helps when the forecasts differ, and ECMWF, the best free global model, is not yet one of its Open-Meteo models; adding it is one catalog entry on code that exists.

## Story

#217 open-meteo-ecmwf — a pier can add ECMWF through Open-Meteo to its provider list, https://github.com/andrewduckett/pier-pressure/issues/217

The issue has no comments.

The user said beforehand to accept every recommended answer, and to be asked only about a question with no recommendation. Rows marked `User` are those recommendations, accepted under that instruction. No question was left without a recommendation.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which Open-Meteo model id: `ecmwf_ifs` (9 km) or `ecmwf_ifs025` (0.25°)? | `ecmwf_ifs`. Its data is hourly and finer. `ecmwf_ifs025` is 3-hourly, interpolated to hours. | Evidence: live `meta.json` for both, 2026-11-14 (`temporal_resolution_seconds` 3600 against 10800) |
| D2 | What key and display name? | Key `open_meteo_ecmwf`, display name `Open-Meteo ECMWF`, like the other model providers. Both stay fixed once released (ADR-0028). | Evidence: #217 Scope; ADR-0028 |
| D3 | Which variables does it declare? | Every variable `open_meteo` declares except the 36 seeing-column variables. That includes `precipitation_probability` and `column_water_vapour`. Its only bundle is the cloud bundle. | Evidence: live `ecmwf_ifs` forecast at Toronto, London, Sydney, Reykjavík and Tokyo, 2026-11-14: these 12 variables had a value at all 76 hours; 35 of the 36 seeing-column variables were null at every hour |
| D4 | Why leave out the whole seeing column when one of its variables (boundary-layer height) arrives? | The seeing column is one bundle: a provider declares all of it or none of it. | Evidence: conditions spec, "The seeing column is one bundle" and "A provider that does not declare the seeing column declares none of its variables" |
| D5 | Which metadata file gives its run time? | `ecmwf_ifs`. It carries `last_run_initialisation_time` and updates every 6 hours. | Evidence: live `https://api.open-meteo.com/data/ecmwf_ifs/static/meta.json`, 2026-11-14 |
| D6 | Does it join the default provider list? | No. A pier adds it by listing its key. The default list stays as it is. | Evidence: #217 outcome line ("a pier can add") |
| D7 | What fixture does it get? | A trimmed 4-hour live recording at Toronto (43.65, −79.38), `tests/fixtures/open_meteo_ecmwf.json`. It holds the 12 columns the provider asks for, and is recorded during apply. | Evidence: `tests/test_conditions_provider.py` recordings of the other five models |
| D8 | Which spec requirements change? | In `conditions`: the catalog gains a sixth model, and the model, metadata and hours tables gain a row. A new requirement says ECMWF declares column water vapour and precipitation probability but not the seeing column. | User |
| D9 | Which docs change? | README: the model table row (the whole world, more than 3 days), the water-vapour and seeing-column source lists, and the health-sensor key and topic lists. `docs/night-card.md`: the Cloud range tip names `open_meteo_ecmwf` as its example second cloud provider. | User |
| D10 | Does `docs/night-timeline.md` change? | No. It names no model and lists no provider keys, so there is nothing to add. | Evidence: `docs/night-timeline.md` |
| D11 | Does it need a new decision record? | No. ADR-0028 already covers adding a named model as its own provider. | Evidence: ADR-0028 |
| D12 | Do the add-on or the card need changes? | No. Neither lists provider keys. The health sensor follows from the catalog entry. | Evidence: search of `card/`, the add-on and `pierpressure/` for the existing model keys |

## Changes from the story

- The packet's "the README and timeline doc list it": the timeline doc (`docs/night-timeline.md`) lists no models, so it does not change (D10). The night-card doc's Cloud range tip names ECMWF instead (D9).
- None split out. The ensemble and AIFS stay out, as the packet says.

Confirmed by user: yes
