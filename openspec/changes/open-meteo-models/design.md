## Context

- `pierpressure/core/providers.py` holds each provider's `ProviderSpec` as plain
  data in `CATALOG`. Configuration validates the provider list against
  `CATALOG` alone (ADR-0022, ADR-0027), so a new catalog entry is accepted by
  `_check_providers` with no code change there.
- `OpenMeteoProvider` in `pierpressure/conditions/open_meteo.py` points at its
  spec through a `ClassVar`. It always asks for the same eleven hourly columns,
  2 forecast days, km/h and UTC. `parse_open_meteo` already treats a missing or
  `null` column as absent, so one parser serves any column subset.
- `build_provider` maps each catalog key to a factory for its real fetcher.
  `test_each_fetcher_points_at_its_catalog_spec` walks every `CATALOG` key, so
  it covers new keys without being edited.
- Health entities, topics and the verdict document are keyed by the provider
  key and named after its display name. They need nothing new for more keys.
- Live API check (brainstorm D1): HRDPS and RDPS return no
  `precipitation_probability`. HRRR and HRDPS answer HTTP 400 outside their
  areas.

## Goals / Non-Goals

**Goals:**

- One fetcher class serves `open_meteo` and the five model providers. Only the
  spec and the model identifier differ between them.
- Each model provider requests only the columns its spec declares.
- The `open_meteo` request stays byte-for-byte as it is today.

**Non-Goals:**

- Sharing one HTTP request across several models.
- Reading a model's run time from Open-Meteo's metadata API. The issue time
  stays the fetch time (D8).
- Checking the pier's coordinates against a model's area.

## Test Seams

- **Primary test seam:** `tests/test_conditions_provider.py`. It drives
  `OpenMeteoProvider.fetch` through an `httpx.MockTransport` and observes the
  request's query and the parsed `SourceForecast`. It drives `build_provider`
  and `CompositeProvider.get` for the fill and the outcomes.
- **Existing seams reused:** `tests/test_provider_catalog.py` for the
  declarations, and `tests/test_config.py` for the provider-list validation.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the conditions package and the catalog in the core. The
  five new keys become user-facing configuration values and health-sensor IDs,
  so their names are a contract from the first release. The default list and
  the `open_meteo` request don't change, so existing installs see no
  difference.

## Decisions

### D1. The model identifier lives with the fetcher, not in the core spec

`pierpressure/conditions/open_meteo.py` holds a table from provider key to the
Open-Meteo `models=` value. `ProviderSpec` gains no field.

- *Alternative:* an `open_meteo_model` field on `ProviderSpec`. Rejected: a
  spec says what a provider supplies, and an Open-Meteo request parameter is a
  network detail that the core and configuration never read. Adding the field
  would put a provider-specific concept into the core's plain data.

### D2. `OpenMeteoProvider` takes its spec and model as instance fields

`spec` becomes a dataclass field that defaults to `OPEN_METEO`, and a new
`model: str | None = None` field defaults to `None`, which sends no `models=`
parameter. A model provider is built as `OpenMeteoProvider(spec=OPEN_METEO_HRDPS,
model="gem_hrdps_continental", now=now)`. The class attribute still reads
`OPEN_METEO`, so existing code and tests that read `OpenMeteoProvider.spec`
still work.

- *Alternative:* a subclass per model. Rejected: five classes that differ only
  in two constants.

### D3. The request lists the columns the spec declares

The fetcher builds its `hourly` parameter from `spec.variables`, through a fixed
map from each variable to its Open-Meteo column (`wind_gust` →
`wind_gusts_10m`, and so on). For `OPEN_METEO` this gives the same eleven
columns in the same order as today, so its request does not change. HRDPS and
RDPS don't ask for `precipitation_probability`.

- *Alternative:* request all eleven columns and let the blank column fall
  through. Rejected: it asks Open-Meteo for something the declaration says the
  provider doesn't supply, and keeps two lists that must be kept in step by hand.

### D4. The model specs sit in the core catalog beside `OPEN_METEO`

`providers.py` adds `OPEN_METEO_HRRR`, `OPEN_METEO_HRDPS`, `OPEN_METEO_RDPS`,
`OPEN_METEO_ICON` and `OPEN_METEO_GFS` to `CATALOG`, after `OPEN_METEO` and
before `SEVEN_TIMER`. HRRR, ICON and GFS reuse `OPEN_METEO.variables`. HRDPS
and RDPS use the same tuple without `precipitation_probability`. All share the
cloud bundle.

### D5. `build_provider` builds the real fetchers from the model table

The factory map gains one entry per row of the D1 table. Each entry passes the
shared clock, as `open_meteo` does today, so each model's issue time and fetch
outcome come from the same clock.

### D6. Fixtures are trimmed live recordings

Each of the five models gets one fixture: a real response for a Great Lakes
point (Toronto), cut to four hours. The fixture keeps every column the model
returned, `null`s included, and the model's real `hourly_units`. The fixtures
show that the parser handles each model's real shape, such as a missing
`precipitation_probability` for HRDPS and RDPS.

### D7. Out-of-area is the existing HTTP-error path

No new code. `raise_for_status` raises on the 400, and `describe_error` reports
it as `HTTPStatusError: 400 Bad Request`. A test pins this behaviour for a
model provider, so a later change cannot quietly hide the error.

## Risks / Trade-offs

- [Open-Meteo renames a model identifier, as it has before] → The identifiers
  sit in one table. A rename then fails every fetch with an HTTP error that the
  provider's health sensor shows. The README names the identifier behind each
  key, so the fix is easy to find.
- [HRRR's precipitation probability is not HRRR's own: in the live check it
  matched best match exactly] → Carried as Open-Meteo reports it, as with every
  weather variable. The README says so. The verdict never reads it.
- [HRDPS reaches about 42–48 h, depending on the run] → Under the existing
  forecast-reach rule, hours past its reach stay empty. Tonight's dark window is
  always inside that reach. The README states each model's reach.
- [A user lists a model whose area doesn't cover their pier] → The provider's
  health sensor shows a 400 on every fetch, and the README lists each model's
  coverage.

## Migration & Rollback

N/A. No data or configuration changes shape. Rolling back removes the five
keys: a configuration that lists one then fails at startup with "is not a known
provider", and the user removes the key.
