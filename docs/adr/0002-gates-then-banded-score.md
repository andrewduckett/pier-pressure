---
id: adrs-adr0002
date: 2026-09-07
status: accepted
title: 'ADR0002: Verdict uses hard gates then a banded score'
description: Architecture Decision Record for computing the night verdict as hard dealbreaker gates followed by a banded 0-100 score, rather than a single weighted average.
---

# ADR-0002: Night verdict uses hard gates then a banded score, not a single weighted average

## Context

PierPressure produces one verdict each night: is tonight worth setting up for?
That verdict must be trustworthy. A wrong answer that hides a dealbreaker, or
scores a hopeless night as a near-miss, is worse than a coarse but honest one. The
night is judged on several factors — the sky, the weather conditions, and the
horizon. A single weighted average across those factors can average a dealbreaker
away. It could report 7/10 while the sky is overcast across the entire dark
window.

## Decision

Compute hard gates first. If any gate fails — no astronomical-dark window,
overcast across the dark window, or wind above a safe limit — the verdict is a
NO-GO with a plain-language reason and no score. Only when every gate passes does
a banded 0-to-100 score follow. The score is built from itemized terms, each a
bonus or penalty: the length of the dark window, the best target's altitude above
the horizon, the moon's brightness and nearness, and the seeing and transparency.
Those itemized terms are surfaced directly as the verdict's reasons. A gated NO-GO
carries no score at all.

## Consequences

- **Easier:** explainability comes for free — the scoring terms are the
  explanation. A dealbreaker is never dressed up as a numeric near-miss. Each gate
  and term is testable and deterministic on its own.
- **Harder:** the gate set and the term weights must be curated and justified. The
  two-stage logic is a little more involved than a single sum.

## Alternatives Considered

### Alternative 1: A single weighted score with a go/no-go threshold
- **Pros**: the simplest thing to build and reason about; one formula.
- **Cons**: averaging can mask a dealbreaker, and the go/no-go threshold is
  arbitrary.
- **Why not**: it fails the trustworthiness test. The product's core value is
  never quietly hiding a bad night or a blocked target.

### Alternative 2: A learned or machine-learned scoring model
- **Pros**: it could capture subtle interactions from historical data.
- **Cons**: it is opaque, hard to explain, non-deterministic, and needs labelled
  data.
- **Why not**: it breaks the deterministic-and-explainable rule. The truth about
  astronomy and conditions must not come from an opaque model.
