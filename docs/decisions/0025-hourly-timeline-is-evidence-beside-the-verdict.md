---
id: adrs-adr0025
date: 2026-10-30
status: accepted
title: 'ADR0025: The verdict document carries a flat hourly timeline as evidence beside the verdict'
description: Architecture Decision Record for adding an hourly timeline of sky and weather to the verdict document as a flat, additive list computed in the core, delivered to Home Assistant one variable at a time, and never used as a verdict on later nights.
---

# ADR-0025: The verdict document carries a flat hourly timeline as evidence beside the verdict

## Context

PierPressure fetches hourly cloud cover, wind gust, seeing and transparency for
two to three days ahead, and computes the dark window and the moon for one
night. Until now the document published only the verdict and its summary
fields, so no dashboard could show the night as a strip of hours. The verdict
document is a frozen contract: existing fields never change meaning, and the
document may only grow. Every number in it comes from a pure, offline core, so
the same inputs give a byte-identical document. The verdict itself judges one
night, the rest of it once the night has started (ADR-0023). Home Assistant
drops state attributes over 16 KiB, and its MQTT integration has no weather
platform, so a forecast series can only reach a chart card as a sensor
attribute array.

## Decision

The verdict document gains a `timeline`: a list with one entry per clock hour
across the union of the hours the conditions sources returned, past hours
included, sorted ascending. Each entry is flat, with fixed keys: `time`,
`sun_altitude`, `moon_altitude`, `cloud_cover`, `cloud_low`, `cloud_mid`,
`cloud_high`, `wind_gust`, `seeing`, `transparency`. Weather values are carried
from each source's reading for the hour, null where a source lacks it. The sun
and moon altitudes are computed in the core from the pinned ephemeris. New
variables append as new flat keys.

The timeline is evidence beside the verdict. It changes no existing field, and
it carries no verdict of its own: the verdict still judges the one night the
dark window names, however far the timeline reaches.

The Verdict entity's attributes leave the timeline out. Home Assistant receives
the timeline one variable at a time, as an ordinary sensor per variable whose
attributes hold that variable's hourly array. No topic carries the whole
timeline.

## Consequences

- **Easier:** any chart card can draw a row of the night strip from one sensor's
  array, and later variables each add one sensor without touching the document's
  existing keys or the Verdict entity.
- **Easier:** a card can shade twilight by the sun's real altitude for each hour,
  rather than by clock time, because the altitude comes from the same offline
  astronomy as the dark window.
- **Easier:** the document stays byte-identical for the same inputs. The timeline
  is a pure function of the conditions value and the pier. Its altitudes and
  qualities are rounded at construction like every other computed field, and
  its cloud and wind values pass through exactly as the provider reported them.
- **Easier:** one name per value, from the core's hour records to the document
  and the sensors, so code, specs and dashboards agree without a mapping.
- **Harder:** the timeline carries hours after tonight, and a reader may be
  tempted to treat them as a forecast verdict. They are inputs, not a decision.
  An outlook verdict for later nights would be a separate decision.
- **Harder:** a consumer that wants the whole timeline must read every variable's
  sensor, or the document itself. The Verdict attributes are no longer the whole
  document.
- **Constraint accepted:** the entry's keys are now part of the frozen contract.
  Grouping them later would be a breaking change, so new variables only append.

## Alternatives Considered

### Alternative 1: Nested entries grouped by sky, cloud and weather
- **Pros**: reads well in a dump; related values sit together.
- **Cons**: every cloud value gets two names, one in the core's hour records and
  one in the document; chart templates reach two levels for each value; the
  grouping of variables that do not exist yet has to be decided now.
- **Why not**: the shape is visible to no dashboard, because cards read per-variable
  sensors, so the grouping buys readability for a document few people read and
  costs a mapping in every piece of code that touches it.

### Alternative 2: Keep the timeline inside the Verdict entity's attributes
- **Pros**: one entity holds everything; no new sensors.
- **Cons**: a 72-hour timeline pushes the attributes past the recorder's 16 KiB
  limit, so Home Assistant would drop every attribute of the Verdict entity,
  including the ones automations read today.
- **Why not**: it would break the entity that the product's core promise hangs on.

### Alternative 3: Also publish the whole timeline on its own retained MQTT topic
- **Pros**: a reader outside Home Assistant gets the whole timeline in one
  message, and the per-variable sensors still serve the cards.
- **Cons**: one more retained topic joins the frozen delivery surface for a
  reader that does not exist yet, and the message repeats what the sensors carry.
- **Why not**: the sensors are the route every known consumer uses, and the
  document itself remains the whole timeline's source. A whole-timeline topic
  can be added later without changing anything decided here, so there is no
  reason to freeze it now.

### Alternative 4: Limit the timeline to tonight's dark window
- **Pros**: smaller payloads; no hours a verdict does not judge.
- **Cons**: a dashboard could not show the coming evening in the afternoon, nor
  the hours around dusk and dawn that frame the night; the sources already
  returned the data.
- **Why not**: windowing is a presentation choice a card makes with the dark
  window's bounds, and the data is free. Dropping it in the core would be an
  irreversible loss for every consumer.
