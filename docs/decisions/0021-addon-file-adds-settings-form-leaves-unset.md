---
id: adrs-adr0021
date: 2026-10-12
status: accepted
title: 'ADR0021: Inside an add-on, the config file adds the settings the form leaves unset'
description: Architecture Decision Record for how a Home Assistant add-on combines its Configuration form with its config file. The file adds settings the form leaves unset, and a setting given in both is a startup error.
---

# ADR-0021: Inside an add-on, the config file adds the settings the form leaves unset

## Context

PierPressure is a Python service that publishes a nightly observing verdict to
Home Assistant over MQTT. Users on Home Assistant OS run it as an add-on. An
add-on is a container that Home Assistant's Supervisor installs and runs.

An add-on user has two places to put settings. The first is the add-on's
Configuration form, which Home Assistant shows and checks. The second is a YAML
config file in the add-on's own folder, in the same format Docker users write.
Some settings cannot go on the form. A form cannot upload a file, so an exported
horizon file can only be named in the config file. Other settings are simply not
on the form yet.

Until now, the service used one place or the other. When the form listed a pier,
the service ignored the file. A user who needed a horizon file had to give up the
form and list every pier in the file.

The service needs a rule for using both places at once. The rule must be easy to
explain, and a mistake must never pass silently.

## Decision

Inside an add-on, the config file adds only settings the form leaves unset. This
includes optional settings the form shows but the user left empty, such as a
pier's horizon. A file pier adds its settings to the form pier
with the same id. The file cannot add a pier of its own.

A setting given in both places stops the add-on at startup, with an error that
names the setting and the pier. A file pier that the form does not list stops it
too. Some settings only make sense from one source, so they count as one
setting: a pier's horizon, a pier's equipment, and the broker connection (host,
port, username and password).

The form must list at least one pier. The file can no longer set up the add-on on
its own. Outside an add-on, the service reads the config file alone, as before.

## Consequences

- **Easier:** a user keeps the form for everyday settings, and puts a horizon
  file, or any setting the form lacks, in the config file.
- **Easier:** a new form field needs no new rule. Once the user fills it in,
  giving the same setting in the file becomes an error by itself.
- **Easier:** a mistake is loud. A user who sets a value in both places learns
  at startup, not by noticing that one value was quietly ignored.
- **Easier:** the broker connection still comes from one source, so a password
  never pairs with a host from somewhere else.
- **Harder:** a user who wrote a full config file must move its piers onto the
  form. The startup error names those piers and says what to move.
- **Harder:** a value the user already set on the form cannot be overridden from
  the file. The user must clear the form field first.
- **Harder:** the service needs a combine step and clear errors for both
  sources, with tests for each conflict.

## Alternatives Considered

### Alternative 1: Keep one source at a time
- **Pros**: the simplest rule, with nothing to combine and no conflicts.
- **Cons**: a user who needs one file-only setting must give up the form
  completely.
- **Why not**: it keeps the problem this decision exists to solve.

### Alternative 2: Let one source silently win
- **Pros**: no startup errors. Either the form or the file overrides the other.
- **Cons**: a user who edits the losing place sees no effect and gets no
  warning. Users would need to remember which source wins.
- **Why not**: a quietly ignored setting is harder to debug than a clear error
  at startup.

### Alternative 3: Let the file add only horizon files
- **Pros**: the smallest surface. The file holds exactly what the form cannot.
- **Cons**: settings that are not on the form yet, such as score thresholds and
  topic names, would have no place at all. Each new file-only setting would need
  its own exception.
- **Why not**: it takes features away from add-on users until the form catches
  up, and some settings may never join the form.

### Alternative 4: Merge each key on its own
- **Pros**: the most freedom. Any key can come from either place.
- **Cons**: a horizon floor from the form and a horizon file from the config
  file would combine into one horizon with two sources. A broker host from one
  place could pair with a password from the other.
- **Why not**: some settings only work as a whole, and a key-by-key merge
  builds combinations that the service would reject with a confusing error, or
  worse, accept.
