## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family
- **Reviewer**: gemini/gemini-4-argon, through `lets delegate review run` (resolver `t3`, effort medium)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Commit reviewed**: 6a5e6b1
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/conditions/spec.md, adr.md, the main conditions spec, provider.py, seven_timer.py, open_meteo.py, core/providers.py, core/conditions.py, core/scoring.py, core/config.py, health.py, service.py, the provider, catalog and config tests, ADR-0027 to ADR-0029, README

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Stale grid cell after a gridpoint 404** (D3, DD3). The cache dropped an entry only when the point request failed. A gridpoint 404, the signal that a cell moved, would fail every recompute until a restart. Check: assumption rows and where it stops working. CONFIRMED.
2. **NWS 301 redirect on coordinates with more than four decimals.** NWS redirects `points/{lat},{lon}` to the four-decimal form. `httpx.Client` does not follow redirects by default, and `open_meteo.py`, the named template, does not set it; `seven_timer.py` does. A pier with five-decimal coordinates would fail on every fetch. Check: where it stops working. CONFIRMED.
3. **A period straddling the 72-hour horizon was unspecified.** The scenario tested only a period that starts past the horizon. DD2 said "every slot from the start for the duration", which an implementer could read as checking the start alone. Check: scenario testability. CONFIRMED.

### 📌 Suggestions

4. **"A bundle travels together" shares its WHEN with the new split-bundle scenario.** They differ only in whether the first provider declares the four-variable bundle, which the WHEN did not say. Check: contradictions. CONFIRMED for the delta's scenario. The reviewer also suggested editing the main spec's "A losing bundle becomes alternates member by member". Declined: that requirement is not in this delta, and the delta's own scenario now states the distinction.
5. **Sentences over 30 words** in design.md DD6, proposal.md Modified Capabilities, and the units and fill requirements of the delta. Check: plain language. CONFIRMED.

The reviewer also traced DD6 by hand for `[open_meteo_hrdps, open_meteo]`, `[open_meteo, open_meteo_hrrr]` and `[nws, open_meteo]` and found the first two identical to today and the third as the delta describes. It confirmed the service is single-threaded, so the cache has no race; that `fetchers` overrides do not leak; and that `__version__` imports cleanly under the core-boundary test.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Design DD3 and the two-step requirement: the point request follows redirects; a gridpoint 404 forgets the remembered cell. Add scenarios for both.
2. Horizon scenario: a period that straddles the horizon is cut at it; keep a second scenario for a period that starts past it. DD2 says each slot is checked against the horizon.
3. "A bundle travels together" WHEN states that the first provider declares the four-variable cloud bundle. Split the named long sentences in design.md, proposal.md and the delta.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed. design.md DD3 and the risk line; proposal.md What Changes; delta requirement "NWS's point request follows redirects and a gridpoint 404 forgets the cell", split out of the two-step requirement because strict validation flagged the combined text as too long, with scenario "A gridpoint 404 forgets the cell".
2. Fixed. design.md DD3; delta requirement text plus scenario "Coordinates with five decimal places still resolve"; proposal.md What Changes.
3. Fixed. design.md DD2 last sentence; delta scenarios "A period that straddles the horizon is cut at it" and "A period that starts past the horizon is dropped".
4. Fixed for the delta: scenario "A bundle travels together" WHEN. Main-spec edit declined, see above.
5. Fixed. design.md DD6 split into four sentences; proposal.md Modified Capabilities split into three; delta units requirement and fill requirement split.
