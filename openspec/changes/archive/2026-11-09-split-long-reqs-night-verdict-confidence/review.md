## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family
- **Independent**: yes. The author is Claude; `gemini/gemini-3.8-flash` reviewed, through the t3 resolver (`"independent": true`).
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files
- **Commit reviewed**: `703389c`
- **Effort**: low, from design.md's scrutiny tier

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **A timeline requirement bundled two rules a later change would modify apart.** "Hours that only an alternate or a hidden variable covers add no timeline entry" held the alternate rule (ADR-0029) and the rule for a variable the timeline does not show (ADR-0030). A change to how alternates count would have to MODIFY both. Check: **CONFIRMED.** The two SHALL NOT sentences come from different records and each has its own scenario.
2. **A heading used a term the glossary does not define.** "Hidden variable" comes from a scenario's label, not from `openspec/glossary.md`, which says "a variable the timeline does not show". Epic #230 decision 5 asks headings to use the glossary's terms. Check: **CONFIRMED.**
3. **The tightened requirement sits at 498 characters.** "Variables the timeline does not show leave the document unchanged" names each such variable. A later change that adds one pushes it over 500, and once #245 adds `--strict` to the gate, that breaks the build. Check: **CONFIRMED** as a risk, already listed in design.md's Risks. The rebuttal says why the plan keeps it.

### 📌 Suggestions

4. **The added scenario asserts the timestamp format, not the top of the hour.** "An entry's time is emitted as a UTC timestamp" rests on `test_timeline_entry_time_is_aware_utc_at_whole_seconds`, which checks the UTC `Z` form. The producer, not the entry model, makes each time a top of the hour. Check: **CONFIRMED**, declined below.
5. **"Agreement changes no gate, score or verdict" has no gated scenario.** Its one scenario compares two scored verdicts. Check: **CONFIRMED**, declined below.
6. **Some carried sentences run past 30 words.** Check: **CONFIRMED**, declined below.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. Split "Hours that only an alternate or a hidden variable covers add no timeline entry" into "Hours only an alternate covers add no timeline entry" and "A variable the timeline does not show adds no timeline hour", one SHALL NOT and one scenario each (findings 1 and 2). Update the counts and the lists in brainstorm.md (D4, D16), proposal.md and design.md (Decisions 1, 3, 5 and 8).
2. In design.md's Risks, say that #245's strict gate fails the archive commit of a change that pushes a requirement over 500 characters (finding 3).

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** The delta now has the two requirements in Required change 1. Each has one scenario: "Hours only an alternate covers add no entry" and "Hours only a hidden variable covers add no entry". The count is now 22 ADDED requirements, and still 33 SHALL, 4 of them SHALL NOT. `openspec validate split-long-reqs-night-verdict-confidence --strict` passes.
2. **Fixed.** By the same edit: the new heading says "A variable the timeline does not show", as the glossary does. No ADDED heading uses "hidden variable". The scenario keeps its name, because scenarios move word for word.
3. **Rebutted, and the risk is noted (Required change 2).** Splitting off the last sentence needs a new SHALL and a scenario no document-level test backs (design.md Decision 2). A later change that adds such a variable must edit this list anyway. OpenSpec checks the main spec after archive, and once #245 adds `openspec validate --specs --strict` to `mise run check`, that change's archive commit fails until it splits the requirement. The warning cannot return unnoticed.
4. **Declined.** The scenario asserts how a top-of-the-hour time is emitted, which is the requirement's second clause. "The timeline spans the union of both providers' hours" already asserts one entry for every whole hour, at the producer seam.
5. **Declined.** The original requirement had the same coverage, and epic #230 adds a scenario only where a new requirement has none. The scenario's equal `verdict` covers the verdict value, which a failed gate decides.
6. **Declined.** Epic #230 keeps the original text. The plan rewords only so that each requirement reads on its own, or fits the limit.
