## Story

#164 open-meteo-run-times — each Open-Meteo model provider reports its model's latest run as its issue time
(https://github.com/andrewduckett/pier-pressure/issues/164)

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which metadata time becomes the issue time? | `last_run_initialisation_time`, the run's start, as 7Timer!'s `init` already is. Not the availability or modification time. | Evidence: `pierpressure/conditions/seven_timer.py` |
| D2 | Which metadata name does HRRR read? | `ncep_hrrr_conus`. | Evidence: Open-Meteo `ForecastapiController.swift`, live `meta.json` |
| D3 | Which metadata name does HRDPS read? | `cmc_gem_hrdps`, the domain behind `gem_hrdps_continental`. | Evidence: Open-Meteo `ForecastapiController.swift`, live `meta.json` |
| D4 | Which metadata name does RDPS read? | `cmc_gem_rdps_10km`. `gem_regional` reads the old and new RDPS grids; the old one (`cmc_gem_rdps`) stopped at a 2026-05-26 run. | Evidence: Open-Meteo `ForecastapiController.swift`, live `meta.json` |
| D5 | Which run does `icon_seamless` carry? | ICON global's, from `dwd_icon` only: it covers every pier and is the oldest run in the blend. | User |
| D6 | Which metadata name does GFS read? | `ncep_gfs013`, the primary domain behind `gfs_global`, which carries surface cloud. | User |
| D7 | What issue time when the metadata call fails? | None (null), so freshness treats the cloud as maximally stale, as it already does for NWS with no update time. | User |
| D8 | How does a metadata failure show on health? | The fetch still succeeds; the outcome and health `issued_at` are null, and the error goes to the log only. No new field. | User |
| D9 | What if the metadata answers but gives no usable run time? | Treated as a failed metadata call: issue time null. | Assumption |
| D10 | What if the forecast itself fails? | Unchanged: the provider fails and is passed over; no metadata result is kept. | Evidence: `pierpressure/conditions/provider.py` (`_safe_fetch`) |
| D11 | Does plain `open_meteo` or the air-quality provider change? | No. Both keep the fetch time as their issue time. | Evidence: #164 Scope |
| D12 | Are new glossary terms needed? | No. "Issue time" keeps its meaning: when the provider issued the data. | Evidence: `openspec/glossary.md` |

## Changes from the story

- The packet left the RDPS metadata name, the ICON choice and the failure behaviour open. D4, D5 and D7 settle them.
- The packet named `ncep_gfs025` for GFS. D6 uses `ncep_gfs013` instead, because it is the primary domain behind `gfs_global`.

Confirmed by user: yes
