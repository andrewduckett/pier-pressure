## Story

#221 firms-nearby-fire — the reasons name an active fire near the pier, with an
optional FIRMS key. https://github.com/andrewduckett/pier-pressure/issues/221

The user decided ahead of time that every question with a recommendation takes
the recommended answer, and asked to be stopped only for a question with none.
Each `User` row below is a recommendation the user approved in that way. The
issue's thread had no comments at the first or the last fetch.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is a FIRMS hotspot in the project's language? | A **fire detection**: a measurement of the ground, not an observation of the sky. It is a separate input beside the observation, in the same way ADR-0037 puts the observation beside the conditions. Added to `openspec/glossary.md` | User |
| D2 | Where does the MAP_KEY live: on each pier, or once for the whole service? | Once, in a new top-level `firms` block as `firms.map_key`. A key belongs to an account, not a site. Every pier gets the fire line when the key is set | User |
| D3 | How is the key kept secret? | A `SecretStr` with `hide_input_in_errors`, like `explainer.api_key`. It supports `${VAR}`. No log line, health error or config error ever shows the key or the request URL that contains it | User |
| D4 | How does an add-on user set the key? | In `config.yaml`, like `explainer`. The Configuration tab gets no field. `ha-addon/DOCS.md` and the README say where it goes | Evidence: `ha-addon/DOCS.md` (explainer and `metar_station` go in the file) |
| D5 | Which FIRMS source, and how many requests? | One area request per pier on each fetch: `VIIRS_NOAA20_NRT`, a day range of 2 (today and yesterday in UTC), for a box that covers the radius. That is far inside 5,000 transactions per 10 minutes. A day range of 1 is today's UTC date only, so after 00:00 UTC it would drop the afternoon pass (plan review, round 1) | User |
| D6 | How far from the pier does a fire count? | 50 km, fixed, as a great-circle distance from the pier. It is just over the 45 km CAMS grid that the story says can miss a nearby fire. It is not a setting | User |
| D7 | Which detections count? | Nominal and high confidence only. VIIRS's low confidence detections are often sun glint or hot surfaces. Only detections from the 24 hours up to the evaluation instant count, so the verdict stays a pure function of its inputs | User |
| D8 | What does the reason line say? | The nearest detection's distance in whole kilometres, its bearing from the pier on an 8-point compass, when it was detected, and how many detections are within 50 km. One line, whatever the count | User |
| D9 | Where does the line go, and on which verdicts? | On every verdict, NO-GO included, after the observation lines and before the equipment notes, like the METAR line | Evidence: `pierpressure/core/producer.py` (metar-reason DD6 ordering) |
| D10 | Does the verdict document get a new key for the fire? | No. The story asks for a reason line only, and no reader needs the structured value yet. A later change can add one key as an addition | User |
| D11 | What does health show? | A `FIRMS` health sensor for each pier, only when the key is set, like METAR's. A fetch that works but finds no detection is a success. A rejected key, such as a 400 "Invalid MAP_KEY.", or a response with no CSV header is a failure | User |
| D12 | What fixture can the build use without a MAP_KEY? | A trimmed recording of FIRMS's public, no-key NOAA-20 VIIRS 24-hour file. It has the same VIIRS NRT columns as the area API. Also a header-only file for "no detections", and the 400 "Invalid MAP_KEY." reply recorded with a made-up key. The parser reads columns by header name, so an extra column in the API's reply breaks nothing | Assumption |

## Changes from the story

- **Added:** the term "fire detection" in `openspec/glossary.md` (D1). This
  change's pull request carries it.
- **Changed:** the outcome said "when the pier has a FIRMS key". The key is now
  one setting for the whole service (D2), so every pier gets the line when it is
  set.
- **Cut:** a key in the verdict document (D10). The story only asked for the
  reason line.

Confirmed by user: yes
