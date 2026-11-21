## REMOVED Requirements

### Requirement: The horizon mask has no consumer in the verdict document

**Reason**: Target ranking now uses the horizon mask, so a configured horizon changes the
`targets` list, and through the top pick the top-pick sentences in `reasons`. The
requirement's rule that the verdict document stays byte-identical and `targets` stays
empty no longer holds.
**Migration**: Rely on "The horizon mask changes only the targets and the top-pick
reasons" in this spec. It keeps the rule that the horizon adds, removes and reshapes
no field, topic or entity. Target ranking's rule for clearing the mask is "A target must
clear the horizon mask for the minimum duration" in the target-ranking spec.

## ADDED Requirements

### Requirement: The horizon mask changes only the targets and the top-pick reasons

A pier's horizon mask SHALL change only the verdict document's `targets` and, through
the top pick, the top-pick sentences in `reasons`: the framing sentence and the sentence
that calls the top pick bright. Every other field and every other reason SHALL be
identical to the verdict for the same pier, instant and conditions with no horizon. The
horizon SHALL NOT add, remove or reshape any field, topic or entity. Entities fed by
these two fields show their new values.

#### Scenario: A horizon that changes no top-pick sentence changes only the targets

- **WHEN** two verdicts are produced for the same pier, instant and conditions, one with no horizon and one with a horizon that hides a target listed in the verdict without it
- **AND** neither verdict's `reasons` holds a top-pick sentence
- **THEN** the two verdicts' `targets` lists differ
- **AND** every other field of the two verdicts is identical
