---
id: adrs-adr0026
date: 2026-11-14
status: accepted
title: 'ADR0026: A pier''s form fields stay in one flat list, and each label names its section'
description: Architecture Decision Record for keeping a pier's fields on the add-on Configuration form flat, although Home Assistant now allows nested blocks, and for showing the pier's sections through label prefixes and help text alone.
---

# ADR-0026: A pier's form fields stay in one flat list, and each label names its section

## Context

Home Assistant users set PierPressure up on the add-on's Configuration form. The
service translates the saved values into the config file's shape (ADR-0020).
Piers are a list, so each pier opens in a dialog of 13 fields. The fields fall
into four topics: location, horizon, equipment, and the rules that decide `GO`
or `NO-GO`.

ADR-0020 kept the fields flat because the form allowed only two levels of
nesting. That limit is gone. Since September 2025, the Supervisor accepts and
describes blocks nested to any depth. So the old reason no longer stops anyone
from nesting each pier's fields into groups.

Two facts about the form shape this decision. Inside a pier's dialog, the
frontend draws a nested block as a row with an edit button, which opens a
dialog of its own. And the Supervisor requires every nested block to be present
when the user saves, because a block cannot be marked optional.

Three layouts were tried in real Home Assistant: the flat list, one group per
topic, and the flat list with each label naming its section.

## Decision

A pier's fields stay in one flat list, with the same names, order and types as
before. Each field's label starts with its section's name, such as
`Horizon: floor`. The first field of each section opens its help text with a
sentence that introduces the section. Nothing but the labels and help text
shows the sections.

## Consequences

- **Easier:** saved settings, the translation step and the service are
  unchanged. A pier saves with only its required fields filled in.
- **Easier:** each section is visible inside the one dialog, with no extra click
  to reach it.
- **Harder:** the sections are only text. A new pier field needs its section in
  its label, and a test checks that every field has one.
- **Harder:** the dialog is still one long list, and its labels are longer.
- **Harder:** nesting later would change every saved pier and the translation
  step, and users would re-enter their piers.

## Alternatives Considered

### Alternative 1: Nest each pier's fields into four groups
- **Pros**: the form's names match the config file's `horizon` and `equipment`
  blocks, and each group can carry its own introduction.
- **Cons**: each group is a row that opens another dialog, so a pier's first
  view shows rows, not fields. A new pier may not save until every group,
  including the optional ones, has been opened.
- **Why not**: in the trial its first view read worse than the flat list, and
  every pier would take more clicks.

### Alternative 2: Keep the flat list with unchanged labels
- **Pros**: no change at all.
- **Cons**: 13 fields with nothing to show where one topic ends and the next
  begins.
- **Why not**: the trial found it hard to read for exactly that reason.

### Alternative 3: Add a fake heading field before each section
- **Pros**: looks most like a real heading.
- **Cons**: the form has no heading type, so it would be a toggle or a text box.
  People can click or type in it, the Supervisor saves it, and the service would
  have to throw it away.
- **Why not**: it is a control that pretends not to be one.
