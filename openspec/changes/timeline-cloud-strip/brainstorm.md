## Story

#133 timeline-cloud-strip — the verdict document carries an hourly timeline, and a Cloud cover sensor charts it in Home Assistant
https://github.com/andrewduckett/pier-pressure/issues/133

Parent: #130 Epic: see the night as a timeline in Home Assistant. Its Shared decisions apply.

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What shape does one timeline entry have? | Flat: `time`, `sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `seeing`, `transparency`. Names match `BaseHour` and `SecondaryHour`. Altitudes round to 3 dp like other angles; seeing and transparency round to 2 dp like `moon.illumination`. Later variables append as new flat keys. | User |
| D2 | How does the Cloud cover sensor treat hours a source lacks, and a current hour with no value? | The `forecast` array has one entry per timeline hour, `value` null where the base source lacked the hour, so later sensors' arrays align hour for hour. The state is the cloud cover for the hour containing `generated_at`. When that hour is missing or null the sensor is unavailable, like Score on a gated NO-GO. | User |
| D3 | After the verdict attributes drop the timeline, no MQTT topic carries the whole timeline. Accept? | Yes for this story. The document with its timeline stays the core's contract, pinned by the golden tests; MQTT delivers it per variable, which #134 completes. The ADR records the consequence. No new topic. | User |
| D4 | Which hours does the timeline hold, in what order? | The union of the hours both sources returned, including past hours, sorted ascending by hour. `time` is the aware-UTC top of hour, emitted like every other document timestamp. | Evidence: #130 Shared decisions; `pierpressure/core/conditions.py` keys hours by top of hour |
| D5 | Is the timeline filled when there is no dark window? | Yes. The service fetches conditions on every recompute, dark window or not, so the timeline carries whatever the providers returned. The verdict's "no dark window" rule is untouched. | Evidence: `pierpressure/service.py` `_publish` |
| D6 | What does the sensor look like? | Name `Cloud cover`, object id `cloud_cover`, on the pier's device, unit `%`, enabled by default, two-entry availability like the rank sensors. Attributes are `available`, `hour` and `forecast`; `forecast` datetimes use the document's timestamp format. "Current hour" is `generated_at` floored to the hour. The state is as fresh as the last recompute, so it can lag by one `recompute.interval_seconds` (any positive value, `pierpressure/core/config.py`); `hour` says which hour it belongs to, and the docs page says so. | Assumption; Evidence: `pierpressure/core/config.py` for the interval |
| D7 | What documentation changes? | A short `docs/` page with one apexcharts-card example reading the `forecast` array. The README's entity table gains the Cloud cover row, and the verdict document section says the Verdict attributes exclude the timeline, since "the full verdict document is in its attributes" stops being true. | Assumption |
| D8 | What does the ADR record? | The timeline's flat shape, that it is evidence beside the verdict and never a verdict on later nights (ADR 0023 stands), that it is additive, that the verdict entity's attributes exclude it, and D3's consequence. | Evidence: #133 Scope; User (D3) |
| D9 | Do the golden fixtures change? | Yes, additively: every expected document gains a `timeline` key. They are regenerated once, in a reviewed commit. | Evidence: `tests/test_golden_verdict.py` |
| D10 | Which specs change? | `night-verdict` gains the timeline requirement. `ha-delivery` gains the Cloud cover sensor and the rule that the verdict attributes exclude the timeline. `conditions` is context only. | Evidence: #133 Scope |

## Changes from the story

None. The story stands as written: about eight to ten tasks. The glossary commit from #130's handoff is already on this branch as `ca513bd`.

Confirmed by user: yes
