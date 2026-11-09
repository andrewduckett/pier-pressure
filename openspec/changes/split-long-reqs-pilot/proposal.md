## Why

One requirement in `pier-equipment` and one in `release-image` each bundle several behaviors in more than 500 characters (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This pilot is the smallest story in epic #230: it proves the split pattern before the large specs start.

## What Changes

- Split "Equipment is optional on each pier" into three requirements, one per behavior (D4).
- Split "A release proposes the add-on version update" into four requirements, one per behavior (D5).
- Each original is REMOVED and its parts ADDED under new headings, because OpenSpec rejects a REMOVE and an ADD of the same heading in one delta (D3).
- Every scenario moves word for word, and every SHALL keeps its meaning (D6, D7).
- Record the D3 finding in the epic #230 body, decision 5 (D9).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pier-equipment`: "Equipment is optional on each pier" becomes three requirements with the same meaning.
- `release-image`: "A release proposes the add-on version update" becomes four requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/pier-equipment/spec.md` and `openspec/specs/release-image/spec.md` after archive.
- No code in `tests/`, `pierpressure/`, `card/`, `docs/` or the README refers to a requirement by its heading, so nothing else changes.
- The epic #230 body gains the D3 finding.
