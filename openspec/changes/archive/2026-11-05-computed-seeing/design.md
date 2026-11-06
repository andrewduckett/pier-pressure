## Context

- `computed` already derives transparency (ADR-0031, ADR-0032). `CompositeProvider.get` fetches every provider, fills once without `computed`, calls `ComputedSource.derive(conditions)`, and fills again with the computed forecast in its slot. `assemble_snapshot` is a pure fill over `(ProviderSpec, SourceForecast)` pairs.
- A `SourceForecast` carries one `issued_at`, and `_series` stamps it on every series the forecast fills. Two computed series with different issue times can't come from one forecast as it stands.
- `ComputedSource.derive` returns one forecast and one error, so its outcome is all or nothing. `fold` in `pierpressure/health.py` clears `last_error` on every success.
- `Variable` is a `Literal`. `SourceReading` has one field per variable, and `_returned` and `_series` read them with `getattr`. `COLUMNS` in `open_meteo.py` maps each variable to its Open-Meteo hourly name, and the request asks for every column the spec declares.
- The Open-Meteo request already sets `wind_speed_unit=kmh` when a spec declares `wind_gust` or `wind_speed`. Every spec that declares the seeing column also declares those, so `wind_speed_300hPa` arrives in km/h with no request change.
- `PierConfig.elevation_m` exists. Geopotential height is height above mean sea level, so the two compare directly. Open-Meteo gives values for levels below the ground, extrapolated.
- `seeing` is already scored from whichever series fills it. Scoring needs no change.

## Goals / Non-Goals

**Goals:**

- Derive seeing in pure core code from the filled seeing column, beside transparency in `pierpressure/core/computed.py`.
- Keep `assemble_snapshot` and its tests unchanged.
- Let each computed variable succeed or fail, and carry its issue time, on its own.
- Answer computed-transparency's open question on issue times and partial outcomes.

**Non-Goals:**

- Calibrating the formula, or giving arcseconds.
- Reading pressure-level wind other than 300 hPa, or wind shear.
- A second computed source key. ADR-0031 keeps one source for every computed variable.
- `inputs` on any health record but `computed`.

## Test Seams

- **Primary test seam:** `build_provider(keys, now=…, fetchers={key: stub})`, then `.get(pier)`. It returns the snapshot and the outcomes, and it covers fill order, the seeing-column bundle, issue times, inputs and every error scenario (`tests/test_conditions_provider.py`).
- **Existing seams reused:**
  - `tests/test_computed.py` for the pure formula: range, monotonicity, bad layers, ground and tropopause, and the ADR's worked values
  - `tests/test_provider_catalog.py` for the declarations and bundles
  - the Open-Meteo request and parse tests in `tests/test_conditions_provider.py`
  - `tests/test_health.py` for `fold`, and `tests/test_health_delivery.py` for the published attributes
  - the night-verdict test that holds the raw-variable byte-identity scenarios

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:**
  - **Conditions:** the `Variable` literal, `SourceReading`, the Open-Meteo specs and `COLUMNS`, `ComputedSource` and `CompositeProvider.get`, and the pure core module.
  - **Health and delivery:** `FetchOutcome`, `ProviderHealth`, `fold` and `health_attributes`. The `computed` error text changes for every pier that lists `computed`, which is every pier on the default list.
  - **Unaffected:** the verdict core, the timeline, scoring and every topic and entity.

## Decisions

### DD1. The 36 variables are written out, and one tuple names the column

`Variable` gains the 36 keys, appended after `column_water_vapour`, in the spec's order: temperature then geopotential height for each level from 1000 to 50 hPa, then `wind_speed_300hpa` and `boundary_layer_height`. `SourceReading` gains one field for each. `pierpressure/core/conditions.py` holds `SEEING_COLUMN: tuple[Variable, ...]` and `SEEING_LEVELS: tuple[int, ...]`, also written out. `COLUMNS` builds its 36 entries from `SEEING_COLUMN` by upper-casing the unit, `hpa` to `hPa`. A test checks that the tuple, the literal's tail and the `SourceReading` fields agree.

**Alternatives:**

- **Turn `SourceReading` into a mapping.** One storage path for every variable, but it rewrites every provider and its tests for a change that adds no behavior.
- **Carry the column as one variable that holds a profile.** A `Series` holds floats, so this breaks the fill, alternates and the timeline rule for one source.

Written out, the names stay typed for mypy and easy to search for.

### DD2. The seeing column is a declared bundle on three specs

`OPEN_METEO` declares the 36 variables after `column_water_vapour`, and gains a second bundle, `frozenset(SEEING_COLUMN)`. HRRR and GFS inherit both through `replace`. ICON, HRDPS and RDPS get variable lists without the column and `bundles=` the cloud bundle alone. The fill needs no change: `bundle_of` and the bundle rule already keep the column whole.

### DD3. Each computed variable is its own fill at the computed slot

`ComputedSource` holds its two derivations as fields, `transparency=computed_transparency` and `seeing=computed_seeing`. A test replaces one through `build_provider(fetchers={"computed": ComputedSource(seeing=raising)})`, at the primary seam.

`ComputedSource.derive(conditions, pier)` returns a `Derived` value:

- `fills`: one `(spec, forecast)` pair per computed variable that carries a value, in declared order. Each spec is `replace(COMPUTED, variables=(variable,))`, and each forecast carries that variable's issue time.
- `issued_at`, `inputs` and `error` for the outcome (DD5).

`CompositeProvider.get` puts these pairs side by side at the computed slot in the second fill. Each pair declares one variable that the other doesn't, so neither touches the other's fill, and `assemble_snapshot` stays as it is. Every series still carries the key `computed`.

**Alternative:** add per-variable issue times to `SourceForecast`. This changes `_series` and the fill for every provider, to serve one source.

### DD4. The seeing math is a pure core function

`computed_seeing(column, elevation_m) -> SeeingDerivation` in `pierpressure/core/computed.py` takes the filled series for each `SEEING_COLUMN` variable (any may be `None`) and the pier's elevation. It returns:

- a `Series` keyed `computed`, covering the column's hours, blank where any member is blank, and carrying the column's issue time
- `MissingColumn()` when any member has no series
- `NoSharedHour()` when no hour carries every member

Per hour:

1. **Tropopause.** Walk the levels upward from 500 hPa. The tropopause is the first level whose next level is higher, and whose temperature falls by 2 K per km or less to that level. If none qualifies, there is no cap.
2. **Bad layers.** Count `n`: the layers between adjacent levels whose lower height is at or above `elevation_m`, which lie below the tropopause, and whose `ΔT / Δz` is greater than −0.00476 K/m.
3. **Index.** Apply DD6 to `n`, the 300 hPa wind and the boundary-layer height.

The bad-layer threshold is a potential-temperature rise of 0.5 K per 100 m, measured at 1000 hPa: `ΔT / Δz + g / c_p > 0.005 K/m`, with `g / c_p` = 0.00976 K/m. A raw `Δθ / Δz` grows with `(1000 / p) ^ 0.286`, about 1.6 times at 200 hPa. Above about 250 hPa it would count air cooling at the standard 6.5 K per km as bad, so summer nights with a high tropopause would start with bad layers. Every comparison multiplies by `Δz` rather than dividing by it. A layer whose heights don't increase upward is neither bad nor a tropopause, so bad data never divides by zero and never caps the count. `computed_transparency` is unchanged.

### DD5. The outcome is built from per-variable results

`derive` runs each derivation in its own `try`. A raising derivation becomes that variable's failure, worded by `describe_error`. Each failure becomes `<variable>: <reason>`:

- `missing_input(keys)` for transparency
- `missing input: seeing column` for seeing, a fixed string `MISSING_SEEING_COLUMN` in `health.py`
- `NO_SHARED_HOUR`, or the error kind

The parts are joined with `"; "` in declared order, transparency first.

- `ok` is true when any variable has a series.
- `issued_at` is the earliest issue time, ignoring `None`, among the series that succeeded.
- `inputs` maps each successful variable to the provider keys of the filled series it read, each key once, in input order. For seeing that is the column's one provider.

`_safe_derive` still guards the whole call, for a bug outside the per-variable `try`. If `derive` itself raises, the outcome is failed. Its error gives the error kind once for each declared variable, in the same `<variable>: <reason>` form.

`FetchOutcome` gains `inputs: Mapping[str, tuple[str, ...]] | None = None`. Providers leave it `None`.

### DD6. The seeing index sums three capped penalties

`q = clamp(1 − 0.12 × n − P_jet − P_blh, 0, 1)`:

- `n` is the number of bad layers.
- `P_jet = 0.4 × clamp((w − 126) / 126, 0, 1) + 0.15 × clamp((18 − w) / 18, 0, 1)`, for the 300 hPa wind `w` in km/h. A jet between 18 and 126 km/h (5 to 35 m/s) costs nothing. A strong jet costs up to 0.4 at 252 km/h (70 m/s). A stagnant one costs up to 0.15.
- `P_blh = 0.25 × clamp((h − 200) / 1300, 0, 1)`, for boundary-layer height `h` in metres. A layer up to 200 m deep costs nothing, and the cost reaches 0.25 at 1500 m.

Each penalty can only grow as its input worsens, so the monotonicity scenarios hold. Worked values for the ADR and the tests:

| Hour | n | w (km/h) | h (m) | q |
|---|---|---|---|---|
| Calm and stable | 0 | 80 | 150 | 1.0 |
| Typical | 2 | 150 | 500 | 0.6261 |
| Jet and mixing | 3 | 250 | 900 | 0.1117 |

The bad layers carry the largest share, since they are the term the story is named for. The jet is the next largest, because high-altitude turbulence dominates poor seeing on jet nights. The weights are uncalibrated and costly to change silently, so they get a decision record in the ADR step. The record also documents the model check from D1.

**Alternatives:**

- **Estimate arcseconds, then map them onto 7Timer!'s bins, as transparency does with extinction.** No free source gives a formula from these inputs to arcseconds. An arcsecond figure would claim precision the index doesn't have.
- **A product of three factors.** Any one bad term then zeroes the index, which over-punishes a single strong inversion.

### DD7. Health keeps the computed error on success, and adds `inputs`

- `fold`, on success, sets `last_error=outcome.error` instead of `None`. A provider's successful outcome has no error, so providers behave as before.
- `ProviderHealth` gains `inputs`. On success it takes `outcome.inputs`. On failure it keeps the earlier value.
- `health_attributes` adds `"inputs"` only when `health.key == COMPUTED.key`. A startup reset therefore publishes `inputs: null` for `computed`, and no other record changes shape.

## Risks / Trade-offs

- [The rewording `transparency: missing input: …` breaks a Home Assistant automation that matched the old text] → The README's health section shows the new wording, and the pull request flags it. The error was never documented as stable.
- [When 7Timer! is down, uncalibrated seeing reaches default verdicts] → This only happens on outage nights. It moves the score by at most the atmosphere factor's seeing half. The `computed` health record and its `inputs` show when it ran and from which model.
- [The tropopause test misreads a strong inversion between 500 hPa and the real tropopause, and stops counting early] → This is rare at night in mid-latitudes, and it only undercounts. The ADR names it as a calibration target.
- [The Open-Meteo request grows to 48 columns for three models] → It is still one request per model. The URL is about 1.5 kB, well inside common limits. The request test pins the count.
- [A model drops the whole column] → The bundle falls through to the next model that declares it. If none is left, the error names `seeing column`.
- [A declaring model returns only part of the column, for example best match at a pier where it picks a model with no boundary-layer height] → It wins the bundle, as ADR-0027's fill rule says, and the next model's complete column is only an alternate. Seeing then fails with `seeing: no hour has every input`. The `computed` health record shows it, so the pier owner can list HRRR or GFS first. The D1 check covered one location, so the README names this case.
- [36 named fields are long to read in `Variable` and `SourceReading`] → One tuple and one test keep them in step (DD1).

## Migration & Rollback

- **Deploy:** none. The `computed` health sensor gains an `inputs` attribute, and its error text changes. A pier that doesn't list `computed` sees no change except the larger Open-Meteo request.
- **Rollback:** revert the change. The `inputs` attribute disappears at the next publish, because attributes are replaced whole. No retained topic is added.
