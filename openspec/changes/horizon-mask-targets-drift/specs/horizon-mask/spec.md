## REMOVED Requirements

### Requirement: The horizon mask has no consumer in the verdict document

**Reason**: Target ranking now uses the horizon mask, so a configured horizon changes the
`targets` list. The requirement's rule that the verdict document stays byte-identical and
`targets` stays empty no longer holds.
**Migration**: Rely on "The horizon mask changes only the targets in the verdict
document" in this spec. It keeps the rule that the horizon adds, removes and reshapes
no field, topic or entity. Target ranking's rule for clearing the mask is "A target must
clear the horizon mask for the minimum duration" in the target-ranking spec.

## ADDED Requirements

### Requirement: The horizon mask changes only the targets in the verdict document

A pier's horizon mask SHALL change only the `targets` field of the verdict document.
A verdict for a pier with a horizon configured SHALL be byte-identical, in every field
except `targets`, to the one for the same pier, instant and conditions with no horizon.
The horizon SHALL add, remove and reshape no field, topic or entity. Entities that
display `targets` show the changed list.

#### Scenario: A horizon that hides a target changes only the targets

- **WHEN** two verdicts are produced for the same pier, instant and conditions, one with no horizon and one with a horizon that hides a target listed in the verdict without it
- **THEN** the two verdict documents' `targets` lists differ
- **AND** every other field of the two verdict documents is byte-identical
