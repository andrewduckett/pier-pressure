## Why

Transparency comes only from 7Timer!. Its index is 3-hourly, built from GFS, and blind to smoke. Water vapour and aerosol optical depth (AOD) drive most of the loss of sky brightness. Both are now available per hour from keyless Open-Meteo providers. The air-quality provider (#156) brought AOD, so the core can now compute transparency itself. Computed seeing (#160) reuses the computed source this story builds.

## What Changes

- A new raw variable, `column_water_vapour` in kg/m², is read from Open-Meteo's `total_column_integrated_water_vapour` (D10). Only the entries whose model returns it declare it: best match, HRRR and GFS (D1). Like AOD, it stays off the timeline (D3).
- A new catalog entry, `computed`, is the **computed** source from the glossary. It declares `transparency`, needs no key and fetches nothing. It runs after every provider has returned, and it takes part in the provider order like any other entry. It supplies no cloud, so it never satisfies the keyless-cloud guard (D2).
- Its inputs, water vapour and AOD, fill by ordinary provider order, with no bundle (D3). The core computes an hourly transparency index on the `[0, 1]` scale that 7Timer! is mapped onto (D4). An hour that lacks either input stays blank (D6). The series carries the oldest issue time of its inputs (D8).
- The `computed` entry gets a health record, like a provider. If no hour could be computed, its outcome is `failed`, and the error names each missing input. If any hour was computed, the outcome is `ok` (D7). Listing `computed` without the providers it needs does not stop startup (D9).
- `computed` is added at the end of the default provider list. It fills transparency only when 7Timer! returned none (D5).
- A decision record gives the formula and says it is uncalibrated.
- The README explains that `computed` fills transparency only when it is listed ahead of 7Timer!.

Nothing breaks. The verdict document and its entities stay the same, and a new health entity is added for `computed`. When 7Timer! returns transparency, a pier on the default list gets the same verdict as before.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: these requirements change:
  - the new `column_water_vapour` variable, and which Open-Meteo entries declare it
  - the `computed` catalog entry and its declaration
  - how and when `computed` derives transparency from its inputs, and where it sits in the fill
  - its outcome when an input is missing, as a new fixed error message
  - the default provider list
  - its place under the keyless-cloud guard

## Impact

- **Code:**
  - `pierpressure/core/conditions.py`: the `Variable` literal
  - `pierpressure/core/providers.py`: `CATALOG` and the Open-Meteo specs
  - `pierpressure/core/config.py`: `DEFAULT_PROVIDERS`
  - a new pure transparency computation in `pierpressure/core/`
  - `pierpressure/conditions/provider.py`: `assemble_snapshot`, `CompositeProvider` and `build_provider`
  - `pierpressure/conditions/open_meteo.py`: `COLUMNS`
  - `pierpressure/health.py`: the missing-input error message
- **Delivery:** additive only. A new `computed` health sensor appears for each pier, through the existing per-provider health entities.
- **Docs:** a new decision record in `docs/decisions/` and the README's conditions section. ADR 0005 and ADR 0027 are context.
- **Dependencies:** none. The Open-Meteo request adds one hourly column for the three entries that declare it.
