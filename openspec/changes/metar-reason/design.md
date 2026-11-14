## Context

- `CompositeProvider.get(pier)` in `pierpressure/conditions/provider.py`
  fetches every provider, fills the snapshot and returns a `FetchResult`: the
  `Conditions` and one `FetchOutcome` per provider. Each fetch is guarded by
  `_safe_fetch`, so a failure becomes a failed outcome.
- `Service._publish` in `pierpressure/service.py` passes only
  `result.conditions` to `produce_verdict(pier, clock, conditions)`, and folds
  `result.outcomes` into per-pier health. `_reset_health` seeds one
  `ProviderHealth` per pier for every configured provider.
- `MqttDelivery.publish_health` publishes discovery, state and attributes for
  any `ProviderHealth` it is given, keyed by `health.key` and named after
  `health.name`. It needs no change to publish one more record.
- `pierpressure/conditions/nws.py` holds the fixed `USER_AGENT` and the
  fetch-then-parse pattern with a recorded fixture.
- The aviationweather.gov Data API returns a JSON list. A report carries
  `icaoId`, `obsTime` (Unix seconds, when measured), `reportTime` (the nominal
  hour), `cover` (the overall code: `FEW`, `SCT`, `BKN`, `OVC`, `OVX`, `CLR`,
  `SKC`, `CAVOK` and so on) and `clouds`, a list of `{cover, base}`. An unknown
  station answers **204 with an empty body**, not an empty list.
- The verdict document's keys are emitted in declaration order, and every key
  is always present. `agreement` is the last key today.

## Goals / Non-Goals

**Goals:**

- One METAR request per pier with a station on every fetch, guarded like a
  provider fetch, with its own health outcome.
- The core takes the observation as a plain value and stays pure.
- One additive document key and one reason line, both a pure function of the
  observation and the evaluation instant.

**Non-Goals:**

- No change to the provider order, the fill, the catalog or config validation
  of `conditions.providers`.
- No batching of stations across piers. Each pier makes its own request.
- No caching of a previous observation. A failed fetch gives no observation.
- No change to gates, score, confidence, the card or the narrative.

## Test Seams

- **Primary test seam:** `produce_verdict` with a pinned clock, a snapshot and
  a pinned observation, in `tests/test_producer.py`. It proves the document key,
  the staleness rule, the reason wording, its position and that nothing else
  changes.
- **Existing seams reused:**
  - The recorded-fixture parser tests, as `nws.py` has them: a new
    `tests/fixtures/metar.json` recorded from the live API, and a new
    `tests/test_metar.py` for the parser and the fetcher with `httpx.MockTransport`.
  - `tests/test_conditions_provider.py` for `CompositeProvider.get` returning
    the observation and the `metar` outcome, and for a failed fetch.
  - `tests/test_service.py` for health seeding and folding of `metar`.
  - `tests/test_config.py` for `metar_station` validation.
  - `tests/test_golden_verdict.py`: every golden expected document gains
    `"observation": null`.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the conditions edge (a new fetcher), the core's inputs and
  verdict document (one additive key, one reason line), the service's health
  seeding, and pier configuration. It adds an external dependency, but one with
  the same shape and failure handling as NWS.

## Decisions

### DD1. The observation is a third input to `produce_verdict`, not part of `Conditions`

`produce_verdict(pier, clock, conditions, observation=None)`. The new value is
`pierpressure/core/observation.py`'s frozen dataclass `Observation(station,
observed_at, cover, clouds)`, with `clouds` a tuple of `CloudLayer(cover,
base_ft)`. `base_ft` is `int | None`.

- *Alternative:* a field on `Conditions`. Rejected: `Conditions` is "one series
  per variable", and the glossary says an observation is not a series. Putting
  it there would make every reader of the snapshot learn to skip it.
- *Alternative:* a required parameter. Rejected: a keyword with a `None`
  default leaves every existing caller and test unchanged.

### DD2. `FetchResult` carries the observation, and `CompositeProvider` fetches it

`FetchResult` gains `observation: Observation | None = None`.
`CompositeProvider` gains an optional `metar` fetcher. When the pier names a
station, `get` calls it after the providers, through a guarded
`_safe_observe` that mirrors `_safe_fetch`, and appends a `metar` outcome to
`outcomes`. The service passes `result.observation` to `produce_verdict`.
`build_provider` constructs the real `MetarFetcher` and passes it to
`CompositeProvider`. A `metar` keyword on `build_provider` replaces it, as
`fetchers` replaces a provider, so tests run the production stack offline.

- *Alternative:* the service calls a separate METAR fetcher. Rejected: the
  service would need a second fetch path, and the "one call per pier returns
  everything the core needs" seam would split.

### DD3. `pierpressure/conditions/metar.py` fetches and parses

- `parse_metar(payload: list[dict], station: str) -> Observation`: picks the
  report whose `icaoId` is `station`, takes `obsTime` as aware UTC, keeps
  `cover` and each layer in the order reported. A layer with a missing base
  keeps `base_ft=None`. A layer whose cover is `CLR`, `SKC`, `NCD` or `NSC` is
  dropped. No report for `station` raises `NoReport`.
- `MetarFetcher.fetch(station) -> Observation`: one `GET` to
  `https://aviationweather.gov/api/data/metar` with `ids` and `format=json`,
  the `USER_AGENT` from `nws.py`, and the same 10-second timeout.
- A 204, an empty body or an empty list raises `NoReport`, whose description
  is `no report returned`. Any other error goes through `describe_error`, as a
  provider's does.
- `METAR = ProviderInfo(key="metar", name="METAR", variables=())` lives here.
  It is not a `ProviderSpec` and not in `CATALOG`, so `metar` in
  `conditions.providers` stays an unknown key.

### DD4. The core decides usability and words the line

`pierpressure/core/observation.py` also holds `usable(observation, instant)`
(measured at most 90 minutes before the instant and not after it) and
`observation_reason(observation)`, which names the layers in their stored
order and never sorts them. The producer calls both. The cover wording
map and the two no-layer heights are module constants beside them.

### DD5. The document models mirror `TimelineEntry`

`model.py` gains `ObservationEntry(station, observed_at, cover, clouds)` and
`CloudLayerEntry(cover, base_ft)`, both `extra="forbid"`. `observed_at` uses the
existing aware-UTC validator and `iso_z` serializer. `VerdictDocument` gains
`observation: ObservationEntry | None = None` after `agreement`.

### DD6. The reason line is appended after the core's lines, before equipment notes

In `produce_verdict`, the line is appended to `decision.reasons` before the
equipment notes are extended. `evaluate` in `scoring.py` does not change, so
the dew line stays last among the scoring lines.

### DD7. `metar_station` is a `PierConfig` field with a pattern

`metar_station: str | None = None`, normalized to upper case before a pattern
check `^[A-Z][A-Z0-9]{3}$`. The add-on form gains no field; `config.yaml` merge
already passes unknown pier keys through to `PierConfig`.

### DD8. Health is seeded per pier, only for piers with a station

`Service._reset_health` adds a `metar` record for each pier whose
`metar_station` is set, when the service reports health at all. `_publish`
folds the `metar` outcome like any other. A `metar` outcome for a pier with no
record is logged and ignored, as an unconfigured provider's is.

## Risks / Trade-offs

- [aviationweather.gov changes its JSON shape] → The recorded fixture pins the
  shape; a parse failure is a failed fetch shown in health, never a failed
  verdict.
- [A station near the pier is not under the pier's sky] → The line names the
  station and its time, so the reader judges distance. Choosing the station is
  the user's call.
- [A fetch on every on-demand refresh adds requests] → One request per pier per
  recompute is far below the 100-a-minute limit; refreshes are already
  collapsed per pier.
- [The new key changes every golden document] → The change is mechanical:
  `"observation": null` at the end. The goldens are regenerated in one task and
  reviewed as a diff.

## Migration & Rollback

N/A. The new key and config field are additive; a pier without
`metar_station` behaves as before, apart from `"observation": null` in its
document. Rolling back removes the key and the `METAR health` sensor; a retained
`METAR health` discovery from before the rollback stays on the broker until
cleared by hand, like any removed provider's.
