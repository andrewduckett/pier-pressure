## Why

Dew on the optics ends an imaging session as surely as cloud, and the heater
decision is made at setup time. Every forecast already carries temperature and
dew point, so the verdict can say when the spread closes without any provider
work. This is a pure-core story from the multi-model epic (#153), which decided
that dew spread is a reason line only.

## What Changes

- The `reasons` list gains one line, `Dew likely from <time>.` or
  `Frost likely from <time>.`, naming the first scored hour whose spread
  between temperature and dew point falls under the pier's margin (D1, D4,
  D6, D7). The time is the document's UTC timestamp string (D1).
- The line appears only on a verdict whose gates passed, and sits last among
  the core's reasons, after the agreement line (D2, D3). No existing line
  moves.
- A pier gains an optional `dew_margin` setting in °C, default 4, zero turns
  the line off (D5). It is set in `config.yaml`, and through the add-on's
  `config.yaml` file; the add-on form does not change (D11).
- Nothing else changes: no gate, score, confidence, timeline variable or
  document field (D8, D9).

No breaking change. The verdict document grows by one reason string only.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: a new requirement that the reasons name the first dew or
  frost hour, and the pier tuning requirement widens from two knobs to three
  with `dew_margin`.

## Impact

- `pierpressure/core/config.py`: `PierConfig.dew_margin`.
- `pierpressure/core/scoring.py`: the dew line, appended in `evaluate` after
  the agreement line on a gate-passing verdict.
- `tests/test_scoring.py`, `tests/test_config.py`: unit tests; the test that
  says a scored verdict ends with the agreement line rewords (D3).
- `tests/test_golden_verdict.py` and `tests/fixtures/golden/`: two new
  stub-based cases, a dew night and a frost night (D10). Existing goldens are
  unchanged because the recorded payload carries no temperature.
- `README.md` and `ha-addon/DOCS.md`: document the setting.
- No new dependencies. No MQTT entity, topic or add-on schema change.
