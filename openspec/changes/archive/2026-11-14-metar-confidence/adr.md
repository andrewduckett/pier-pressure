# ADR Review Manifest

- Status: completed
- Review date: 2026-11-14

## Review Summary

ADR review completed for this change. The rule behind brainstorm D4 and D9, that
the observation only lowers confidence and never touches a gate or the score,
passes the test. Someone could plausibly make a cloudy report a gate, or let a
clear report raise confidence, without knowing why the station's 12,000 ft view
rules both out. Design DD1 to DD7 are recoverable from code or follow existing
records.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the document's shape does not change; only confidence values do.
- [ADR-0002](../../../docs/decisions/0002-gates-then-banded-score.md): the gates and the score are unchanged.
- [ADR-0029](../../../docs/decisions/0029-forecast-agreement-is-a-confidence-input.md): agreement is a confidence input; the new factor follows its pattern and multiplies with it.
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md): the factor reads the filled cloud bundle, never an alternate.
- [ADR-0037](../../../docs/decisions/0037-observations-are-a-core-input-beside-the-conditions.md): the observation stays an input beside the conditions; this change gives it its first effect.
- Every other record in `docs/decisions/` (ADR-0003 to ADR-0005, ADR-0007 to ADR-0025, ADR-0028, ADR-0030 to ADR-0036; ADR-0006 and ADR-0026 are superseded) was read and is not affected.

## New Durable ADRs Created

- [ADR-0038](../../../docs/decisions/0038-an-observation-only-lowers-confidence.md): an observation can only lower confidence, never raise it or change a gate or the score (brainstorm D4, D9).
