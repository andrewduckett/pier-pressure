# Glossary

Shared terms for PierPressure. Each entry gives the term, what it means, and
where the meaning applies. A spec folder may hold a narrower `glossary.md` of
its own. Agree a term with the user before adding it here.

## Timeline

The hourly series of sky and weather for one pier, in the verdict document. One
entry per clock hour, each carrying that hour's conditions and the sun and moon
altitude computed by the core. The hours are those of the selected night's local
solar day, from solar noon to the next solar noon, starting earlier at the
current hour when that comes first, joined by every hour a provider returned for
a variable the timeline shows. The night's hours are present even when every
provider fails; their conditions are then null. A variable the timeline does not
show never adds an hour. The timeline is evidence beside the verdict. It carries
no verdict of its own, and the verdict judges one night regardless of how far
the timeline reaches.

Scope: the verdict document and its delivery. Code and specs use `timeline`.

## Later night

A night after the selected night, one for each local solar day after the
selected night's solar day, from solar noon to the next solar noon. A later
night counts only while the timeline holds an hour that starts inside its solar
day, and there are at most three. It carries its own dark window. It has no
verdict, score or confidence; those judge only the selected night.

Scope: the verdict document, its delivery and dashboards. Code and specs use
`later_nights`.

## Night strip

A dashboard rendering of the timeline: hours across, one row per condition,
and the Temperature chart, with dusk, dawn and the moon on the same time axis.
The Temperature chart is part of the strip: a Temperature line and a Dew point
line on a °C scale, drawn under the target lanes on the strip's time axis, so
it pans with the rows. A strip is a view of the data. Nothing in the core or
the delivery computes or publishes a strip.

Scope: dashboards and their documentation only.

## Provider

One external forecast behind the conditions seam, with a stable key such as
`open_meteo` or `seven_timer`. A provider declares the variables it supplies
and its bundles. The conditions spec says "provider" where it once said
"source".

Scope: conditions, configuration and provider health.

## Variable

One per-hour quantity the conditions carry, named by its key, such as
`cloud_cover`, `wind_gust` or `seeing`. The timeline publishes a documented
subset of the variables; a raw input such as aerosol optical depth is a
variable the timeline does not show. The conditions spec says "variable" where
it once said "field".

Scope: conditions and the verdict document's timeline.

## Series

One variable's hourly values from a single provider, carrying that provider's
key and the issue time of its data. A series comes whole from one provider.
Hours that provider did not cover stay empty; they are never filled from
another provider.

Scope: the conditions snapshot.

## Observation

A report of what the sky or weather was at one moment, measured at one place,
such as the METAR from the airport a pier names. An observation is not a
forecast: unlike a series it covers no hours, comes from no provider in the
provider order and never fills a variable. Its time is when it was measured,
not when it was issued or fetched.

Scope: conditions, the verdict document and provider health.

## Fire detection

A satellite's report of an active fire on the ground, at one place and one
moment, such as a NASA FIRMS hotspot near a pier. Like an observation it is a
measurement, not a forecast: it covers no hours, comes from no provider in the
provider order and never fills a variable. It is not an observation, because
it reports the ground, not the sky or weather above a pier. Its time is when
the satellite passed over.

Scope: conditions, the verdict document's reasons and provider health.

## Bundle

Variables a provider declares travel together, so they are filled from the same
provider or not at all. Two bundles exist: cloud total with its low, mid and
high layers, and the seeing column (layer temperatures and heights, the 300 hPa
wind speed and boundary-layer height).

Scope: conditions.

## Provider order

The configured ordered list of providers, preferred first. Each variable, or
bundle, is filled by the first provider in order that returned it: at least one
hour carries a value for it, or for a variable in its bundle. Every listed
provider is fetched on every recompute, in order.

Scope: configuration and conditions.

## Alternate

A provider's series for a variable that did not win the fill, kept beside the
filled series for comparison instead of being discarded. An alternate never
fills an hour the filled series lacks. The core reads alternates only to
measure agreement.

Scope: the conditions snapshot and the core's agreement measure.

## Agreement

How closely the filled series and its alternates agree on one variable over
the night window, measured by the core and expressed as a band. Low agreement
lowers confidence; it never changes a gate or the score. Agreement is a
property of the forecasts, not of any one provider.

Scope: the core's scoring and the verdict document.

## Computed

The source in the provider order whose variables the core derives from other
series rather than fetches, such as seeing from layer temperature gradients.
It has a stable key, declares its variables and has a health record like a
provider, but it fetches nothing and runs after every provider has returned.

Scope: configuration, conditions and provider health.

## Scored window

The part of the dark window that the verdict and the target ranking judge.
Before astronomical dusk it is the whole dark window. Once the night has
started, it runs from the scoring instant to `dark_window.end`. It is empty only
when the scoring instant equals `dark_window.end`. The `dark_window` field
always keeps the whole night.

Scope: the verdict, target ranking and the verdict document. Code and specs use
`scored_window`.

## Scoring instant

The evaluation instant with its sub-second part removed: the same whole second
as `generated_at`. Once the night has started, the scored window starts here.

Scope: the verdict and target ranking.

## Remaining window

A target's longest stretch above the pier's horizon mask within the scored
window. The ranking gates and scores the target on it. Before dusk it equals
the target's observable window (`window`). Once the night has started it can be
shorter, or, for a target that clears the mask more than once, a different
stretch.

Scope: target ranking and the verdict document's targets. Code and specs use
`remaining_window`.
