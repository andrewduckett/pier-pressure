## Context

`OpenMeteoProvider` (`pierpressure/conditions/open_meteo.py`) serves plain
best match, the five model providers and the air-quality provider. It makes one
request and stamps `issued_at=self.now()`. Two tables key request details by
provider key: `MODELS` (the `models=` value) and `ENDPOINTS` (a non-forecast
host). `build_provider` builds each model provider from `MODELS` with the stack's
clock.

`CompositeProvider._safe_fetch` turns any exception from `fetch` into a failed
outcome and copies `forecast.issued_at` into a successful one. So the provider
alone decides the issue time, and a metadata failure must not raise out of
`fetch`, or it would fail the fetch, which D7 rules out.

The core needs no change. `freshness_factor` reads the cloud series' issue time
and already treats `None` as maximally stale. Health already publishes a null
`issued_at`.

Open-Meteo's metadata file is a small JSON object. Each time field is seconds
since the Unix epoch. Only `last_run_initialisation_time` is read (D1).

## Goals / Non-Goals

**Goals:**

- Each model provider carries its run start as its issue time, read from one
  fixed metadata file (D2–D6).
- A metadata failure leaves the forecast usable with a null issue time (D7–D9).
- Plain `open_meteo` and air quality make exactly the request they make today.

**Non-Goals:**

- Caching the run time between recomputes. One small request per model per
  recompute is cheap, and a cache would add state that can itself go stale.
- Sharing one request across models (#164 Scope, out).
- Checking that the run in the metadata is the run in the forecast data. The
  response carries no run identifier to compare against.

## Test Seams

- **Primary test seam:** `build_provider([...]).get(pier)` with each fetcher's
  `client` replaced by an `httpx.MockTransport` that answers by URL path: the
  forecast path returns a recorded forecast, `/data/<name>/static/meta.json`
  returns a recorded metadata file or an error. It proves the series' issue time,
  the outcome's issue time and success, and which URLs were requested, through
  the production stack.
- **Existing seams reused:** `tests/test_conditions_provider.py`, its `_load`
  fixture loader and `_open_meteo_stack` helper. The helper answers by the
  `models=` parameter today, so it must route metadata requests by path. Model
  tests that do not care about the run time get a default metadata answer.
  `_requests_of` returns every request, so the tests that unpack exactly one
  request from a model provider must pick the forecast request instead:
  `test_the_forecast_providers_ask_the_forecast_endpoint`,
  `test_a_model_provider_asks_for_its_model_and_its_declared_variables_only`
  and `test_each_model_provider_names_exactly_its_own_model`.
  `test_a_model_provider_stamps_its_fetch_time_as_the_issue_time` pins the
  removed requirement, so it is replaced, not patched.
  New fixture: a recorded `meta.json` trimmed of `crs_wkt`.

## Scrutiny Tier & Blast Radius

- **Tier:** medium. One module on an established pattern, but a new endpoint
  call on every model fetch and a change in the confidence those piers see.
- **Blast radius:** `pierpressure/conditions/open_meteo.py` and its tests; the
  `build_provider` docstring; the README. No core, delivery or configuration
  change.

## Decisions

### DD1: A `RUN_METADATA` table keyed by provider key

Add `RUN_METADATA: Mapping[str, str]` beside `MODELS` and `ENDPOINTS`, mapping
each model provider's key to its metadata name. `fetch` reads the run time only
when its spec's key is in the table. `build_provider` is unchanged.

- *Alternative:* fold both names into `MODELS` as a pair, or pass the name into
  the constructor. A pair changes every reader of `MODELS`; a constructor field
  lets a test or caller pair a spec with the wrong name. Keying by spec is the
  reason `ENDPOINTS` exists (air-quality-provider DD3), so this follows it.

### DD2: Read the metadata before the forecast

Fetch the metadata first, then the forecast, through the same client. If a new
run lands between the two calls, the data is newer than the stamp, and
confidence understates freshness rather than overstating it, which is the safe
side for this story.

- *Alternative:* forecast first. One request fewer if the forecast fails, but a
  run landing between the calls then makes old data look new.

### DD3: The run-time read never raises

A private `_run_start(client, name) -> datetime | None` makes the request and
converts the value with `datetime.fromtimestamp(value, UTC)`. It returns `None`
in each of these cases:

- `httpx.HTTPError`: status and transport errors;
- `ValueError` from `response.json()`: a body that is not JSON, such as an HTML
  error page sent with status 200;
- a parsed body that is not a JSON object;
- a `last_run_initialisation_time` that is missing or not an `int` (a `bool` is
  not accepted);
- `OverflowError`, `OSError` or `ValueError` from `fromtimestamp`: an integer
  outside the range a `datetime` can hold.

It logs a warning with the error, as `_safe_fetch` does, so the full text stays
in the log only (D8).

Exceptions outside that set, such as a bug, still raise and fail the fetch
through `_safe_fetch`, which is the project's rule for unexpected errors.

`parse_open_meteo` widens `issued_at` to `datetime | None`, so a model provider
can pass the null run time through.

- *Alternative:* catch every exception. That would hide a bug as a null issue
  time, and a null issue time only shows as lower confidence.

### DD4: The forecast fails the fetch whatever the metadata says

When the forecast request fails or returns no readings, `_safe_fetch` already
fails the outcome with a null issue time. The metadata result is simply
discarded; no new code path.

## Risks / Trade-offs

- [Open-Meteo moves a model to a new metadata name again, as it did with RDPS,
  and the old file stops updating] → The old file reports an ever older run,
  so confidence drops and health's `issued_at` shows a date long past, which is
  visible rather than silently fresh. The README says how to read that. A
  rename to a missing file returns 404 and a null issue time.
- [A second request per model doubles the calls to Open-Meteo] → The metadata
  file is small and keyless, on the same 10-second timeout. Five models make
  ten calls per recompute, within Open-Meteo's free limits.
- [The metadata file does not depend on the pier, yet each pier fetches it
  again, and a pier outside a regional model's area fetches it only for the
  forecast to fail. Three piers and five models make 15 metadata calls per
  recompute] → Accepted. Each call is a small keyless file, and the forecast
  calls already scale the same way. Sharing a fetch across piers would add
  state between per-pier fetches, which this change keeps out (Non-Goals).
- [ICON global is older than ICON-EU or -D2 for a European pier, so its first
  hours look older than they are] → Accepted (D5). It errs toward lower
  confidence.

## Migration & Rollback

N/A. No configuration, document or delivery shape changes. Reverting the change
restores the fetch time as the issue time.
