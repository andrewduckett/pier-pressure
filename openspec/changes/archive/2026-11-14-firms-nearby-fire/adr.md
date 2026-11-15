# ADR Review Manifest

- Status: completed
- Review date: 2026-11-14

## Review Summary

ADR review completed for this change. Of design.md's decisions, only DD5 passes
the test. Someone reading the code could remove the log filter as redundant with
the safe call-site logging. That would leak the key on every successful fetch,
through httpx's own request line. DD1 follows ADR-0037 and the glossary's
"fire detection" entry. DD2 to DD4 and DD6 to DD8 follow existing patterns or
can be read from the code.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md): the core emits one JSON document; this change adds no key to it.
- [ADR-0005](../../../docs/decisions/0005-conditions-provider-edge-seam.md): the fire detections are fetched at the provider edge, before the core runs.
- [ADR-0015](../../../docs/decisions/0015-provider-health-beside-verdict-in-memory.md): FIRMS health travels beside the verdict, in memory.
- [ADR-0020](../../../docs/decisions/0020-addon-form-translated-to-config-file-shape.md), [ADR-0021](../../../docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md), [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the `firms` block comes from the add-on's config file and is validated only by the core.
- [ADR-0027](../../../docs/decisions/0027-conditions-filled-per-variable-from-an-ordered-provider-list.md), [ADR-0031](../../../docs/decisions/0031-computed-variables-are-a-source-in-the-provider-order.md): FIRMS is not in the provider order and fills no variable.
- [ADR-0037](../../../docs/decisions/0037-observations-are-a-core-input-beside-the-conditions.md): fire detections enter the core as a separate plain input beside the conditions, in the same way (design DD1, DD2).
- [ADR-0038](../../../docs/decisions/0038-an-observation-only-lowers-confidence.md): fire detections touch no gate, score or confidence, so the observation factor is unchanged.
- Every other record in `docs/decisions/` (ADR-0002 to ADR-0004, ADR-0006 to ADR-0014, ADR-0016 to ADR-0019, ADR-0023 to ADR-0026, ADR-0028 to ADR-0030, ADR-0032 to ADR-0036) was read and is not affected.

## New Durable ADRs Created

- [ADR-0039](../../../docs/decisions/0039-a-key-in-a-url-is-masked-in-every-log-record.md): a key that travels in a request URL is masked in every log record (design DD5).
