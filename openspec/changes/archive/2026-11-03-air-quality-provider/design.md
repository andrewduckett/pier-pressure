## Context

- `Variable` (`pierpressure/core/conditions.py`) is one `Literal` that serves
  two jobs: the fill walks it (`assemble_snapshot` in
  `pierpressure/conditions/provider.py`), and the timeline spreads it into
  `TimelineEntry` (`_timeline` in `pierpressure/core/producer.py`).
  `TimelineEntry` forbids extra keys, so adding a variable today either breaks
  the timeline or grows it.
- `Conditions.hours()` is the union of every filled series' hours, and only
  `_timeline` reads it.
- `OpenMeteoProvider` already builds its `hourly=` request from its spec's
  variables, through one `COLUMNS` map, and stamps the fetch time as the issue
  time. The model providers reuse it with a different spec and a `models=`
  value.
- The air-quality endpoint uses the same response shape (`hourly.time` plus
  one array per column). A live call on 2026-11-03 returned 48 hourly values
  for `forecast_days=2`, `timezone=UTC`. It ignored `wind_speed_unit`, and it
  rejected an unknown `models` value with an error.
- The default list is written twice in `pierpressure/core/config.py`: in the
  field's default and in the validator that reads `null` as "not given".

## Goals / Non-Goals

**Goals:**

- One place in the core says which variables the timeline shows. The timeline's
  keys and its hours both come from it.
- The new provider reuses the Open-Meteo fetch and parse path, so it gets the
  same partial-data and failure behavior with no new code path.

**Non-Goals:**

- Choosing the CAMS domain. The endpoint picks CAMS Europe inside Europe and
  CAMS global elsewhere, and that is accepted as it is.
- Sharing one HTTP request between the forecast and air-quality endpoints.
  They are different hosts.

## Test Seams

- **Primary test seam:** `produce_verdict` with a hand-built `Conditions`
  value, in `tests/test_producer_timeline.py`. It proves the hour rule and that
  air-quality series leave the document byte-identical.
- **Existing seams reused:** `httpx.MockTransport` with a recorded fixture in
  `tests/test_conditions_provider.py` for the request and the parse;
  `tests/test_conditions_model.py` for `Conditions.hours`;
  `tests/test_provider_catalog.py` for the declaration; `tests/test_config.py`
  for the default list; `tests/test_health_delivery.py` for the `variables`
  attribute.

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the core's conditions model and the timeline producer, the
  provider catalog, the Open-Meteo fetcher, the configuration default and the
  README. The verdict document's shape is unchanged. Default installs gain one
  outbound request per recompute and one health entity.

## Decisions

### DD1: A `TIMELINE_VARIABLES` tuple beside `Variable`

`Variable` gains `aerosol_optical_depth` and `pm2_5`, appended last so every
existing variable keeps its place in the fill order. A new
`TIMELINE_VARIABLES: tuple[Variable, ...]` in `core/conditions.py` lists the
thirteen variables the timeline shows, in timeline order. `_timeline` spreads
only those. A test pins `TIMELINE_VARIABLES` to the `TimelineEntry` fields
that hold a variable's value, so the two cannot drift.

Alternatives: a second `Literal` for the hidden variables, joined into
`Variable` with a union. `get_args` on a union returns the two `Literal`
types, not their values, so every walk over the variables would need
unwrapping. A per-variable "shown" flag on `ProviderSpec` puts a timeline fact
on the provider, where it doesn't belong: a variable is shown or not,
whichever provider fills it.

### DD2: `Conditions.hours()` takes the variables whose hours count

`hours(variables)` returns the sorted union of the hours of the filled series
of the given variables. The argument is required and has no default, so no
caller can count a raw variable's hours by forgetting it. `_timeline` passes
`TIMELINE_VARIABLES`. An explicit argument keeps the rule visible at the call
site and leaves `Conditions` free of timeline knowledge. The existing callers
in `tests/test_conditions_model.py` pass their variables explicitly.

Alternative: a separate `timeline_hours()` method on `Conditions`. That puts
the timeline's rule inside the conditions value, which only carries data.

### DD3: Reuse `OpenMeteoProvider`, with the endpoint chosen by the spec's key

`COLUMNS` gains `aerosol_optical_depth` and `pm2_5`, each named the same as
the endpoint's column. A module map `ENDPOINTS`, keyed by provider key like
`MODELS`, sends `open_meteo_air_quality` to the air-quality URL. Every other
key gets the forecast URL. `OpenMeteoProvider` looks its URL up from its
spec's key, so no caller can pair the air-quality spec with the forecast URL.
It sends `wind_speed_unit=kmh` only when its spec declares a wind variable,
so the air-quality request carries no parameter that endpoint ignores.
`parse_open_meteo` is unchanged: a column the payload lacks is left `None`, so
each endpoint's payload fills only its own variables. `SourceReading` gains the
two fields. `build_provider` registers `open_meteo_air_quality` as
`OpenMeteoProvider(spec=OPEN_METEO_AIR_QUALITY, now=now)`.

Alternatives: a separate `url` field beside `spec`. It lets a caller pass the
air-quality spec with the forecast URL, and the forecast endpoint rejects the
air-quality columns with HTTP 400. A separate module like `nws.py` copies the
request, the parse and the issue-time stamping for no difference in behavior.

### DD4: One `DEFAULT_PROVIDERS` constant

`core/config.py` holds `DEFAULT_PROVIDERS = ("open_meteo", "seven_timer",
"open_meteo_air_quality")`, and both the field default and the `null`
validator read it.

### DD5: The fixture is a live recording

`tests/fixtures/open_meteo_air_quality.json` is the response for the existing
fixture's coordinates (51.5, -0.12) with `forecast_days=2` and `timezone=UTC`,
saved as returned. The parse tests read values from it by hour.

No decision here needs a record: each one is local and cheap to undo.

## Risks / Trade-offs

- [Open-Meteo renames a column, as it has renamed model identifiers before]
  → the series comes back empty, the health sensor shows the failure as "no
  readings", and the verdict does not change, because nothing reads these
  variables.
- [Default installs make one more request per recompute] → it is keyless and
  free, and well inside Open-Meteo's daily limit at any sensible interval. A pier
  that doesn't want it lists its own providers.
- [The endpoint answers with every value null, for example during a CAMS
  gap] → the fetch counts as a success, as it does for every provider, so the
  health sensor shows `ok` while no series is filled. Health tracks whether the
  provider answered, not whether its values were present. Changing that is a
  rule for all providers, not for this one.
- [A new health entity appears on default installs and can show a failure that
  affects nothing] → the README says that nothing reads the air-quality
  variables yet.

## Migration & Rollback

No data or configuration migration. A pier with no `conditions` block picks up
the new provider on upgrade. A pier with its own list is unaffected. To roll
back, revert the change. The health entity the provider created stays in Home
Assistant as an orphan until it is deleted there, as with any provider
removed from the list.
