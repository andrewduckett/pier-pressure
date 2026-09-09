# ADR Review Manifest

- Status: completed
- Review date: 2026-09-07

## Review Summary

ADR review completed for the `add-walking-skeleton` change. `design.md` was re-read and each decision assessed against the bar (hard to reverse AND surprising without context AND the result of a real trade-off). Three foundational, cross-cutting decisions qualified and were captured as new repository-level ADRs. Reversible implementation choices — the uv/just/ruff toolchain (D10), Pydantic for models/config (D2), and the threaded paho loop (D7) — were deliberately excluded as they do not meet the bar.

## In-Force ADRs Reviewed

- None — `docs/adr/` contained only `ADR-000-template.md` (the template); there were no in-force repository ADRs prior to this change. No supersession graph applies. Highest pre-existing sequence: 000 (template).

## New Durable ADRs Created

- `docs/adr/0001-core-ha-agnostic-json-verdict-contract.md` — standalone, self-scheduling pure core emitting a JSON verdict contract; Home Assistant is a dumb, replaceable MQTT-discovery adapter and never load-bearing. (Basis for design D1, D2, D5, D7 wiring and the persistent-container model.)
- `docs/adr/0002-gates-then-banded-score.md` — verdict is hard dealbreaker gates then a banded 0-100 score (null on gated NO-GO), not a single weighted average; `reasons[]` are the itemized terms.
- `docs/adr/0003-astronomical-night-hard-clamp.md` — target observability is always clamped to astronomical night regardless of any user-requested view window; `dark_window` is a first-class contract field.
