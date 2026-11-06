## Why

Seeing comes only from 7Timer!. Its index is 3-hourly, built from coarse GFS output, and publishes no formula. Every free seeing forecast is derived from a model's vertical column, and Open-Meteo now serves that column per hour for keyless models. The computed source that #159 built can derive seeing the same way it derives transparency, so a pier can rank the two against each other.

## What Changes

- New raw variables carry the **seeing column**: temperature and geopotential height at 17 pressure levels from 1000 to 50 hPa, the 300 hPa wind speed and boundary-layer height (D3). Like aerosol, they stay off the timeline (D13).
- The seeing column is one **bundle**, so it is filled whole from one model or not at all. Only the Open-Meteo entries whose model returns all of it declare it: best match, HRRR and GFS. HRDPS, RDPS and ICON return no boundary-layer height, so they do not declare it (D1, D2).
- `computed` declares `seeing` beside `transparency`. The core derives an hourly seeing index on the `[0, 1]` scale that 7Timer! is mapped onto. It counts bad layers between the pier's ground and the tropopause (D4, D5), and reads the jet-stream speed (D6) and boundary-layer height. More bad layers, a jet further outside 5 to 35 m/s, or a deeper boundary layer never raise it (D7).
- Each computed series carries the oldest issue time of its own inputs (D11).
- The `computed` health record changes in three ways:
  - **Partial success.** When one computed variable works and the other fails, the status is `ok` and the error says which variable failed and why (D9).
  - **Error wording.** When both fail, the status is `failed` and the error lists each failure, prefixed by its variable. This rewords today's transparency-only errors, such as `missing input: aerosol_optical_depth`, to name `transparency` (D10).
  - **New `inputs` attribute.** It maps each computed variable to the providers that fed it on the last success (D12).
- The default provider list does not change. `computed` stays last, so 7Timer!'s seeing wins, and computed seeing fills only when 7Timer! returns none (D8).
- A decision record gives the seeing formula, records the model check from D1 and says the index is uncalibrated.
- The README explains computed seeing, which models can feed it, and the new health attribute.

The verdict document and its entities stay the same. When 7Timer! returns seeing, a pier on the default list gets the same verdict as before. The only delivery changes are the `computed` health sensor's error wording and its new attribute. A Home Assistant automation that matches the old error text exactly needs updating.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: these requirements change:
  - the seeing-column variables, their bundle, and which Open-Meteo entries declare them
  - the `computed` declaration, which gains `seeing`
  - how `computed` derives seeing, which hours it covers and which issue time each computed series carries
  - the `computed` outcome when one or both derivations fail, and its error wording
- `night-verdict`: the requirement that variables the timeline does not show never change the document now covers the seeing column, and names computed `seeing` as a way such a value reaches the document.
- `ha-delivery`: the computed source's health sensor gains the `inputs` attribute, and the meaning of its error when its status is `ok`.

## Impact

- **Code:**
  - `pierpressure/core/conditions.py`: the `Variable` literal
  - `pierpressure/core/providers.py`: the Open-Meteo specs, their bundles and `COMPUTED`
  - `pierpressure/core/computed.py`: a new pure seeing derivation beside transparency
  - `pierpressure/conditions/provider.py`: `SourceReading`, `ComputedSource.derive` and the computed outcome; `assemble_snapshot` is unchanged
  - `pierpressure/conditions/open_meteo.py`: `COLUMNS` and the request's wind unit for the 300 hPa wind
  - `pierpressure/health.py` and the health publisher: the error wording and the `inputs` attribute
- **Delivery:** additive, except the reworded `computed` error text. No topic, entity or verdict field changes.
- **Docs:** a new decision record in `docs/decisions/`, and the README's conditions and health sections. ADR 0027, 0030, 0031 and 0032 are context.
- **Dependencies:** none. The Open-Meteo request for best match, HRRR and GFS grows by 36 hourly columns. That is still one request per model.
