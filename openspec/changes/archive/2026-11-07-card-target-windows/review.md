## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family
- **Independent**: yes (the plan was written by Claude; gemini/gemini-4-argon reviewed, through `lets delegate review run`)
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit f40cbf0

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Left padding widens every target bar past its window.** Check: contradictions. The card sets each bar's width inline as a share of the axis, and its CSS uses the default `content-box`. DD2's 4 px left padding would make each bar 4 px wider, over the dawn line and past the axis end. CONFIRMED: `card/src/pierpressure-card.ts` `.bar` has no `box-sizing`, and `renderBar` sets `width` inline.
2. **A transient `unknown` or empty state draws a lane with no name.** Check: assumption rows (D4). Delivery publishes a rank's state and its attributes as two MQTT messages (`pierpressure/delivery/mqtt.py`, `MqttDelivery.publish`). So Home Assistant can briefly hold `unknown` or `""` beside a window, and the plan only skipped `unavailable`. CONFIRMED.
3. **The hover reads "from 10:58 to 10:58" for a target up all through a polar night.** Check: assumption rows (D9). A polar dark window runs solar noon to solar noon, just over 24 hours. `moonUpText` guards against this case and the plan's hover did not. CONFIRMED: `card/src/strip.ts` `moonUpText`; the reviewer reproduced a 24 h 00 m 30 s window from the core at 86° N.

### 📌 Suggestions

4. **DD4 leaves out the missing config, and DD1 leaves the overlap rule implicit.** Check: contradictions. `getCardSize` can run before `setConfig`. A window that only touches an axis end must give no zero-width bar. CONFIRMED.
5. **Four sentences run over 30 words, and D14's opening-paragraph decision is not in the spec.** Check: plain language; scope. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. DD2: indent the bar's text with `text-indent`, not padding, so the bar's width stays the window's.
2. DD1, D4 and the requirement "A rank with no target tonight leaves no lane": skip a rank whose state is `unavailable`, `unknown` or empty, with a scenario for `unknown` and empty states beside a valid window.
3. D9, DD1 and the requirement "Hovering over a target bar shows its window": show `<name>` alone when the window lasts 24 hours or more, or both ends read the same `HH:MM`, with a polar-night scenario.
4. DD4 and DD1: name the missing config, and the strict overlap rule `end > axis.start && start < axis.end`, with the touching case in the bar requirement. Split the long sentences, and add a requirement for the docs' opening paragraph (D14).

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: DD2 now uses `text-indent: 4px` and says why padding would widen the bar.
2. Fixed: DD1 lists `unavailable`, `unknown` and empty, and says why. The spec requirement lists the three states, with the scenario "A rank whose name has not arrived". Ledger row D4 now says the same.
3. Fixed: DD1, the hover requirement and ledger row D9 give `<name>` alone, with the scenario "A target up all through a polar night".
4. Fixed: DD4 names "no config yet", DD1 states the overlap rule, and the bar requirement says a window touching an axis end counts as outside.
5. Fixed: the long sentences in DD2, DD3, the Risks and the two spec requirements are split. The new requirement "The docs' opening names the targets" carries D14. It is its own requirement because the docs requirement passed 500 characters with it.
