## Review Metadata

- **Review round**: 1
- **Prior round**: none. An earlier attempt on gemini-4-argon returned only "Usage Limit Reached" and no review, so it does not count as a round.
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported the working tree clean after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, ADR-0026, and the relevant source files, at commit 155b004

## Findings

### 🔴 Critical (blocking)

1. **The card type is `custom:plotly-graph`, not `custom:plotly-graph-card`.** Check: contradictions. The spec and DD7 named a type that Home Assistant would reject with "Custom element doesn't exist", and a correct YAML would fail the guard test. **CONFIRMED**: all 49 examples in the plotly-graph-card README use `type: custom:plotly-graph`, and none uses `-card`.
2. **The 7Timer! health entity id is `sensor.pierpressure_backyard_7timer_health`.** Check: contradictions. The spec named `seven_timer_health`, which is the MQTT topic segment, not the entity id. Home Assistant slugs the discovery name `7Timer! health` to `7timer_health`. **CONFIRMED**: `README.md:420` already gives `sensor.pierpressure_backyard_7timer_health`.
3. **The relative window in DD5 starts in the future before dusk, and can drift.** Check: assumptions. Before dusk, `time_offset` exceeds `hours_to_show`. Unless both are recomputed on each refresh, the range slides with the clock. **CONFIRMED in part**: the arithmetic does give the right range (16:30 to 08:25 in the reviewer's own example), so nothing "inverts". But a range starting in the future is behaviour the README never describes, and recomputing on every refresh was unstated. An absolute `layout.xaxis.range` fits a fixed night better.

### 🟡 Moderate

4. **Lane thickness changes with the number of lanes.** Check: scenario behaviour. Plotly shares a fixed axis domain among its categories, so two lanes draw far thicker than ten. **CONFIRMED**: DD3 did not say how the lanes' domain adapts.
5. **The Verdict has no attributes builder in the adapter.** Check: test seams. DD7 said the published keys come from "the adapter's attribute builders", but the Verdict payload is built inline. **CONFIRMED**: `pierpressure/delivery/mqtt.py:1059` publishes `document.model_dump_json(exclude={"timeline"})` directly.
6. **D9 (local time) is an Assumption that the mock contradicts.** Check: assumption rows. The mock is in UTC. **REFUTED**: the mock is in UTC only because its mock data is the London golden fixture. D9 rests on the epic's shared decision that the user's pier is in the US, and on plotly-graph-card following the Home Assistant time zone (`time_zone: server`). The user confirmed the ledger with D9 as an Assumption.
7. **D10 is evidence, not an assumption: "#135 Scope dictates `docs/night-dashboard.md`".** Check: assumption rows. **REFUTED**: the packet's **Relevant code** says only "new, under `docs/`". It names no file, so D10 stays an Assumption. That leaves nothing to fix.

### 📌 Suggestions

8. **Sentences over 30 words** in DD2, the spec's row requirement, adr.md line 9 and ADR-0026's Context. Check: plain language. **CONFIRMED** for DD2, which listed five rules in one sentence. The others sit between 31 and 38 words and each carries one idea.

**Found while checking Finding 1:** the plotly-graph-card README's manual install says to download **every** `.js` file of a release into `www/plotly-graph-card/`, because the card loads the other files on demand. DD8 said "the release file", singular, which would give a card that fails to load its chunks.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. spec.md: name the card type `custom:plotly-graph` in the requirement and in the "Only core cards" scenario (Finding 1).
2. design.md DD7: allow `custom:plotly-graph` as the custom card type (Finding 1).
3. spec.md: use `sensor.pierpressure_backyard_7timer_health` in the "Every card is present" scenario (Finding 2).
4. design.md DD5: make an absolute `layout.xaxis.range` from `dark_window` the primary mechanism. Keep a recomputed `hours_to_show` and `time_offset` as the fallback. Check which one the card honours first, in the Docker check, before dusk. Update the matching risk (Finding 3).
5. design.md DD3: compute `layout.height` and the domain split from the number of lanes, so every lane keeps the same thickness (Finding 4).
6. design.md DD7: take the Verdict's published keys from `document.model_dump_json(exclude={"timeline"})`, the call the adapter makes, and the other entities' keys from their public builders (Finding 5).
7. design.md DD2: split the five shading rules into a list (Finding 8).
8. design.md DD8: install every `.js` file of the pinned release into `www/plotly-graph-card/` (found while checking Finding 1).

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required changes 1 and 2.
2. Fixed: required change 3.
3. Fixed: required change 4. The reviewer's "inversion" did not happen, as noted above, but the fix removes both the unstated recompute and the undocumented future-start window.
4. Fixed: required change 5.
5. Fixed: required change 6.
6. Rebutted: the user confirmed D9 as an Assumption; the evidence is above.
7. Rebutted: the packet names no file; the evidence is above.
8. Fixed for DD2 (required change 7). Declined for the rest: each long sentence carries one idea, and splitting it would not help a reader.
