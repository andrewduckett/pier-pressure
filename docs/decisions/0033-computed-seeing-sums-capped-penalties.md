---
id: adrs-adr0033
date: 2026-11-05
status: accepted
title: 'ADR-0033: Computed seeing subtracts capped penalties for bad layers, the jet stream and the boundary layer'
description: Architecture decision record for the uncalibrated formula behind computed seeing. It counts strongly stable layers between the pier's ground and the tropopause, penalises a 300 hPa wind outside 5 to 35 m/s and a deep boundary layer, and subtracts the three penalties from 1 on the 0 to 1 seeing scale. Only models that send the whole column feed it.
---

# ADR-0033: Computed seeing subtracts capped penalties for bad layers, the jet stream and the boundary layer

Builds on ADR-0031.

## Context

Seeing is a quality from 0 to 1, where 1 is best. 7Timer! fills it from an
index from 1 to 8, mapped as `(8 − index) / 7`. The computed source derives
seeing from one weather model's column: temperature and geopotential height at
17 pressure levels from 1000 to 50 hPa, the 300 hPa wind speed in km/h, and
boundary-layer height in metres above ground. Meteoblue describes bad seeing
with three features:

- "bad layers", where the temperature gradient exceeds 0.5 K per 100 m
- a jet stream faster than 35 m/s
- a jet stream slower than 5 m/s

Neither meteoblue nor 7Timer! publishes a formula or a validation. This formula
is uncalibrated, and is meant to be calibrated against the rig's guiding logs
later.

A check of Open-Meteo on 2026-11-05 showed which models send the column:

- **Best match and GFS** send every level, the 300 hPa wind and boundary-layer
  height.
- **HRRR** sends everything except the 70 and 30 hPa levels, which the column
  leaves out.
- **ICON, GEM regional (RDPS) and HRDPS** send no boundary-layer height. HRDPS
  also covers only 43 of 48 hours.

## Decision

Only best match, HRRR and GFS declare the column, as one bundle, so one model
feeds each hour's index and every index is worked out the same way. For each
hour that has the whole column:

1. **Bad layers.** A layer between two adjacent levels is bad when its
   temperature falls by less than 0.476 K per 100 m, or rises. That is a
   potential-temperature rise of more than 0.5 K per 100 m, measured as if
   the layer were at 1000 hPa. Count `n`, the bad layers whose lower level is
   at or above the pier's elevation and which lie below the tropopause.
2. **Tropopause.** The tropopause is the lowest level at 500 hPa or higher up
   from which temperature falls by 2 K per km or less to the next, higher,
   level.
3. **Index.** `q = clamp(1 − 0.12 × n − P_jet − P_blh, 0, 1)`, where:
   - `P_jet = 0.4 × clamp((w − 126) / 126, 0, 1) + 0.15 × clamp((18 − w) / 18, 0, 1)`
     for the 300 hPa wind `w` in km/h
   - `P_blh = 0.25 × clamp((h − 200) / 1300, 0, 1)` for boundary-layer height
     `h` in metres

For example, 2 bad layers, a 150 km/h jet and a 500 m boundary layer give
0.6261. Three bad layers, a 250 km/h jet and a 900 m boundary layer give
0.1117. The value is uncalibrated.

## Consequences

- **Easier:** each term can be read and calibrated on its own, and each
  penalty only grows as its input worsens. Tests can check the shape of the
  index without fixing its calibration.
- **Easier:** the test reads stability the same way at every height, so air
  that cools at the normal rate, about 0.65 K per 100 m, is never bad. The
  count then varies with the night, not with the season's tropopause height.
- **Easier:** a value from HRRR and one from GFS mean the same thing, so the
  computed source's health can name the model, and nights can be compared
  across a change of model.
- **Harder:** the Canadian models can't feed seeing, though HRDPS has the
  finest grid over the Great Lakes. A pier that lists HRDPS first gets its
  seeing column from the next complete model.
- **Harder:** a strong inversion between 500 hPa and the real tropopause is
  read as the tropopause, and the layers above it are not counted. It only
  undercounts.
- **Harder:** the weights are guesses. A change to any constant changes every
  pier's computed seeing. Make one deliberately, in a new record, so that
  nights before and after can still be compared.

## Alternatives Considered

### Alternative 1: Let every model feed seeing, and drop the boundary-layer term when it is missing
- **Pros**: HRDPS, with its 2.5 km grid, could feed seeing.
- **Cons**: two models' indices would be worked out differently. The dropped
  term is the one that depends most on the site.
- **Why not**: an index whose meaning changes with its model can't be
  compared night to night, or ranked fairly against 7Timer!.

### Alternative 2: Estimate seeing in arcseconds, then map it onto 7Timer!'s bins
- **Pros**: the same approach as computed transparency, and a value in a
  physical unit.
- **Cons**: no free source gives a formula from these inputs to arcseconds.
- **Why not**: the figure would claim a precision the index doesn't have.

### Alternative 3: Multiply three factors instead of subtracting penalties
- **Pros**: each factor is a clean fraction, and the product stays between
  0 and 1.
- **Cons**: one bad term can zero the index on its own.
- **Why not**: a single strong inversion would read as the worst seeing
  possible, which over-punishes one feature of the column.

### Alternative 4: Use the raw potential-temperature gradient
- **Pros**: the textbook measure of stability, with no correction.
- **Cons**: the raw gradient grows with height, about 1.6 times at 200 hPa.
  Air cooling at the normal rate counts as bad above about 250 hPa.
- **Why not**: on a summer night, with a high tropopause, every hour would
  start with one to three bad layers.

### Alternative 5: Read meteoblue's gradient literally, as temperature change in either direction
- **Pros**: it follows the quoted description word for word.
- **Cons**: normal air cools by more than 0.5 K per 100 m, so most layers
  count as bad on most nights.
- **Why not**: a count that barely varies tells the pier nothing.
