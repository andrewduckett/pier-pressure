## 1. The measure and the factor

- [x] 1.1 [easy] `observed_cloud(observation)` in `pierpressure/core/observation.py` returns `62` for `FEW` 3000 and `BKN` 4200, `12` for `FEW` 3000 and `OVC` 25000, `0` for `BKN` with no base, `100` for `VV` at 200 ft and for `VV` with no base, and `0` for a report with no layers (design DD1) (verify: uv run pytest tests/test_observation.py -q -k observed_cloud) (✓ uv run pytest tests/test_observation.py -q -k observed_cloud passed)
- [x] 1.2 [medium] `observed_term(instant, conditions, observation)` in `pierpressure/core/scoring.py` reads the filled `cloud_low` and `cloud_mid` at the instant's hour (21:30 reads the 21:00 slot), gives `forecast` `19` for `10` and `10`, `gap` `observed − forecast`, and `factor` 1 under 15, `_A_MIXED` from 15 to 35 and `_A_DISAGREE` above 35; it returns `None` without an observation or without a low or mid value for that hour, and ignores `cloud_high` (design DD2, DD3) (verify: uv run pytest tests/test_scoring.py -q -k observed) (✓ uv run pytest tests/test_scoring.py -q -k observed passed)
- [x] 1.3 [easy] `confidence(..., observed=term)` multiplies the agreement factor and the term's factor, and the MEDIUM clamp covers the product: raw 30 with a factor of `_A_DISAGREE` gives 20, and raw 50 with `DISAGREE` agreement and a disagreeing term gives 40; `observed=None` leaves every value unchanged (design DD4) (verify: uv run pytest tests/test_scoring.py -q -k confidence) (✓ uv run pytest tests/test_scoring.py -q -k confidence passed)

## 2. The verdict [depends-on: 1]

- [x] 2.1 [medium] `produce_verdict` passes the usable observation to `evaluate`, so confidence falls for a report above this hour's forecast (100 → 90 for a gap of 22, 100 → 67 on a wind `NO-GO`), and is unchanged for a gap under 15, a clear or `CAVOK` report, a stale report, an hour with no mid cloud and a night with no dark window; `verdict`, `score`, `agreement` and `timeline` never change (design DD5) (verify: uv run pytest tests/test_producer.py -q -k observed) (✓ uv run pytest tests/test_producer.py -q -k observed passed)
- [x] 2.2 [medium] `Decision.observed` holds the term only when the value with it is below the value without it, and the no-dark-window, no-dark-time and no-cloud paths carry `None`; the producer then appends `Observed cloud above this hour's forecast: KBOS reported at least 62%, the forecast gave 20% low and mid cloud, a gap of 42 points. Confidence lowered.` straight after the observation line and before every equipment note, and no such line when the clamp holds the value or the confidence is fixed (design DD5, DD6) (verify: uv run pytest tests/test_producer.py -q -k observed) (✓ uv run pytest tests/test_producer.py -q -k observed passed)
- [x] 2.3 [easy] The existing observation tests still hold where the report does not lower confidence: the observation line follows the dew line and ends a gated overcast `NO-GO`; the old "observation changes no confidence" test becomes "changes no verdict, score, agreement or timeline", and `produce_verdict`'s docstring no longer says the observation changes no confidence (verify: uv run pytest tests/test_producer.py -q -k observation) (✓ uv run pytest tests/test_producer.py -q -k observation passed)

## 3. Docs and the gate [depends-on: 2]

- [ ] 3.1 [easy] The README's `metar_station` row says the observation lowers confidence when the report shows more cloud than this hour's low and mid cloud forecast, and that the check needs a cloud forecast with low and mid layers (the Open-Meteo providers, not NWS or 7Timer!); its `confidence` row says confidence also falls when the forecasts disagree or the airport reports more cloud than forecast (design DD7) (verify: uv run pytest tests/test_docs.py -q)
- [ ] 3.2 [easy] The whole project gate is green (verify: mise run check)

## Deviations Ledger

- 2.3: the old `test_an_observation_changes_no_decision_field` was removed, not
  renamed. Its report never lowered confidence, so it proved nothing new. Task
  2.1's test, now `test_an_observation_changes_no_verdict_score_agreement_or_timeline`,
  uses a report that does lower confidence and asserts the same four fields.
