---
id: adrs-adr0041
date: 2026-11-15
status: accepted
title: 'ADR0041: Settings YAML keeps YAML 1.1 rules, except that padded integers are decimal and base-60 values are text'
description: Architecture Decision Record. The core reads settings YAML with PyYAML's safe loader and changes only two number forms, rather than adopting the YAML 1.2 rules or another YAML library.
---

# ADR-0041: Settings YAML keeps YAML 1.1 rules, except that padded integers are decimal and base-60 values are text

## Context

PierPressure's core reads its settings from YAML: the whole config file, and
horizon points written as text, such as the add-on form's horizon points field.
Both are read with PyYAML's safe loader, which follows YAML 1.1. YAML 1.1 reads
`045` as the octal number 37 and `1:30` as the base-60 number 90. Users copy
horizon azimuths from tables that pad them with zeros, so the core loaded wrong
horizons and logged nothing.

The value is wrong as soon as it is parsed: `045` and `37` are the same integer
afterwards. So the fix has to be in the reader. YAML 1.2 fixes both forms, but it
also changes others that users may rely on, such as `yes` and `no` read as true
and false, and whether `08` is a number or text.

## Decision

The core keeps PyYAML's safe loader and its YAML 1.1 patterns. It changes only
two constructors. An integer written with leading zeros, such as `045`, is read
as a decimal number. A value written as numbers joined by colons, such as `1:30`,
is read as the text written. Every place the core reads settings YAML uses this
one reader.

## Consequences

- A padded number means what the user wrote, in the config file and on the
  add-on form alike.
- A base-60 value in a number setting is now rejected by the settings check
  rather than loaded as a different number.
- Every other value reads exactly as before, so no setting that relies on YAML
  1.1, such as `enabled: yes` or `id: 08`, changes.
- The rules are PierPressure's own: neither plain YAML 1.1 nor YAML 1.2. A
  reader who knows YAML has to learn two exceptions, so the user docs state them.
- Swapping the reader for `yaml.safe_load` or another YAML library would bring
  the octal and base-60 readings back, or change other values. Tests pin both
  exceptions and the forms that stay unchanged.

## Alternatives Considered

### Alternative 1: Adopt the YAML 1.2 core schema in PyYAML

- **Pros**: A published standard; `045` is 45 and `1:30` is text there too.
- **Cons**: It also changes booleans, `0o` octal, underscores in numbers and
  whether `08` is a number.
- **Why not**: Each of those changes what an existing config file means, and
  no user asked for them.

### Alternative 2: Switch to a YAML 1.2 library, such as ruamel.yaml

- **Pros**: The library maintains the YAML 1.2 rules.
- **Cons**: A new runtime dependency, with the same wider changes as
  Alternative 1, and its own differences from PyYAML in error text and types.
- **Why not**: It adds a dependency and a migration to fix two number forms.

### Alternative 3: Reject padded and base-60 numbers

- **Pros**: No guess about what the user meant.
- **Cons**: Padded tables are common, and a padded integer has one plain
  meaning to the person who typed it.
- **Why not**: It turns a common, clear input into an error the user must fix
  by hand.
