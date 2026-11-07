## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver t3, effort low)
- **Independent**: yes. The author is Claude; the reviewer is Gemini. `lets delegate` exited 5 ("the session stopped to ask", thread `cbb65653-c12f-4101-b529-3b30573dc20b`) and left the raw file empty, though the review had finished. The findings were recovered from that thread's final message.
- **Tool restrictions**: read-only: plan mode, no file writes
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `2a68c7d`

## Findings

### 🔴 Critical (blocking)

1. **The outline has no stroke width, and the lit part paints over it** (design.md DD3). SVG's default `stroke-width` of 1 user unit is a whole moon radius in this viewBox, so the outline would swallow half the face. Drawn under the lit part, a thin outline would still lose its inner half on the lit limb. Check: Contradictions, Geometry. **CONFIRMED.**
2. **Conditional SVG fragments written with Lit's `html` tag are not SVG elements** (design.md DD3). A nested `html` fragment holding `<circle>` or `<path>` is parsed as HTML, so a browser paints nothing, while the test DOM still finds the elements and every test passes. Check: Test seams. **CONFIRMED**: `card/src/pierpressure-card.ts:1` imports only `html`; `renderArrow` works because its whole `<svg>` is one literal.

### 🟡 Moderate

3. **Wrapping the verdict `<dl>` breaks an existing test** (design.md DD4, Test Seams). `card/test/messages.test.ts:226` expects the darkness note's previous sibling to be a `DL`. Check: Test seams. **CONFIRMED.**
4. **The Moon section has no horizontal layout** (design.md DD4). A block section stacks the SVG above its `<dl>`, so the times are not beside the drawing as #187 asks, and the test DOM cannot catch it. Check: Contradictions, Scope. **CONFIRMED.**
5. **The terminator requirement contradicts `new`, `full`, a quarter, the 0 and 1 ends, and the state before Home Assistant arrives** (spec, "The moon drawing lights the illumination's share of the disc" and "The Moon section shows only with the verdict"). A quarter has a straight terminator; a `waxing crescent` at 0 would draw a zero-width path. Check: Scenario testability, Contradictions. **CONFIRMED.**
6. **D7 ties the lit side to Home Assistant's latitude, and the doc scenario does not check the caveat** (brainstorm D7, spec docs requirement). A remote pier in the other hemisphere shows the moon mirrored, and the doc test would pass if the page dropped the caveat. D5, D13 and D14 are marked `Assumption` though the repo supports them. Check: Assumption rows. **CONFIRMED** for the doc gap, the unsupported rows and the limitation. The missing card override is **OUT-OF-SCOPE**: see Rebuttals.

### 📌 Suggestions

7. **Plain language and accuracy** (all artifacts). Several sentences exceed 30 words; brainstorm.md and design.md say the Verdict sensor's attributes are the whole document, though README.md:467 says they omit `timeline`; the Moon section has no accessible name. Check: Plain language. **CONFIRMED.**

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD3: draw the outline last, as `<circle r="1" fill="none">` with `stroke-width="0.08"`; give the unlit disc and the lit part no stroke.
2. design.md DD3: build the SVG's child layers with Lit's `svg` tag, and have the tests check each layer's `namespaceURI`.
3. design.md Test Seams and DD4: name the `messages.test.ts` note-position test as one to update; make `.moon` a centred flex row with `aria-label="Moon"`; check both flex rules through `cardStyles()`.
4. spec and design.md DD2: scope the terminator requirement to phases other than `new` and `full`; say the terminator is straight at 0.5 and curved otherwise; map illumination 0 to no lit part and 1 to the whole disc; add the state before Home Assistant arrives to "The Moon section shows only with the verdict".
5. brainstorm.md, spec and design.md Risks: cite evidence for D5, D13 and D14; state the other-hemisphere limitation on D7 and in design.md's risks; make the docs requirement a bullet list in active voice that names the limitation; add right, left and Home Assistant to its scenario.
6. brainstorm.md and design.md Context: say the Verdict sensor's attributes hold every key except `timeline`; split the longest sentences.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md DD3 now draws three layers, with the outline last at `stroke-width="0.08"`.
2. Fixed: design.md DD3 now names Lit's `svg` tag and a `namespaceURI` check in the tests.
3. Fixed: design.md Test Seams names `messages.test.ts` as an existing test to update, to follow `.summary`.
4. Fixed: design.md DD4 makes `.moon` a centred flex row, named `Moon`, with both flex rules checked through `cardStyles()`.
5. Fixed: the spec's terminator requirement now covers only phases other than `new` and `full`. It says the terminator is straight at 0.5, and it draws 0 and 1 as unlit and fully lit, with two new scenarios. "The Moon section shows only with the verdict" covers the state before Home Assistant arrives, with a scenario. design.md DD2 maps 0 and 1.
6. Fixed in part, rebutted in part. D7 and design.md's risks now state that a pier in the other hemisphere from Home Assistant shows the moon mirrored. The docs requirement names it, and its scenario checks right, left and Home Assistant. D5, D13 and D14 now cite evidence. A card option to override the hemisphere is not added: #187's scope is a drawing from the document's moon fields, and the brainstorm ruled out new card options. The card cannot know the pier's hemisphere without a new document field, which #187 rules out ("out: any new field in the document").
7. Fixed: brainstorm.md and design.md now say the attributes hold every key except `timeline`. The section has `aria-label="Moon"`. The docs requirement is a bullet list. The longest sentences in design.md DD3 and DD4, the proposal and the spec are split.
