## Why

With several Open-Meteo models in the provider list (#154), every cloud series that loses the fill is thrown away today, so the verdict is always one model's opinion and Andrew cannot tell a consensus from a lone forecast. Keeping those series as alternates and measuring their spread tells him how far to trust tonight's call before the rig goes out. This is the one Astrospheric Pro feature its API would not have sold us, and the reason epic #153 exists.

## What Changes

- The conditions snapshot keeps the series that lost the fill as alternates, beside the filled series, for every variable (D8). The fill itself is unchanged.
- The core measures cloud agreement over the scored window: per hour, the gap between the lowest and highest cloud any provider gave, counted only where two or more providers cover the hour, averaged with the clarity weight of the most optimistic reading (D1, D2), and banded agree, mixed, disagree (D3).
- The verdict document gains an additive top-level `agreement` object keyed by variable, always present and empty when fewer than two providers returned cloud (D4).
- Each timeline entry gains two additive keys, `cloud_cover_min` and `cloud_cover_max`, null for an hour fewer than two providers cover (D5).
- A reason line names the agreement on every verdict whose `agreement` is non-empty (D7).
- Confidence gains an agreement factor: agree leaves it alone, mixed cuts about a tenth, disagree about a third; it never changes a gate or the score (D6).
- A new decision record widens confidence's inputs from lead time and freshness to include agreement (D10).
- The delivery surface does not change: `agreement` reaches the Verdict entity's attributes through the existing rule that the payload carries every document key except `timeline` (D9). No new sensor.

Out of scope, per the story: agreement on gusts, NWS, drawing the band on the dashboard (#132), blending values.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conditions`: the snapshot keeps alternates beside the filled series; an alternate never fills an hour the filled series lacks.
- `night-verdict`: the document carries `agreement`; the timeline entry's fixed flat shape gains `cloud_cover_min` and `cloud_cover_max`; confidence falls with low agreement; the reasons name the agreement.

## Impact

- `pierpressure/core/conditions.py`: `Conditions` gains alternates, additively.
- `pierpressure/conditions/provider.py`: `assemble_snapshot` keeps losers instead of dropping them.
- `pierpressure/core/scoring.py`: the agreement measure, its bands and tuning constants, the confidence factor and the reason line.
- `pierpressure/core/model.py`: an `Agreement` object on `VerdictDocument`; two new `TimelineEntry` fields.
- `pierpressure/core/producer.py`: fills `agreement` and the per-hour band.
- `docs/decisions/`: one new ADR on confidence's inputs.
- Tests: `tests/test_conditions_provider.py`, scoring and producer tests, and the golden fixtures in `tests/fixtures/golden/`, which change for every expected document because the new keys are always present.
- No dependency, topic, entity or configuration changes. `openspec/prd.md` and the config context already describe confidence this way (#162).
