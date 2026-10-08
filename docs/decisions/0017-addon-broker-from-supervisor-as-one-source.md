---
id: adrs-adr0017
date: 2026-10-06
status: accepted
title: 'ADR0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix'
description: Architecture Decision Record for how the Home Assistant add-on finds its MQTT broker. The service asks the Supervisor only when the config file names no broker host, and takes all connection settings from one source.
---

# ADR-0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix

## Context

PierPressure is a Python service that publishes an observing verdict to Home
Assistant through an MQTT broker. Users on Home Assistant OS run it as an add-on.
An add-on is a container that Home Assistant's Supervisor installs and runs.
Docker users run the same container image outside Home Assistant.

Most add-on users also run the Mosquitto broker add-on. The Supervisor holds that
broker's host, port, username and password. It hands them to any add-on that
declares it wants the `mqtt` service. The password is one that Mosquitto created
for add-ons. Until now, PierPressure read its broker only from its own config
file, so users copied these settings into the file by hand.

The service needs a rule for when the file and the Supervisor both have broker
settings. The connection settings are the host, port, username and password. A
user can point the file at a different broker, and leave out a password because
that broker needs none.

## Decision

Inside an add-on, the service takes all four connection settings from one source.
If the config file names a broker host, all four come from the file, and the
service never asks the Supervisor. If the file names no host, all four come from
the Supervisor. A file that sets a port, username or password without a host is
an error.

Outside an add-on, nothing changes: the file must name a host. The service tells
the two cases apart by the token that the Supervisor gives only to add-ons.

## Consequences

- **Easier:** a Mosquitto user writes a config file with no broker settings.
- **Easier:** the Supervisor's credentials only ever go to the broker that issued
  them. A broker the user chose never receives them.
- **Easier:** existing config files keep working, because a file that names a host
  behaves as before.
- **Harder:** a user who names the Mosquitto host in the file must also copy its
  credentials. The add-on documentation tells them to leave the host out instead.
- **Harder:** the add-on is no longer packaging only. The image now has one
  behaviour that runs only inside an add-on, and tests must cover both cases.

## Alternatives Considered

### Alternative 1: Fill each missing setting from the Supervisor
- **Pros**: the user can set any mix, such as only the host, and the Supervisor
  fills in the rest.
- **Cons**: a user who points the host at another broker and leaves out the
  password gets the Supervisor's password. The service then sends Mosquitto's
  credentials to a broker that never issued them.
- **Why not**: leaking a credential to a third party is worse than asking a user to
  copy two settings.

### Alternative 2: Any `mqtt:` block in the file turns the lookup off
- **Pros**: the simplest rule to explain.
- **Cons**: a user cannot change only the topic names and still use the
  Supervisor's broker.
- **Why not**: the topic names are not connection settings. Tying them to the
  broker's source takes away a choice for no safety gain.

### Alternative 3: Keep the add-on packaging only, and leave the broker in the file
- **Pros**: the image has no add-on-specific behaviour.
- **Cons**: every Mosquitto user copies a host and a password into a plain-text
  file by hand.
- **Why not**: using the Supervisor's broker is the setup Home Assistant users
  expect from an add-on, and it keeps a password out of the file.
