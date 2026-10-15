---
id: adrs-adr0023
date: 2026-10-14
status: accepted
title: 'ADR0023: Once the night has started, the verdict judges the rest of it'
description: Architecture Decision Record. After astronomical dusk, the gates and the score cover the span from now to dawn, while the dark-window field keeps the whole night.
---

# ADR-0023: Once the night has started, the verdict judges the rest of it

## Context

PierPressure recomputes each pier's night verdict on a schedule and on demand,
so the question "is tonight worth setting up for?" is asked again and again
through the evening and the night.

The verdict judges a night by its usable dark time, over the dark window from
astronomical dusk to astronomical dawn. Until now, every rule read the whole
window, whatever the time of the question. At 22:00, a clear spell that ended
at 21:00 still counted as usable time, and a gust that blew at 20:00 still
failed the wind gate. The answer described a night that was partly over.

The dark-window field in the verdict document is a frozen contract. The moon's
rise and set and the target list also describe the whole night.

## Decision

Once the evaluation instant is past astronomical dusk, the verdict judges the
scored window: the span from that instant to astronomical dawn. The overcast
gate, the wind gate, the score, and the completeness part of confidence all
read this span. Before dusk, the scored window is the whole dark window, so a
verdict asked in the afternoon is unchanged.

The dark-window field keeps the whole night. The document gains a separate
scored-window field that reports the span judged.

## Consequences

- **Easier:** a mid-session verdict is honest. The score falls as clear hours
  pass, and a gust or a gap that is behind the observer no longer gates or
  caps the night. The refresh button answers "is the rest of tonight worth
  it", which is the question a person asks at 22:00.
- **Easier:** the rule is one clamp at the one place that decides the verdict.
  Every condition rule already takes a window, so none of them changes.
- **Harder:** the score now moves through the night, so a Home Assistant
  automation that triggers on a threshold can fire more than once. Users who
  want one decision per night should act on the first verdict after dusk.
- **Constraint accepted:** the target list still judges the whole night, so
  mid-session the verdict and the targets describe different spans. Ranking
  the rest of the night is a separate change.
- **Constraint accepted:** a verdict asked in the last partial second before
  dawn has an empty scored window. It reports that no dark time remains rather
  than failing a gate. A second later, the next night is selected.

## Alternatives Considered

### Alternative 1: Keep judging the whole night
- **Pros**: no change; the verdict and the targets stay in step.
- **Cons**: the answer is wrong once the night has started. A clear evening
  keeps a socked-in rest of the night afloat, and a past gust gates a calm
  night.
- **Why not**: the product's core value is never dressing up a bad night. A
  score that counts hours already gone is a quiet lie.

### Alternative 2: Narrow the dark-window field itself to the remaining span
- **Pros**: one window for everything; no new field.
- **Cons**: the dark-window field is a frozen contract, and the moon and the
  targets are defined against the whole night. Narrowing it would change the
  meaning of an existing field and break those readers.
- **Why not**: the contract forbids changing what an existing field means. The
  document may only grow.

### Alternative 3: Judge a fixed session window, such as the next six hours
- **Pros**: matches how long a person tends to image.
- **Cons**: adds a knob, and cuts against the astronomical-night clamp that
  bounds every other window in the system.
- **Why not**: dawn is the natural end of the night and needs no setting. A
  shorter session is the user's call, not the system's.
