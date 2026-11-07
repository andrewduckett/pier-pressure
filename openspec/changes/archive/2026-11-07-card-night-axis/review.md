## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `ca04b79`

## Findings

### 🔴 Critical (blocking)

1. **Two unchanged main-spec requirements contradict the Sun altitude row.** Check: contradictions. "More cloud is darker" shades "each cell" by the 15% rule, so a Sun altitude cell at −18° would need `#cde2fb` and `#0d366b` at once. "No cloud sensors at all" says the card shows "the four labelled rows", and the strip now has five. **CONFIRMED.**

### 🟡 Moderate

2. **The line overlay has no `inset: 0` and no stacking order.** Check: contradictions (DD5 against the line requirements). An absolutely positioned grid child without `inset` keeps its auto size and collapses, and opaque cells earlier in paint order would cover the lines and take their hover. A style check in happy-dom passes either way. **CONFIRMED.**
3. **Assumption D9's hover text names a forecast boundary as a moonrise or moonset, and wraps a run of 24 hours or more.** Check: assumption rows. The timeline holds only hours a weather source returned (`docs/night-timeline.md`, lines 77 to 80), so a run at the forecast's start or end has an unknown rise or set. A run of 25 hours reads `from 12:00 to 13:00`, since `HH:MM` carries no date. **CONFIRMED.**
4. **The existing `pinClock` fakes only `Date`, so a timer test would pass with no cleanup.** Check: test seams. `card/test/strip.test.ts` line 35 passes `toFake: ["Date"]`; real intervals are invisible to `vi.getTimerCount()`. A second `connectedCallback` without a clear would leak a timer. **CONFIRMED.**

### 📌 Suggestions

5. **`data-line` on both a line and its label makes `[data-line="dusk"]` find two elements.** Check: test seams. **CONFIRMED.**
6. **Plain language: a 58-word sentence with an actorless passive in adr.md, a 53-word WHEN clause and a 38-word requirement sentence in the spec, and long bullets in design.md.** Check: plain language. **CONFIRMED.** The reviewer's "marks row" against "line labels" is a naming of one thing in two documents at two levels (the row that holds the labels, and the labels), not two words for one concept, so it stays.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. specs: MODIFIED "More cloud is darker" says "each cell in a cloud row". MODIFIED "A missing cloud sensor leaves an empty row" says "the other three cloud rows" and "the four labelled cloud rows".
2. design.md DD5: `.lines` has `inset: 0`, is the strip's last child and has `z-index: 1`. DD8: the tests assert these in its style.
3. brainstorm.md D9, specs "Hovering over a Moon up bar shows its hours" with a new "A Moon up bar names only a rise or set the forecast shows", and design.md DD3: a rise or set is shown only when the forecast holds a value of 0 or below beside the run; otherwise the text is `Moon up from <HH:MM>`, `Moon up until <HH:MM>` or `Moon up`. A run of 24 hours or more shows `Moon up`. Scenarios for each form. Risks and the docs requirement say so.
4. design.md Test Seams: the timer tests fake `Date`, `setInterval` and `clearInterval` together. DD7: `connectedCallback` and `disconnectedCallback` call `super`, and `connectedCallback` clears any timer it already holds.
5. design.md DD8: the labels carry `data-mark`, and only the lines carry `data-line`.
6. Plain language: split the long sentences in adr.md, the "Three runs" scenario, the Moon up hover requirement (now split in two to pass strict validation), the Test Seams bullets, DD5 and the Risks bullet, and make adr.md's passive active.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1.
2. Fixed: required change 2.
3. Fixed: required change 3.
4. Fixed: required change 4.
5. Fixed: required change 5.
6. Fixed: required change 6, except the "marks row" naming, kept for the reason given under finding 6.
