---
id: adrs-adr0029
date: 2026-11-02
status: accepted
title: 'ADR-0029: Forecast agreement is an input to confidence, never to a gate or the score'
description: Architecture decision record for measuring how far several providers' cloud forecasts agree, from the alternates the fill keeps, and folding the result into confidence as a multiplier while the gates and the score keep reading one filled series.
---

# ADR-0029: Forecast agreement is an input to confidence, never to a gate or the score

## Context

Conditions are filled variable by variable from an ordered provider list, and
each Open-Meteo model is its own provider, so a pier can list several cloud
forecasts for the same hours. Only the first that returned cloud fills the
series the gates and the score read. The verdict has three parts that a reader
trusts differently: hard gates that make a `NO-GO`, a banded score when the gates
pass (ADR-0002), and a confidence that says how far to trust the call.
Confidence so far reads lead time, freshness and completeness. The verdict
document is a frozen contract that grows only additively, and the core must stay
a pure function of its inputs.

## Decision

The series that lose the fill travel to the core as alternates, kept beside the
filled series and read for nothing else. The core measures agreement for cloud
cover as the clarity-weighted mean, over the scored window, of the hourly gap
between the lowest and highest cloud any provider gave, weighting each hour by
the clarity of its most optimistic reading. The result is banded agree, mixed
or disagree, carried in the document as an `agreement` object keyed by variable,
named in a reason line, and multiplied into confidence. The gates, the score and
the verdict value keep reading the one filled series; alternates are never
blended into it.

## Consequences

- **Easier:** the reader learns whether tonight's call is one model's opinion
  or a consensus, in the same place they already look for how far to trust it.
- **Easier:** the measure reuses the clarity and coverage weights the score is
  built on, so there is still one notion of "usable dark time per hour".
- **Easier:** agreement on another variable, such as gusts, is a new key in the
  same object, with no reshaping.
- **Easier:** the fill, the gates and the score are unchanged, so a user who
  lists one cloud provider sees the same verdict as before.
- **Harder:** the shape of `agreement` and the names of the two timeline keys
  are part of the frozen contract from the first release that carries them.
- **Harder:** confidence now has four inputs, and the agreement bands and
  factors are tuning constants that need a justification kept beside them.
- **Harder:** weighting by the most optimistic reading means a single
  optimistic model can mark a night as disagreeing. That is intended: the
  optimistic forecast is the one that would have sent the observer out.

## Alternatives Considered

### Alternative 1: Blend the providers' cloud into one consensus series
- **Pros**: one series to score; disagreement averages out; no new object.
- **Cons**: the filled series loses its provenance, so freshness and the
  provider's key no longer mean one provider's data. A blend hides the spread
  the reader wants to see, and changes the score and the gates for every user
  who lists more than one model.
- **Why not**: it breaks the rule that a series comes whole from one provider,
  and it changes existing verdicts instead of adding to them.

### Alternative 2: Let disagreement lower the score or fire a gate
- **Pros**: a disagreeing night would read as a worse night, which is easy to
  act on.
- **Cons**: the score answers "how good is the night" and the gates "is it
  safe and possible". Disagreement answers neither; it says how sure the
  forecast is. A disagreeing but clear night would score below a unanimous
  hazy one.
- **Why not**: confidence already exists to carry how far to trust the call,
  and the product rule keeps score and confidence orthogonal.

### Alternative 3: Report the spread only, with no effect on confidence
- **Pros**: purely additive; no tuning constants.
- **Cons**: the reader has to combine two numbers in their head, and an
  automation that acts on the confidence band would not see the disagreement.
- **Why not**: the product intent says confidence reflects how well the
  forecasts agree when more than one gives cloud.
