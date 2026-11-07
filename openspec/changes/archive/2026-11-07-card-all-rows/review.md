## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `25bb78d`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The docs requirement asks for the lightest and darkest shade of every row, but Wind direction has no shade.** Check: contradictions. "The docs describe every row" against "A Wind direction arrow points downwind". **CONFIRMED.**
2. **NWS fills `precipitation_probability` by the hour each value starts, so the one-hour shift draws NWS rain an hour early.** Check: assumptions. `pierpressure/conditions/nws.py` `_hours` keys each hour a period covers by its start, against `docs/night-timeline.md`, which says the value is for the hour that ends at `time`. **CONFIRMED** as a risk; **OUT-OF-SCOPE** as a fix. The card cannot tell which provider filled a value, and the documented contract is Open-Meteo's. Aligning NWS is a core change.
3. **DD3 names Lit's `svg` template for the `<svg>` element, and gives the SVG no size.** Check: contradictions (design against the drawing the spec needs). Lit's `svg` tag is for content inside an `<svg>`, and an unsized inline SVG overflows a 16 px cell. Binding `undefined` leaves an empty attribute where `nothing` removes it. **CONFIRMED.**
4. **The proposal and D2 say the cloud-only requirements widen to every row, but the spec adds parallel ones; "an added row" means nothing once archived; the main spec's "A null hour is blank" speaks only of shades.** Check: contradictions. **CONFIRMED.**

### 📌 Suggestions

5. **Matching Temperature and Dew point shades do not mean an hour near the dew point.** Check: assumption rows (D8). At 5.0 °C and 4.9 °C the shades differ; at 9.9 °C and 5.0 °C they match; below −5 °C both are the lightest. **CONFIRMED.**
6. **Test Seams names only the row-order tests, but three more `strip.test.ts` assertions depend on the row count.** Check: test seams. The row above the Moon up lane, the lines' `grid-row` and the strip's `grid-template-rows`. **CONFIRMED.**
7. **Plain language and precision: long sentences, lower-case "precipitation probability", and "between 0 and 360" for the arrow.** Check: plain language. **CONFIRMED** for the range. The casing follows the main spec, which writes "the moon altitude forecast" and "the sun altitude sensor" in lower case for a sensor and capitals for a row. The long sentences are mostly the fifteen-row lists, which a list reads no better in.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. specs: "The docs describe every row" asks for the lightest and darkest shade of each shaded row only.
2. design.md Context and Risks: the hour-before rule is the documented one, which Open-Meteo follows; a risk names NWS's hour-start fill as a core fix outside this change.
3. design.md DD3: the `<svg>` is written in Lit's `html` template, styled `display: block; width: 100%; height: 100%`, and an unused `data-shade` or `data-arrow` is bound to `nothing`.
4. proposal.md and brainstorm.md D2 describe the spec's structure as it is. specs: "an added row" becomes the named rows ("A Moon altitude or weather value fills its hour", "A missing sensor leaves its row empty", "Hovering over a cell shows its unit"); the separate null-hour requirement folds into a MODIFIED "A null hour is blank", which now says "every shade or arrow" and gains Seeing, Temperature and Wind direction scenarios.
5. proposal.md, brainstorm.md D8 and design.md Risks no longer say matching shades mean an hour near the dew point.
6. design.md Test Seams names the four row-count assertions in `strip.test.ts`.
7. specs: the arrow's rotation is "at least 0 and below 360".

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: required change 1.
2. Fixed: required change 2. The NWS fix itself is out of scope, for the reason under finding 2.
3. Fixed: required change 3.
4. Fixed: required change 4.
5. Fixed: required change 5.
6. Fixed: required change 6.
7. Fixed: required change 7. Casing and the list sentences declined, for the reasons under finding 7.
