---
id: adrs-adr0022
date: 2026-10-12
status: accepted
title: 'ADR0022: The core is the only place that validates settings, whatever the interface'
description: Architecture Decision Record. The core validates every setting from every interface; an interface layer only reads, renames and combines settings.
---

# ADR-0022: The core is the only place that validates settings, whatever the interface

## Context

PierPressure is a Python service that publishes a nightly observing verdict to
Home Assistant over MQTT. Its core is a pure library with no Home Assistant
code. The core validates settings into one settings object. It skips a bad pier,
a single observing site, and logs why, rather than stopping.

Users can supply settings through more than one interface. Docker and source
installs use a YAML config file. Home Assistant add-on users fill in a
Configuration form. The add-on is a container that Home Assistant's Supervisor
runs. The Supervisor checks the form's values on save and writes them as JSON.
A layer outside the core then turns those values into the config file's shape
and combines them with the add-on's own config file.

That layer had grown checks of its own. For example, it rejected horizon points
that were not text or not valid YAML, and it explained this by saying it did not
rely on the Supervisor's check. So two places decided whether some settings were
valid. They could disagree, and an add-on user could get a different error from
a Docker user with the same mistake.

## Decision

The core is the only place that decides whether a setting's value is valid. This
holds for every interface.

An interface layer reads settings, renames them to the config file's names, and
combines its sources. For each setting it reads, it passes on any value it does
not expect, so the core can reject it. It ignores keys it does not read. It keeps only the checks it needs to run, such as "the saved values
are a mapping", and the rules about combining two sources, which only it has.

A check made before the core, such as the Supervisor's save check, is a
convenience for the user. Nothing depends on it.

## Consequences

- **Easier:** one rule. A bad value gets the same check from every interface,
  and an error that names the same setting.
- **Easier:** an interface layer stays small. A new interface needs no copy of
  the setting rules.
- **Easier:** the core's tests cover every setting rule once.
- **Harder:** an error names a setting by its config file name, such as
  `horizon.points`. An add-on user who typed into a differently named form field
  needs the add-on docs to link the two names.
- **Harder:** when an interface offers a setting in a form the core does not
  read, the core must learn to read it. For example, the core now accepts horizon
  points written as YAML text, because a form field can only hold text.
- **Harder:** a new interface could slip a check of its own back in. Reviewers
  need to apply this rule.

## Alternatives Considered

### Alternative 1: Each interface validates what it collects
- **Pros**: an interface can give errors in its own field names.
- **Cons**: each rule exists more than once, and the copies drift. Users of
  different installs get different errors for the same mistake.
- **Why not**: it breaks the promise that every install checks settings the
  same way.

### Alternative 2: Rely on the Supervisor's save check for the add-on
- **Pros**: the add-on layer needs no checks at all.
- **Cons**: values written another way, or by a future Supervisor, skip the
  check. The core would then run on values nobody checked.
- **Why not**: Home Assistant must never be load-bearing for correctness.

### Alternative 3: Teach the core each interface's field names
- **Pros**: errors could name the form field directly.
- **Cons**: the core would hold Home Assistant knowledge.
- **Why not**: the core must stay pure and testable without Home Assistant.
