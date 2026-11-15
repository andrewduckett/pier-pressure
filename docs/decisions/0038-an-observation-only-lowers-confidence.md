---
id: adrs-adr0038
date: 2026-11-14
status: accepted
title: 'ADR-0038: An observation can only lower confidence, never raise it or change a gate or the score'
description: Architecture decision record for letting an airport's METAR change the verdict only by lowering confidence, when it reports more cloud than the current hour's forecast, and never by raising confidence, firing a gate or moving the score.
---

# ADR-0038: An observation can only lower confidence, never raise it or change a gate or the score

Builds on ADR-0029.

## Context

A pier can name an airport weather station, and the verdict quotes that
station's latest METAR. The report is a measurement, not a forecast: one moment,
at an airport that may be several kilometres from the pier. An automated station
sees cloud only up to 12,000 ft, and a CAVOK report vouches only for 5,000 ft.
So a report of no cloud does not show a clear sky. High cloud, and much of the
mid layer, can sit above what the station sees. When the report shows more
cloud than the forecast for the same hour, though, the forecast is already
wrong. The verdict has hard gates, a score when the gates pass, and a confidence
that says how far to trust the call. Forecast agreement already lowers
confidence and nothing else.

## Decision

The observation reaches the verdict only through confidence, and only
downwards. When it shows more cloud below 12,000 ft than the forecast's low and
mid cloud for the hour that holds the evaluation instant, confidence is
multiplied by a factor below 1, with a reason line. A report with the same or
less cloud, a clear report and a CAVOK report change nothing. The gates and the
score never read the observation.

## Consequences

- **Easier:** a forecast that is already wrong at dusk is trusted less for the
  rest of the night, in the field a reader and an automation already watch.
- **Easier:** a station that sees less of the sky than the pier, or sits under
  a different sky, can at worst make the call less certain. It never turns a
  `NO-GO` into a `GO` or the reverse.
- **Easier:** a pier with no station gets exactly the verdict it got before.
- **Harder:** a clear report under a cloudy forecast, which may mean the
  forecast is too pessimistic, is ignored. The reader still sees the report in
  its own reason line.
- **Harder:** confidence has five inputs, and the observation's bands and
  factors are tuning constants that need a justification beside them.

## Alternatives Considered

### Alternative 1: Compare in both directions
- **Pros**: a forecast that is wrong either way is trusted less, so the measure
  is symmetric.
- **Cons**: a clear report is the one reading the station cannot vouch for.
  High cloud and the upper mid layer are invisible to it, so a clear report
  under a cloudy forecast is often both right.
- **Why not**: it would lower confidence on nights when the forecast is right
  and the station simply cannot see the cloud.

### Alternative 2: Let a cloudy report fire a gate or lower the score
- **Pros**: overcast at the airport right now would read as a worse night.
- **Cons**: the gates and the score judge the whole scored window from the
  forecast. One report covers one moment at another place. A broken layer at
  dusk says nothing about the hours after midnight.
- **Why not**: the score answers how good the night is, and one report cannot
  answer that for the night. Confidence already carries how far to trust the
  forecast, and the product keeps score and confidence apart.

### Alternative 3: Let a report that matches the forecast raise confidence
- **Pros**: a forecast that tracks reality earns more trust.
- **Cons**: confidence is capped at 100 and already rises as dusk nears. A
  match below 12,000 ft says nothing about high cloud, which the score reads.
- **Why not**: a match proves less than it seems, and raising confidence on it
  would claim a certainty the station cannot give.
