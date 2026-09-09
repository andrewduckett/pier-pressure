# ADR Review Manifest

- Status: completed
- Review date: 2026-09-08

## Review Summary

ADR review completed for this change. Reviewed the design's technical decisions
against the existing in-force ADRs. One decision met the bar for a durable,
repository-level ADR — the deterministic-offline astronomy strategy — because it
is hard to reverse (it sets the astronomy library and data-pinning discipline for
the whole project), surprising without context (Skyfield-only despite the
roadmap's three-library candidate set; vendoring an ephemeris rather than letting
the library fetch it), and the result of a real trade-off (offline determinism
versus Astropy's convenience and precision). The astronomical-night hard clamp is
already decided in ADR-0003 and is not re-decided here; moon-object shape, the
rounding rule as a facet of determinism, and keeping the alt/az engine internal
are reversible design choices captured in design.md, not ADRs.

## In-Force ADRs Reviewed

- ADR-0001 — Home-Assistant-agnostic core with a JSON verdict contract delivered via a dumb adapter (accepted)
- ADR-0002 — Night verdict uses hard gates then a banded score, not a single weighted average (accepted)
- ADR-0003 — Target observability is hard-clamped to astronomical night, regardless of the requested view window (accepted)

## New Durable ADRs Created

- `docs/adr/0004-deterministic-offline-astronomy.md` — Deterministic offline astronomy via Skyfield with a pinned ephemeris and built-in timescale (accepted). Establishes Skyfield-only computation, a version-pinned bundled ephemeris, the built-in timescale, zero runtime network access, and fixed-precision rounding for byte-identical output.
