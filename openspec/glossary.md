# Glossary

Shared terms for PierPressure. Each entry gives the term, what it means, and
where the meaning applies. A spec folder may hold a narrower `glossary.md` of
its own. Agree a term with the user before adding it here.

## Timeline

The hourly series of sky and weather for one pier, in the verdict document.
One entry per clock hour across every hour the conditions providers returned,
each carrying that hour's conditions and the sun and moon altitude computed by
the core. The timeline is evidence beside the verdict. It carries no verdict
of its own, and the verdict judges one night regardless of how far the timeline
reaches.

Scope: the verdict document and its delivery. Code and specs use `timeline`.

## Night strip

A dashboard rendering of the timeline: hours across, one row per condition,
with dusk, dawn and the moon on the same time axis. A strip is a view of the
data. Nothing in the core or the delivery computes or publishes a strip.

Scope: dashboards and their documentation only.

## Provider

One external forecast behind the conditions seam, with a stable key such as
`open_meteo` or `seven_timer`. A provider declares the variables it supplies
and its bundles. The conditions spec says "provider" where it once said
"source".

Scope: conditions, configuration and provider health.

## Variable

One per-hour quantity the conditions carry, named by its timeline key, such as
`cloud_cover`, `wind_gust` or `seeing`. The conditions spec says "variable"
where it once said "field".

Scope: conditions and the verdict document's timeline.

## Series

One variable's hourly values from a single provider, carrying that provider's
key and the issue time of its data. A series comes whole from one provider.
Hours that provider did not cover stay empty; they are never filled from
another provider.

Scope: the conditions snapshot.

## Bundle

Variables a provider declares travel together, so they are filled from the same
provider or not at all. Today the only bundle is cloud total with its low, mid
and high layers.

Scope: conditions.

## Provider order

The configured ordered list of providers, preferred first. Each variable, or
bundle, is filled by the first provider in order that returned it: at least one
hour carries a value for it, or for a variable in its bundle. Every listed
provider is fetched on every recompute, in order.

Scope: configuration and conditions.
