---
id: adrs-adr0020
date: 2026-10-10
status: accepted
title: 'ADR0020: The add-on is set up on a form, and the form is translated into the config file''s shape'
description: Architecture Decision Record for how Home Assistant add-on users configure PierPressure. The add-on declares a Configuration form, and the service turns the saved values into the same settings a config file produces, outside the pure core.
---

# ADR-0020: The add-on is set up on a form, and the form is translated into the config file's shape

## Context

PierPressure is a Python service that publishes a nightly observing verdict to
Home Assistant over MQTT. Users on Home Assistant OS run it as an add-on. An
add-on is a container that Home Assistant's Supervisor installs and runs. Docker
users run the same container image with a YAML config file.

Until now, the add-on read only that YAML file from its own folder. Home
Assistant has no file editor of its own. So an add-on user had to install a
second add-on only to write the file.

An add-on can declare a form instead. Home Assistant shows it on the add-on's
Configuration tab, checks the values on save, and writes them into the container
as a JSON file. The form allows only two levels of nesting, so some settings,
such as a list of horizon points or an uploaded horizon file, do not fit it.

The service's core is a pure library with no Home Assistant code. It validates
config into one settings object, and it skips a bad pier rather than stopping.

## Decision

The add-on declares a Configuration form for the settings that fit typed fields.
Inside an add-on, the service reads the form's saved values at startup. Code
outside the core turns them into the same mapping a config file with those
settings would hold. The core then validates that mapping exactly as it validates
a file.

Form field names follow the config file's key names wherever the nesting limit
allows. The config file stays available to add-on users for settings the form
cannot hold. Outside an add-on, the service never reads the form.

## Consequences

- **Easier:** an add-on user can reach a first verdict using only the Home
  Assistant UI.
- **Easier:** one validation path. A pier from the form gets the same checks and
  error messages as a pier from a file.
- **Easier:** the core stays free of Home Assistant code. Only the translating
  module knows the form's field names.
- **Easier:** the Supervisor checks types and ranges when the user saves, so many
  mistakes show in the form before the service starts.
- **Harder:** each new setting that suits the form needs three edits: the form's
  schema, its label, and the translation step.
- **Harder:** add-on users have two places to configure. The service needs a
  clear rule, and clear errors, for settings that appear in both.
- **Harder:** removing the form later would strand users whose settings live
  only in it.

## Alternatives Considered

### Alternative 1: Keep the config file as the only source
- **Pros**: the add-on stays packaging only, with one source of settings.
- **Cons**: every add-on user installs a second add-on to write one file, and
  types a broker password into plain text.
- **Why not**: it blocks the simplest setup Home Assistant users expect.

### Alternative 2: One text field on the form that holds the whole YAML config
- **Pros**: the smallest change, and every setting fits.
- **Cons**: the field is awkward to edit, Home Assistant cannot check its
  content, and errors show only in the log.
- **Why not**: it moves the file into a text box without the benefits of a form.

### Alternative 3: A sidebar web page with its own YAML editor
- **Pros**: every setting fits, with room for richer help.
- **Cons**: PierPressure would serve a web page, which is new product surface to
  build, secure and maintain.
- **Why not**: the cost is far larger than the gain for a handful of settings.

### Alternative 4: Teach the core the form's field names
- **Pros**: no translating module.
- **Cons**: the core would hold Home Assistant knowledge, and the form's names
  could drift from the file's names in the core itself.
- **Why not**: the core must stay pure and testable without Home Assistant.
