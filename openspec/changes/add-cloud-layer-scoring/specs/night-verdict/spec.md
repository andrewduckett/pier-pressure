## ADDED Requirements

### Requirement: High, thin cloud is a distinct score penalty

When every hard gate passes and cloud data is available, the banded score SHALL
apply a penalty for high-layer (thin cirrus) cloud across the dark window that is
distinct from the total-cloud term of the score. High cirrus can leave a low
total cloud reading yet wreck transparency for deep-sky work, so the night is
scored honestly rather than as clear. The high-cloud penalty SHALL be reported as
its own itemized `reasons[]` line, separate from the total-cloud reason, so the
explanation names it as a distinct term. Holding every other input fixed —
including the total cloud cover — more high-layer cloud usably up during the dark
window SHALL NOT raise the score: it lowers it or leaves it unchanged.

The high-cloud penalty SHALL only shape the banded score; it SHALL NOT introduce
a new hard gate and SHALL NOT on its own cause a `NO-GO`. It SHALL be weighted
toward the usably clear hours in the same way as the other non-cloud terms, so a
high-cirrus reading during a clouded-out hour does not distort the verdict. When
the high-layer cloud component is unavailable for the dark window, the high-cloud
term SHALL drop its own contribution — no penalty and no reason line — rather than
fail or guess, exactly as the other optional terms degrade when their data is
missing. This term is additive: it does not change the meaning of the existing
total-cloud term, the gates, the bands, or the confidence.

#### Scenario: High cirrus lowers the score with its own reason

- **WHEN** two nights are identical, each with cloud data available and every hard gate passing, except that one has high, thin cloud usably up during the dark window and the other has none
- **THEN** the night with the high cirrus has the lower score
- **AND** its `reasons` list carries a high/thin-cloud line distinct from the total-cloud line

#### Scenario: The high-cloud penalty never gates the night

- **WHEN** a night has high, thin cloud during the dark window while every hard gate passes
- **THEN** the `verdict` is not `NO-GO` on account of the high cloud
- **AND** the `score` is a non-null integer between 0 and 100 inclusive

#### Scenario: Missing high-cloud component drops the term without penalty

- **WHEN** two nights are identical and every hard gate passes, except that one has its high-layer cloud component available and clear and the other has that component unavailable while total cloud cover is available
- **THEN** neither night is penalized for high cloud
- **AND** neither `reasons` list carries a high/thin-cloud line
