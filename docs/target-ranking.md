# Target ranking: what to point at tonight

PierPressure answers two questions. The verdict answers "is tonight worth setting
up for?" Target ranking answers the second: "what should I point at from this
pier?" This page explains what the ranked targets are, how the ranking works, why
an object might be missing, and where the targets show up in Home Assistant.

## What the targets are

Each night, PierPressure ranks deep-sky objects — galaxies, nebulae, and star
clusters — from a catalog bundled with the app (OpenNGC). It keeps the objects
that are worth imaging and that clear your pier's horizon during astronomical
night, scores them, and publishes the best ten.

The ranked list travels inside the verdict document as the `targets` field, newest
verdict each time the core recomputes. Every target carries these fields:

- **`id`:** the object's catalog designation, such as `NGC0224`. Always present.
- **`name`:** the common name, such as "Andromeda Galaxy". Null when the catalog
  records none.
- **`type`:** the object type code, such as `G` (galaxy), `PN` (planetary
  nebula), or `OCl` (open cluster).
- **`score`:** the ranking score from 0 to 100. Higher is better placed tonight.
- **`window`:** the observable window — `start` and `end` times (UTC) when the
  object is above your horizon mask and the sky is astronomically dark.
- **`max_altitude`:** the highest the object climbs during that window, in degrees
  above the horizon.
- **`transit_time`:** when the object crosses your meridian — its highest point for
  the day. This can fall in daylight for an object that stays up all night, so it
  may sit outside the observable window.
- **`moon_separation`:** how far the object sits from the moon, in degrees,
  measured when the object is at its highest during the window.

The list is ordered by score, highest first. Ties break by `id`, so the same night
always produces the same order. When no object is rankable, the list is empty
rather than missing, so its shape never changes.

## How the ranking works

PierPressure scores each target on four factors, then combines them into the 0-to-100
score. All four reward what makes an object easy to image well tonight:

- **Altitude:** how high the object climbs. Higher objects shine through less air,
  so a target that reaches the top of the sky beats one that only skims the
  horizon.
- **Window length:** how long the object stays observable during the dark window.
  Longer is better — more time to collect light.
- **Moon separation:** how far the object sits from the moon while it is up and
  lit. Farther is better. This factor is neutral on a new moon or when the moon is
  below the horizon, because then the moon does no harm.
- **Transit timing:** whether the object peaks near the middle of its observable
  window. A target that peaks mid-window gives you its best view during the dark
  hours.

Altitude carries the most weight, then window length, then moon separation, then
transit timing. These weights are fixed in the app version, so the ranking is the
same for everyone running that version and does not drift between runs.

Brightness is **not** a ranking factor yet. A fainter but better-placed object can
outrank a famous bright one, because equipment and field-of-view fit arrive in a
later milestone. Until then, the ranking answers "what is best placed tonight?",
not "what is easiest to see in a small scope?"

## Why an object might be missing

An object you expected can be absent for three plain reasons:

- **Too faint:** the app drops objects fainter than a set magnitude limit before
  ranking. Objects with no recorded brightness are kept, so real objects are not
  lost to missing data.
- **Never clears your horizon:** if the object stays below your horizon mask all
  night — behind a hill, a building, or simply too far south for your latitude — it
  cannot be observed, so it is left out.
- **Up too briefly:** if the object is above your horizon for less than the minimum
  observing window, it is dropped rather than listed with a low score. A target you
  can only catch for a few minutes is not worth setting up for.

The list is also capped at ten, so a well-placed object can rank just outside the
top ten on a night crowded with good targets.

## Where the targets appear in Home Assistant

PierPressure publishes a **Top target** sensor for each pier over MQTT discovery,
alongside the existing verdict, score, and refresh entities:

- **State:** the top-ranked target's name, or its catalog `id` when it has no
  common name.
- **Attributes:** the full ordered list of targets and the top target's fields, as
  a JSON attributes payload. A dashboard card can read the list from there.
- **Unavailable when empty:** when no target is rankable — for example, a night
  with no dark window — the sensor shows as unavailable rather than a blank or
  placeholder value.

The sensor is additive. Your existing verdict, score, and refresh entities keep
their topics and identities unchanged.
