# ADR Review Manifest

- Status: completed
- Review date: 2026-09-10

## Review Summary

ADR review completed for this change. Every decision in `design.md` was tested
against the bar — hard to reverse, surprising without context, and the result of
a real trade-off. None clears it: the change adds cloud-layer detail additively
within already-recorded architecture, so no new repository-level ADR was created.

The load-bearing decision (score high, thin cloud as a distinct multiplicative
penalty — design D2) applies the pattern **ADR-0002** already records — hard gates
then a banded score cut by penalty terms — with the existing moon penalty as its
direct precedent. It does not change the verdict contract (no new document field;
the term surfaces only as a `reasons[]` line), and reversing it is a reviewed
scoring-constant diff plus a one-time golden re-base, not a hard-to-reverse
commitment. The model extension (carry low/mid/high on `BaseHour` — design D1)
follows **ADR-0006**'s per-source group model additively, honouring the frozen,
additive-only contract constraint.

## In-Force ADRs Reviewed

- ADR-0001 — Home-Assistant-agnostic core with a JSON verdict contract delivered
  via a dumb adapter. Bounds this change to additive, contract-preserving edits.
- ADR-0002 — Night verdict uses hard gates then a banded score, not a single
  weighted average. Governs the new penalty term; the high-cloud penalty follows
  the moon-penalty precedent this ADR records.
- ADR-0003 — Target observability is hard-clamped to astronomical night. Untouched
  by this change.
- ADR-0004 — Deterministic offline astronomy via Skyfield with a pinned ephemeris.
  Untouched; the new term is pure math over existing inputs.
- ADR-0005 — Weather enters at a provider edge; the core takes a conditions
  snapshot. The Open-Meteo component fetch and parser change stay behind this seam.
- ADR-0006 — The conditions snapshot is modelled as per-source groups. The
  `BaseHour` component split extends this model additively.

None of the in-force ADRs are superseded by this change.

## New Durable ADRs Created

- None — no major durable architectural decisions were introduced. The change is
  an additive extension governed by ADR-0002 (banded score with penalty terms) and
  ADR-0006 (per-source group model), so no new repository-level ADR file was
  created.
