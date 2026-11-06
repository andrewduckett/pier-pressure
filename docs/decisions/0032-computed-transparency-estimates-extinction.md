---
id: adrs-adr0032
date: 2026-11-05
status: accepted
title: 'ADR-0032: Computed transparency estimates extinction and maps it onto 7Timer!''s scale'
description: Architecture decision record for the uncalibrated formula behind computed transparency. It estimates zenith V-band extinction from aerosol optical depth and column water vapour, then maps that linearly across 7Timer!'s extinction range onto the 0 to 1 transparency scale.
---

# ADR-0032: Computed transparency estimates extinction and maps it onto 7Timer!'s scale

Builds on ADR-0031.

## Context

Transparency is a quality from 0 to 1, where 1 is best. 7Timer! fills it by
mapping its index from 1 to 8 as `(8 − index) / 7`. Its index bins are total
extinction in magnitudes per airmass: below 0.3 is index 1, and above 1.0 is
index 8. The computed source must give a value on the same scale, so that a
pier can rank the two sources fairly. Its inputs per hour are aerosol optical
depth at 550 nm, which has no unit, and column water vapour, in kg/m². No
free service publishes a validated formula. This one is uncalibrated, and is
meant to be calibrated against observing logs later.

## Decision

For each hour that has both inputs, estimate the zenith V-band extinction in
magnitudes per airmass:

`E = 0.17 + 1.086 × AOD + 0.006 × W`

- `0.17` is a fixed floor for Rayleigh scattering and ozone at sea level.
- `1.086 × AOD` converts aerosol optical depth to magnitudes.
- `0.006 × W` is a haze proxy for water vapour `W`, in kg/m².

Then map `E` linearly across 7Timer!'s range:
`transparency = clamp((1.0 − E) / 0.7, 0, 1)`.

For example, AOD 0.15 with 30 kg/m² gives `E` = 0.5129 and transparency
0.6959. Smoke at AOD 0.60 with 20 kg/m² gives 0.0834. The value is
uncalibrated.

## Consequences

- **Easier:** the value has a physical unit before it is mapped, so it can be
  compared with 7Timer!'s bins and calibrated term by term.
- **Easier:** smoke shows up. Aerosol dominates the estimate, which 7Timer!'s
  index doesn't see.
- **Easier:** neither input can raise the value, and every value lies between
  0 and 1, so tests can check its shape without fixing calibration.
- **Harder:** the fixed floor ignores the pier's elevation. A pier at 1500 m
  reads about 0.04 too low.
- **Harder:** water vapour absorbs little in the V band, so its term is a proxy
  for the haze that humid air carries, not physics. Its weight is a guess.
- **Harder:** a change of any constant changes every pier's computed
  transparency. Make one deliberately, in a new record, so that nights before
  and after can still be compared.

## Alternatives Considered

### Alternative 1: Two independently clamped terms, multiplied
- **Pros**: simple, and each input's effect is easy to see.
- **Cons**: the product has no unit, and its clamp points are arbitrary.
- **Why not**: it can't be checked against 7Timer!'s bins, which are
  extinction, so ranking the two sources would be a guess.

### Alternative 2: Step through 7Timer!'s exact bins
- **Pros**: the value matches 7Timer!'s eight levels exactly.
- **Cons**: a staircase throws away resolution the hourly inputs carry, and
  small input changes jump a whole level.
- **Why not**: an uncalibrated estimate gains nothing from false precision at
  the bin edges, and loses smoothness.

### Alternative 3: Aerosol alone
- **Pros**: the best-grounded term, with no proxy.
- **Cons**: humid, hazy nights with clean aerosol read as excellent.
- **Why not**: water vapour is the other input this source was built to use,
  and a small weight keeps its error small.
