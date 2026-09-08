---
id: adrs-adr0002
date: 2026-09-07
status: accepted
title: 'ADR0002: Verdict uses hard gates then a banded score'
description: Architecture Decision Record for computing the night verdict as hard dealbreaker gates followed by a banded 0-100 score, rather than a single weighted average.
---

# ADR-0002: Night verdict uses hard gates then a banded score, not a single weighted average

## Context

The night verdict must be trustworthy: a wrong answer that silently hides a dealbreaker (or scores a hopeless night as a near-miss) is worse than a coarse-but-honest one. A single weighted average across sky, conditions, and horizon factors can average away a dealbreaker — for example reporting 7/10 while the sky is fully overcast across the entire dark window.

## Decision

Compute hard gates first: if any gate fails (e.g. no astronomical-dark window, overcast across the dark window, wind above a safe limit) the verdict is NO-GO with a human-readable reason and a null score. Only when all gates pass is a banded 0-100 score computed from itemized bonus/penalty terms (dark-window length, best target altitude above the horizon mask, moon illumination and proximity, seeing/transparency). The itemized terms are surfaced directly as `reasons[]`, and `score` is null on any gated NO-GO.

## Consequences

- Easier: explainability falls out of the scoring terms for free; a dealbreaker is never presented as a numeric near-miss; each gate and term is independently testable and deterministic.
- Harder: the gate set and term weights must be curated and justified; the two-stage logic is slightly more involved than a single sum.

## Alternatives Considered

### Alternative 1: Single weighted score with a go/no-go threshold
- **Pros**: simplest to implement and reason about; one formula.
- **Cons**: can mask dealbreakers by averaging; the go/no-go threshold is arbitrary.
- **Why not**: fails the trustworthiness requirement — the core value of the product is not silently hiding a bad night or a blocked target.

### Alternative 2: A learned/ML scoring model
- **Pros**: could capture subtle interactions from historical data.
- **Cons**: opaque, hard to explain, non-deterministic, needs labelled data.
- **Why not**: violates the deterministic-and-explainable requirement; astronomy/conditions truth must not come from an opaque model.
