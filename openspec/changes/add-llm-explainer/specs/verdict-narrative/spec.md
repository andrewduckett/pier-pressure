## Purpose

The verdict-narrative capability turns an already-computed verdict into a short
prose explanation, so a reader gets the go/no-go answer and the top targets as
plain sentences instead of only itemized terms. It is optional, never feeds the
astronomy or scoring math, and the system stays fully correct without it.

## ADDED Requirements

### Requirement: Narrative explains an already-computed verdict

The explainer SHALL take an already-produced verdict document as its sole input
and produce a short prose narrative of that verdict. It SHALL NOT compute,
re-derive, or alter the verdict, score, confidence, reasons, or targets. The
narrative is derived only from the terms present in the document, so it explains
what the core decided rather than deciding anything itself.

Whether the resulting prose reads as a faithful, plain-language summary of the
verdict is confirmed by a documented manual acceptance check, because it depends
on generated language that PierPressure does not assert mechanically.

#### Scenario: Explainer consumes the verdict document

- **WHEN** the explainer is given a verdict document and asked to explain it
- **THEN** its only input is that document (verdict, score, confidence, reasons, and targets)
- **AND** it returns prose text without reading any astronomy, conditions, or ranking source

#### Scenario: Explaining never alters the numbers

- **WHEN** a verdict is explained
- **THEN** the verdict document delivered downstream is byte-identical to the document produced without the explainer
- **AND** the verdict, score, confidence, reasons, and targets are unchanged

### Requirement: The narrative is delivered separately from the verdict document

The narrative SHALL be delivered as text alongside the verdict, not as a field of
the verdict document. The verdict document remains the numbers-only contract, and
the LLM output is never merged into it or read back into any decision.

#### Scenario: Narrative is not part of the verdict document

- **WHEN** a narrative is produced for a verdict
- **THEN** the verdict document contains no narrative field
- **AND** the narrative text is delivered on its own surface

### Requirement: The explainer is optional and disabled by default

The explainer SHALL be disabled by default and enabled only through explicit
configuration. When it is disabled or not configured, the system SHALL deliver the
verdict exactly as it does without the explainer and SHALL produce no narrative.

#### Scenario: Disabled explainer produces no narrative

- **WHEN** the explainer is disabled or unconfigured and a verdict is produced
- **THEN** the verdict is delivered as usual
- **AND** no narrative is produced

### Requirement: The explainer degrades gracefully on failure

When the explainer is enabled but the provider call fails, times out, or returns
nothing usable, the explainer SHALL produce no narrative text for that recompute
(it yields none). The system SHALL still deliver the verdict, and the narrative
entity SHALL resolve to unavailable rather than retaining earlier prose (spec
ha-delivery) — this is an active unavailable publish, never a skipped one that
would leave stale text shown as current. The failure SHALL be reported through
logging and SHALL NOT raise into the recompute loop or delay or corrupt delivery of
the verdict.

#### Scenario: Provider failure does not block the verdict

- **WHEN** the explainer is enabled and the provider call fails
- **THEN** the verdict is still delivered
- **AND** the explainer produces no narrative text, and the narrative entity resolves to unavailable
- **AND** the failure is reported without aborting the recompute

### Requirement: Narratives are cached on the deterministic verdict terms

The explainer SHALL cache a produced narrative keyed on every verdict term that
influences the narrative — the verdict value, the score, the confidence, the
reasons, and the emitted fields of the targets included in the explanation (not
merely their identities). When a later recompute yields identical influencing
terms, the explainer SHALL reuse the cached narrative rather than issue a new
provider call. When any influencing term differs, it SHALL produce a fresh
narrative. The cache SHALL NOT serve a narrative when any term it explained has
changed, so a later night can never show an earlier night's prose.

#### Scenario: Identical influencing terms reuse the cached narrative

- **WHEN** two recomputes yield verdicts identical in verdict, score, confidence, reasons, and every emitted target field
- **THEN** the explainer issues a provider call for the first
- **AND** the second reuses the cached narrative without a new provider call

#### Scenario: A changed target field produces a fresh narrative

- **WHEN** a later recompute yields the same target identities but a changed target field, such as a new transit time or maximum altitude, or a changed confidence band
- **THEN** the explainer issues a new provider call rather than reusing the cached narrative

### Requirement: The explainer sits behind a provider interface

The explainer SHALL obtain prose through a provider interface so the provider is
swappable and can be replaced by a test double. The default provider SHALL use an
LLM service and SHALL be the only component permitted to make a network call; no
other part of the explainer or core reaches the network. Selecting or omitting a
provider SHALL NOT change the verdict document.

#### Scenario: A test double replaces the LLM provider

- **WHEN** the explainer is configured with a non-LLM provider double
- **THEN** it produces narratives through that double with no network call
- **AND** the verdict document is unchanged by the choice of provider
