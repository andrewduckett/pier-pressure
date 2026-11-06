## Context

- `CompositeProvider.get` (`pierpressure/conditions/provider.py`) fetches every listed provider, each guarded, and then calls `assemble_snapshot`. That fill is a pure function over `(ProviderSpec, SourceForecast)` pairs in configured order. It fills each variable from the first provider that returned it, and keeps the later ones as alternates.
- Every entry in `CompositeProvider.fetchers` is a `Provider`: something with a `spec` and a `fetch(pier)`. `CompositeProvider.providers` builds the `ProviderInfo` list that the service turns into health records. The outcomes come back in fetcher order.
- The `computed` source fetches nothing. Its inputs only exist once the providers' fill has run, and its own transparency series then has to take part in that same fill at its place in the order. So it can't be an ordinary `Provider`, and the fill can't run once.
- `transparency` is already a shown variable on the `[0, 1]` scale, 1 best. 7Timer! maps its index 1 to 8 as `(8 − i) / 7`. Its index bins are total extinction in magnitudes per airmass: below 0.3 is index 1, and above 1.0 is index 8.
- The core must stay pure (`tests/test_core_boundary.py`). The night-verdict requirement says raw variables never change the document. So derivation happens before `produce_verdict`, and the core verdict code never reads the raw inputs.
- Open-Meteo's `aerosol_optical_depth` is the CAMS value at 550 nm, close to the V band. `total_column_integrated_water_vapour` is in kg/m², which equals millimetres of precipitable water.

## Goals / Non-Goals

**Goals:**

- Derive transparency in pure core code, from the filled input series only.
- Keep `assemble_snapshot` and its existing tests unchanged. The computed series takes part as one more `(spec, forecast)` pair.
- Give `computed` a health record by the same path as every provider.
- Give computed seeing (#160) a catalog entry, a core module and a fill path to extend. How it reports a second derivation's issue time and outcome is left to that story.

**Non-Goals:**

- Calibrating the formula, or correcting it for pier elevation or airmass.
- Reading alternates of the inputs.
- Showing the inputs, or which source filled transparency, anywhere new in the verdict document.

## Test Seams

- **Primary test seam:** `build_provider(keys, now=…, fetchers={key: stub})`, then `.get(pier)`. It runs the production stack with stub forecasts and no network, and it returns the snapshot and the outcomes. Fill order, coverage, alternates, issue time and every outcome scenario are asserted here (`tests/test_conditions_provider.py`).
- **Existing seams reused:**
  - `tests/test_provider_catalog.py` for the declarations
  - `tests/test_config.py` for the default list and the cloud guard
  - the Open-Meteo request and parse tests in `tests/test_conditions_provider.py`
  - `tests/test_producer_timeline.py`, or the night-verdict test that holds the raw-variable scenarios, for the water-vapour byte-identity scenario
  - one new pure test file for the formula's range, its monotonicity and the ADR's worked values

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:**
  - **Conditions:** the provider layer (`CompositeProvider.get`, `build_provider`, the Open-Meteo columns), the core catalog, the `Variable` literal, and a new pure core module.
  - **Configuration and delivery:** the default provider list changes, so every pier without an explicit list gains a `computed` health sensor and a transparency fallback. That health sensor is the only new delivery output, through the existing per-provider mechanism.
  - **Unaffected:** the verdict core's scoring code is untouched.

## Decisions

### DD1. The fill runs twice, around the derivation

`CompositeProvider.get` works in four steps:

1. Fetch every network provider, as today.
2. Run `assemble_snapshot` over the providers' fills without `computed`, to get the filled inputs.
3. Derive the computed forecast from that snapshot.
4. Run `assemble_snapshot` again over every fill in configured order, with the computed forecast in its slot. That result is the snapshot.

`computed` declares only `transparency`, which no input depends on. So the first pass gives the same input series as the second pass, and the result doesn't depend on where `computed` is listed.

**Alternatives:**

- **Derive inside `assemble_snapshot`.** This mixes a derivation into a pure fill and changes the fill's signature and tests.
- **Derive inside `produce_verdict`.** The computed series then can't take part in the provider order. It would also break the requirement that raw variables never change the document for a given snapshot.

### DD2. `ComputedSource` is a derived source, not a `Provider`

The conditions layer gets a `ComputedSource` with a `spec` (`COMPUTED`) and a `derive(conditions)` method. It returns the computed `SourceForecast` and the failure reason for the outcome, which is `None` on success. `CompositeProvider.fetchers` becomes `Sequence[Provider | ComputedSource]`. `get` fetches the providers, defers the derived sources to step 3 of DD1, and keeps each outcome in its slot. `providers` reads every entry's `spec`, so the health records follow without change.

`build_provider` maps the key `computed` to a `ComputedSource`. Its `fetchers` overrides widen to `Mapping[str, Provider | ComputedSource]`, so a test can still replace any entry.

**Alternative:** a `derived` flag on `ProviderSpec`. Configuration has no use for it, and it would put an edge concern into the core catalog.

### DD3. The math is a pure core function

`pierpressure/core/computed.py` holds `computed_transparency(water_vapour, aerosol) -> Derivation`. It takes the two filled `Series | None`, and returns either:

- a `Series` keyed `computed`, covering the hours both inputs cover, with `None` where either value is blank, and carrying the earlier issue time that is not `None`, or
- the reason nothing was computed: the missing input keys, or no shared hour with a value.

`ComputedSource.derive` turns the result into a `SourceForecast` of `transparency` readings and the failure reason. Seeing (#160) adds a sibling function to this module.

### DD4. The formula estimates extinction, then maps it onto 7Timer!'s scale

For each hour, estimate the total V-band extinction at the zenith, in magnitudes per airmass:

`E = 0.17 + 1.086 × AOD + 0.006 × W`

- `0.17` is a fixed Rayleigh-plus-ozone floor at sea level.
- `1.086 × AOD` converts optical depth to magnitudes.
- `0.006 × W` is a small haze proxy for water vapour `W` in kg/m². At 40 kg/m² it adds 0.24 mag.

Map `E` linearly across 7Timer!'s index range: `q = clamp((1.0 − E) / 0.7, 0, 1)`. At `E` of 0.3 or less, `q` is 1, like index 1. At 1.0 or more, `q` is 0, like index 8.

Neither input can raise `q`, so the monotonicity scenarios hold, and every value lies in `[0, 1]`. Worked values for the ADR and the tests:

| Hour | AOD | W (kg/m²) | E | q |
|---|---|---|---|---|
| Clean and dry | 0.05 | 10 | 0.2843 | 1.0 |
| Typical summer | 0.15 | 30 | 0.5129 | 0.6959 |
| Smoke | 0.60 | 20 | 0.9416 | 0.0834 |

The formula and its constants are uncalibrated, and are costly to change silently once nights are compared against it. They get a decision record in the ADR step.

**Alternatives:**

- **A product of two independently clamped terms.** This has no physical unit, and ranks poorly against 7Timer!, whose bins are extinction.
- **Stepping through 7Timer!'s exact bins.** This gives a staircase with no benefit for an uncalibrated estimate.

### DD5. The derivation is guarded like a fetch

If `derive` raises, the outcome is failed with the kind of error, built by `describe_error`, and there is no computed forecast. The snapshot is as if `computed` returned nothing. A bug in the math never fails the snapshot.

### DD6. The missing-input errors are fixed strings in `health.py`

`missing_input(variables)` builds `missing input: <keys>` from variable keys only. `NO_SHARED_HOUR = "no hour has every input"` sits beside `NO_READINGS`. Both are fixed parts under the safe-error rule. The core returns which keys were missing, and the edge formats the message.

### DD7. Column water vapour joins Open-Meteo as an ordinary variable

- `column_water_vapour` is appended last to `Variable`. It is not added to `TIMELINE_VARIABLES`.
- `SourceReading` gains the field, and `COLUMNS` maps it to `total_column_integrated_water_vapour`.
- `OPEN_METEO` declares it last. HRRR and GFS inherit it through `replace`. ICON gets an explicit list without it. HRDPS and RDPS drop it with precipitation probability.
- `COMPUTED` is a `ProviderSpec` with the key `computed`, the name `Computed`, `needs_key=False` and `variables=("transparency",)`. It is in `CATALOG`, and appended last to `DEFAULT_PROVIDERS`.

## Risks / Trade-offs

- [On a 7Timer! outage, uncalibrated transparency reaches default verdicts and removes the coverage trim on confidence] → It is limited to outage nights. It can move the score by at most the atmosphere factor's transparency half. The README and the ADR say the value is uncalibrated, and the `computed` health record shows when it ran.
- [The fixed Rayleigh floor ignores pier elevation, so a high pier reads slightly pessimistic, by about 0.04 in `q` at 1500 m] → This is accepted while uncalibrated. Calibration (the epic's Could) can add elevation.
- [Water vapour absorbs little in the V band, so its term is a haze proxy, not physics] → Its weight is kept small, and the ADR says so.
- [The forecast and air-quality endpoints may cover different hours] → The series covers only the hours both inputs cover, and gaps stay blank.
- [Open-Meteo stops returning water vapour for a model] → A blank column falls through to the next declaring provider. If none is left, the outcome names the missing input.

## Migration & Rollback

- **Deploy:** none. On upgrade, a pier without an explicit provider list gains `computed` at the end of its order, and a `computed` health sensor appears.
- **Rollback:** revert the change. The retained `computed` health discovery config stays on the broker until it is cleared. The README's clean-up list gains `sensor/pierpressure_<pier>/computed_health`.

## Open Questions

- **For computed seeing (#160).** A `SourceForecast` carries one issue time, and the outcome is all or nothing. When `computed` derives two variables, their inputs can have different issue times, and one can fail while the other succeeds. #160 decides how those reach the series and the health record. This story derives one variable, so neither case arises here.
