## Story

#154 open-meteo-models — a pier names which Open-Meteo models it uses, each one a provider in the list
https://github.com/andrewduckett/pier-pressure/issues/154

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which Open-Meteo identifiers exist and work today? | `ncep_hrrr_conus`, `gem_hrdps_continental`, `gem_regional`, `icon_seamless` and `gfs_global` all return the cloud split, gusts, temperature, dew point, humidity, wind speed and wind direction; HRDPS and RDPS return no precipitation probability (D4). `gfs_hrrr` and `ncep_gfs_global` are aliases that return identical data | Evidence: live API, Toronto point, 2026-11-02 UTC |
| D2 | What keys and display names do the five model providers get? | `open_meteo_hrrr`, `open_meteo_hrdps`, `open_meteo_rdps`, `open_meteo_icon`, `open_meteo_gfs`, named "Open-Meteo HRRR", "Open-Meteo HRDPS", "Open-Meteo RDPS", "Open-Meteo ICON", "Open-Meteo GFS" | User |
| D3 | Which identifier backs ICON and GFS? | `icon_seamless`, the finest ICON for the pier's location; `gfs_global`, because `gfs_seamless` blends HRRR in and repeats the HRRR entry (identical cloud in North America) | User |
| D4 | Does every model provider declare the same variables? | No. Each declares what its model returns: HRDPS and RDPS leave out `precipitation_probability`, which they never send; HRRR, ICON and GFS declare the same eleven as `open_meteo` | User |
| D5 | What happens for a pier outside HRRR's or HRDPS's area? | Open-Meteo answers HTTP 400; it is reported as a failed fetch like any HTTP error and the provider is passed over. The README lists each model's coverage. No startup check | User |
| D6 | Does the forecast length change? | No. Every entry asks for 2 days, as `open_meteo` does today. HRRR reaches about 48 h, HRDPS about 42–48 h, RDPS 84 h, ICON and GFS longer, so hours past a model's reach stay empty under the existing rule | Evidence: live API; `pierpressure/conditions/open_meteo.py` |
| D7 | Does plain `open_meteo` change? | No. It keeps best match and sends the same request as today; the default list stays `open_meteo`, `seven_timer` | Evidence: #154 Scope |
| D8 | What issue time does a model provider carry? | The fetch time, as `open_meteo` does today; the forecast response reports no issue time | Evidence: `pierpressure/conditions/open_meteo.py`, README "Watching provider health" |
| D9 | How is each model's parsing tested? | A trimmed recording of a live response per model, beside the existing `open_meteo.json` fixture | Evidence: #154 Scope |
| D10 | Does the story need new glossary terms? | No. Each model provider is a Provider as the glossary defines it | Evidence: `openspec/glossary.md` |
| D11 | Does the story need splitting? | No. Five catalog entries, one parameterised fetcher, config, fixtures and README fit in one change | Assumption |
| D12 | Do HRRR and HRDPS really answer 400 outside their areas? | Yes. HRRR: 400 at London, 200 at Arizona. HRDPS: 400 at London and at Arizona. RDPS: 200 at both | Evidence: live API, 2026-11-02 UTC, added after plan review |
| D13 | Should a model provider read its run time from Open-Meteo's metadata endpoint instead of the fetch time? | Not in this story. Keep D8, state the effect on confidence in the design and README, and file reading the run time as a follow-up | User, after plan review |

## Changes from the story

None. Two details the packet left open are now fixed: GFS uses `gfs_global` and ICON uses `icon_seamless` (D3), and HRDPS and RDPS declare no precipitation probability (D4).

Confirmed by user: yes
