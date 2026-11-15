## Context

- `metar-reason` built the seam this change copies. `CompositeProvider.get`
  fetches the METAR after the providers, through `_safe_observe`, and returns
  it on `FetchResult.observation`. `produce_verdict` takes it as a keyword
  argument. `Service._reset_health` adds `METAR` health only for a pier that
  needs it. ADR-0037 says a measurement enters the core beside the conditions,
  never as a provider.
- Secrets have one established shape (#89): a `SecretStr` on a block model with
  `hide_input_in_errors`, validated through `_block_error`, which never quotes
  input. `ExplainerConfig.api_key` is the example. `explain/provider.py` treats
  a key that still holds `${` as unset.
- FIRMS takes its MAP_KEY only in the URL path. There is no header form.
- `main()` calls `logging.basicConfig(level=logging.INFO)`. httpx logs every
  request at INFO on the `httpx` logger as `HTTP Request: GET <url> ...`. So
  without a filter, every FIRMS fetch would write the key to the log. httpx's
  `HTTPStatusError` message quotes the URL too, and `_safe_fetch` and
  `_safe_observe` log `%s` of the exception.
- FIRMS's public no-key VIIRS NOAA-20 file, read on 2026-11-14, has the header
  `latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight`.
  A request with a made-up key answers `400` with `text/plain` body
  `Invalid MAP_KEY.`.

## Goals / Non-Goals

**Goals:**

- Fire detections reach the core as a plain tuple beside the observation, and
  the producer adds one line from them. `evaluate()` never sees them.
- The key cannot reach a log line by any path, including a log line from a
  library.
- The fetch, the parse and the counting can each be tested with no network and
  no real key.

**Non-Goals:**

- A shared "keyed provider" mechanism. `astrospheric-provider` (#147) has not
  landed. This change adds one block for one key and does not generalise it.
- An ellipsoidal distance. A sphere is well within the accuracy of a 375 m
  VIIRS pixel at 50 km.
- Caching FIRMS responses across fetches. One request per pier per fetch is far
  inside the limit.

## Test Seams

- **Primary test seam:** `build_provider(..., firms=<stub>)` and
  `produce_verdict(..., fires=...)`. These are the existing seams that
  `test_conditions_provider.py` and `test_producer.py` use for METAR.
- **Existing seams reused:** `httpx.MockTransport` for the fetcher, as
  `test_metar.py` does; the `Service` tests with a fake delivery for health;
  `test_config.py` for the block; `caplog` for the key never appearing in a log.

## Scrutiny Tier & Blast Radius

- **Tier:** high. The change adds a new external service and a secret that
  travels in a URL. That is a trust boundary.
- **Blast radius:** `core/config.py` (a new top-level block), a new
  `core/fire.py`, `core/producer.py` (one more reason line), a new
  `conditions/firms.py`, `conditions/provider.py`, `service.py`, `__main__.py`
  (wiring and the log filter), and the README and `ha-addon/DOCS.md`. The
  verdict document's keys, the gates, the score and confidence are untouched.

## Decisions

### DD1: A fire detection is a core value in `pierpressure/core/fire.py`

`FireDetection` is a frozen dataclass: `latitude`, `longitude`, `detected_at`
(aware UTC) and `confidence` (`str`, as given). The same module holds
`RADIUS_KM = 50`, `MAX_AGE = timedelta(hours=24)`,
`COUNTED_CONFIDENCE = {"nominal", "high"}`, a pure `counted(fires, pier,
instant)` and `fire_reason(...)`. Distance is haversine on a sphere of radius
6371.0088 km, the mean Earth radius. Bearing is the initial great-circle
bearing. Both use `math`, so the core stays free of new imports.

- **Alternative:** reuse `Observation` with a new kind. Rejected by D1 of the
  brainstorm and the glossary: an observation is of the sky.
- **Alternative:** a geodesy library such as `pyproj`. Rejected: a new compiled
  dependency for an error of under 0.5% at 50 km.

### DD2: `produce_verdict` takes `fires` as a keyword argument

`produce_verdict(pier, clock, conditions, observation=None, fires=())`. It runs
`counted` at the evaluation instant. When one or more count, it appends
`fire_reason` right after the observed-cloud line, before the equipment notes.
`evaluate()`, the model and the document schema do not change. Golden files do
not change, because no golden pier passes fires.

The nearest is chosen by `min` over `(distance, -timestamp, index)`, which gives
the tie rule in the spec. Distance is rounded with `math.floor(d + 0.5)`, not
`round()`, so .5 always rounds up, and then raised to at least 1. Bearing index
is `int((bearing + 22.5) // 45) % 8` over `N, NE, E, SE, S, SW, W, NW`. That
sends a boundary bearing clockwise.

### DD3: The fetcher lives in `pierpressure/conditions/firms.py`

It follows `metar.py`:

- `FIRMS = ProviderInfo(key="firms", name="FIRMS", variables=())`.
- `firms_box(latitude, longitude) -> str` builds the four bounds with `:.4f`.
  Within 0.5° of a pole it gives −180 and 180 for longitude.
- `parse_firms(text) -> tuple[FireDetection, ...]` uses `csv.DictReader`.
  `UnexpectedResponse` (description `unexpected response`, added to `health.py`
  beside `NO_REPORT`) is raised when the header lacks a needed column. A row
  whose values fail to parse is skipped.
- `FirmsFetcher(map_key: SecretStr, client: httpx.Client | None)` with
  `fetch(pier) -> tuple[FireDetection, ...]`. It calls `raise_for_status()` and
  parses `response.text`. It sends the same fixed User-Agent as NWS and METAR.

### DD4: `CompositeProvider` fetches fires after the METAR, and logs safely

`CompositeProvider` gains `firms: FireSource | None = None`, a `Protocol` with
`fetch(pier)`. `get()` calls `_safe_fires` for every pier when it is set, and
`FetchResult` gains `fires: tuple[FireDetection, ...] = ()`. `_safe_fires`
mirrors `_safe_observe`, with one difference: its warning logs only
`describe_error(exc)`, never the exception, because httpx error text quotes the
URL. The outcome's `issued_at` is the latest `detected_at`, or `None` when
there are none. `build_provider` gains `firms_key: SecretStr | None` and
`firms: FireSource | None`. A stub replaces the real fetcher, as `metar=`
does.

### DD5: A log filter masks the key in every record

When a key is set, `main()` adds a `logging.Filter` to each root handler. The
filter replaces the key's text with `**********` in the record's formatted
message and in any exception text, then clears `args`. It lives in a small new
`pierpressure/redact.py`, outside the core. A filter on the handlers catches
records that propagate from every logger, httpx's included. DD4 still logs
safely, so the filter is a second guard, not the only one.

- **Alternative:** raise the `httpx` logger to WARNING. Rejected: it removes
  the request log for every other provider, and it does not cover the
  exception path.
- **Alternative:** rely on DD4 alone. Rejected: httpx's own INFO line would
  still carry the key.

### DD6: `FirmsConfig` is a top-level block validated like `explainer`

`FirmsConfig(BaseModel)` uses `extra="forbid"` and `hide_input_in_errors=True`,
and holds `map_key: SecretStr | None = None`. `AppConfig.firms: FirmsConfig |
None = None`. `ConfigFile` rejects a `firms` value that is not a mapping, with
the wording the explainer uses. `load_app_config` validates the block through
`_block_error("firms", FirmsConfig, ...)`, and treats an empty block as absent.
`FirmsConfig.usable_key` returns the key, or `None` when it is empty or still
holds `${`. `main()` logs the one warning that names `firms.map_key` when a key
is given but not usable. The add-on needs no change: `combine_settings` passes
through every `AppConfig` field the file sets.

### DD7: `Service` adds FIRMS health from the config

`_reset_health` appends `FIRMS` to each pier's health sources when
`config.firms` has a usable key, in the same place it appends `METAR`, and
under the same rule that health is reported only when providers are. The order
is the providers, then METAR, then FIRMS. `_publish` passes `result.fires` to
`produce_verdict`.

### DD8: The fixture is a trimmed recording of the public no-key file

`tests/fixtures/firms_viirs_noaa20.csv` holds the public file's header and a
few rows near one test pier, recorded from
`https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_USA_contiguous_and_Hawaii_24h.csv`.
It mixes `low` and `nominal` confidence and at least one row beyond 50 km.
These three rows, read on 2026-11-14, serve if the file has changed when the
build records it:

```text
46.76213,-71.00217,321.85,0.45,0.63,2026-11-13,0554,N20,nominal,2.0NRT,262.35,2.06,N
46.7646,-70.99916,304.2,0.52,0.5,2026-11-13,0735,N20,nominal,2.0NRT,263.76,1.68,N
19.4086,-155.27255,342.6,0.34,0.56,2026-11-13,0015,N20,low,2.0NRT,315.08,7.2,D
```

The tests build the header-only body, the `instrument`-column variant and the
`Invalid MAP_KEY.` body inline. They need no file. No test uses a real key.

## Risks / Trade-offs

- [The area API's columns differ from the public file's] → The parser reads
  columns by name, and the spec has a scenario with an extra `instrument`
  column. The first live run with a real key confirms it; the health sensor
  shows `unexpected response` if a needed column is missing.
- [A future log line formats the key through a path the filter misses, such as
  a `print`] → The service logs only through `logging`. A test drives a failed
  fetch through `main`'s logging setup and checks `caplog` and stderr.
- [The box clamps at the antimeridian, so a fire just across 180° is missed] →
  Accepted. Few piers sit within 50 km of 180°.
- [FIRMS answers slowly] → A 10 s timeout, as METAR uses. It holds up only that
  pier's publish, and a timeout is a failed fetch with no line.

## Migration & Rollback

N/A. The block is optional and new. Without it, nothing changes. Rolling back
removes the line and the health sensor. Home Assistant keeps a retained FIRMS
health discovery until it is removed, as with any removed provider.
