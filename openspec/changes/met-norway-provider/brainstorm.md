**Why:** Every model provider except NWS reaches PierPressure through Open-Meteo's one API, so if Open-Meteo fails, a pier outside the United States has no cloud forecast left; MET Norway's Locationforecast is free, global, gives cloud in low, mid and high layers, and does not depend on Open-Meteo.

## Story

#220 met-norway-provider — a pier can add MET Norway's Locationforecast to its provider list, https://github.com/andrewduckett/pier-pressure/issues/220

The issue has no comments.

The user said beforehand to accept every recommended answer, and to be asked only about a question with no recommendation. Rows marked `User` are those recommendations, accepted under that instruction. No question was left without a recommendation.

Live recordings used as evidence below were made on 2026-11-14 at Toronto (43.65, −79.38), Oslo (59.9139, 10.7522) and Sydney (−33.8688, 151.2093), from `https://api.met.no/weatherapi/locationforecast/2.0/complete`.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What key and display name? | Key `met_norway`, display name `MET Norway`. It needs no key, and is not in the default provider order. A pier adds it by listing it. | Evidence: #220 outcome line ("a pier can add"); the NWS requirement sets the same pattern |
| D2 | Which variables does it declare? | `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and `precipitation_probability`. Its one bundle is the cloud bundle. No column water vapour, no seeing column, no seeing or transparency. | Evidence: live recordings; `pierpressure/core/providers.py` |
| D3 | Which field fills each variable? | From each step's `instant.details`: `cloud_area_fraction`, `cloud_area_fraction_low`, `cloud_area_fraction_medium` (mid), `cloud_area_fraction_high`, `wind_speed_of_gust`, `wind_speed`, `wind_from_direction`, `air_temperature`, `dew_point_temperature`, `relative_humidity`. Rain chance from `next_1_hours.details.probability_of_precipitation`. | Evidence: live recordings |
| D4 | Gust and rain chance arrive only for Nordic piers. Declare them anyway? | Yes. Outside the Nordic area they are blank in every hour, so the fill passes MET Norway over for them and the next provider that returned them fills them. The fetch still succeeds. | Evidence: Oslo had both; Toronto and Sydney had neither; `_returned` in `pierpressure/conditions/provider.py` |
| D5 | How are units checked? | Against the units in `properties.meta.units`, like NWS: `%` for the cloud fields, humidity and rain chance; `celsius` for temperature and dew point; `degrees` for direction; `m/s` for wind speed and gust. A variable whose unit is anything else is left blank in every hour. | Evidence: live `meta.units`; NWS design DD4 |
| D6 | MET Norway gives wind only in m/s. Convert it, or leave wind blank? | Convert: multiply m/s by 3.6 to give km/h, unrounded. Gust feeds the `max_gust` gate, so a blank gust would make the provider much less useful. The general rule "carried as reported, with no conversion" is changed to allow this one named conversion. | User |
| D7 | Which steps are kept? | Only the leading run of steps one hour apart. From the first step that is not one hour after the one before, every later step is dropped. Then only hours within 72 hours of the first step are kept, so listing it never lengthens the timeline. | Evidence: live recordings (55–62 hourly steps, then 6-hourly); #220 Scope; NWS's 72-hour rule |
| D8 | Which hour does a rain chance belong to? | `next_1_hours` at time T is the chance for the hour from T to T+1. PierPressure's rain chance at an hour is for the hour that ends there, so it is held at T+1, as NWS's is. A held hour past the 72-hour limit is dropped. | Evidence: MET Norway FAQ ("between 12:00 and 13:00"); conditions spec, NWS rain-chance requirement |
| D9 | What is its issue time? | `properties.meta.updated_at`, in UTC. When it is missing, the issue time is null. | Evidence: live recordings |
| D10 | How are coordinates sent? | Latitude and longitude rounded to 4 decimal places. MET Norway answers 403 for 5 or more. No altitude is sent, like the Open-Meteo providers. | Evidence: MET Norway terms of service |
| D11 | Which User-Agent? | The same fixed User-Agent that NWS and METAR send: project name, version and repository URL. The terms ask for a website or email; the repository URL is the website. | Evidence: MET Norway terms of service; `pierpressure/conditions/nws.py` |
| D12 | How does it keep within the terms on `Expires` and `If-Modified-Since`? | It remembers, per rounded coordinates and for as long as the process runs, its last good forecast with that response's `Expires` and `Last-Modified`. Before `Expires`, a fetch makes no request and returns the remembered forecast. After it, the request carries `If-Modified-Since` with the remembered `Last-Modified`; a 304 returns the remembered forecast and takes the new `Expires`. Any failed request forgets what was remembered. Times are compared with the provider's injected clock. Nothing is written to disk. | Evidence: MET Norway terms of service ("Never repeat requests until the time indicated in the Expires response header") |
| D13 | D12 answers a fetch from an earlier response. What happens to the rule against that? | The requirement "No single provider is load-bearing" is changed: a failed or empty fetch is still never filled from an earlier fetch, but a provider may answer from a response its source still calls current. Such a fetch is a successful outcome with the remembered issue time. | User |
| D14 | How are other statuses handled? | 403, 429 and any other error status fail the fetch like any provider, and the next provider fills. A 203 (deprecated product version) is a success, and the provider logs a warning. | Evidence: MET Norway terms of service; conditions spec, "No single provider is load-bearing" |
| D15 | What fixture does it get? | A trimmed live recording at Oslo, `tests/fixtures/met_norway.json`, so gust and rain chance are present. It is recorded during apply. Synthetic payloads cover the 6-hourly cut, the Nordic-only blanks and the units. | Evidence: `tests/fixtures/` recordings for NWS and the Open-Meteo models |
| D16 | Which spec requirements change? | In `conditions` only. New requirements for the catalog entry, the request, the units and conversion, the kept steps, the rain-chance hour, the issue time and the caching. Changed: "Weather variables are carried as reported and never judged" (D6) and "No single provider is load-bearing" (D13). | User |
| D17 | Which docs change? | README: a section on adding MET Norway, like NWS's; the list of provider keys; the health-sensor key and topic lists; and the `metar_station` line, which names the providers that give low and mid cloud. `docs/night-timeline.md`: the rain-chance row says MET Norway gives it only near the Nordic countries and does not publish its threshold. | Evidence: `README.md`; `docs/night-timeline.md` |
| D18 | Do the core, the add-on or the card change? | No. The core reads no provider key, the add-on and card list none, and the health sensor follows from the catalog entry. | Evidence: search of `pierpressure/core/`, the add-on and `card/` for provider keys |
| D19 | Does it need a new decision record? | No. ADR-0027 covers adding a provider to the ordered list. | Evidence: ADR-0027 |

## Changes from the story

- Added: wind speed and gust are converted from m/s to km/h (D6), which changes the "carried as reported" rule. The packet assumed they could be carried as they are.
- Added: the "No single provider is load-bearing" rule changes so a remembered response can answer a fetch (D12, D13). The packet allowed "keep within its rate terms" instead, but the terms forbid any request before `Expires`.
- Added: the 72-hour limit on kept hours (D7).
- Clarified: gust and rain chance are only present for Nordic piers (D4).
- Left out: sending the pier's altitude (D10). Fog fraction and the Nowcast product stay out, as the packet says.
- None split out.

Confirmed by user: yes
