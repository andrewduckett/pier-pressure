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
