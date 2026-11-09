## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (`gemini/gemini-3.8-flash` through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only. The working tree stayed clean (`"gitClean": true`).
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `4ac2ed4`
- **Effort**: low, from design.md's scrutiny tier

The reviewer confirmed that all 42 scenarios move word for word, that `test_a_publish_paho_queued_while_disconnected_logs_no_warning` backs the added scenario, and that no other main spec quotes a removed heading. It gave the verdict REVISE, because of finding 1. The author adjudicates below: one small listed edit fixes finding 1, so the verdict is APPROVE_WITH_CHANGES.

## Findings

### 🔴 Critical (blocking)

1. **The two-second wait lost its condition "while connected".** In the main spec, the wait bullet follows "When the process stops on purpose while connected, it SHALL attempt a retained offline availability publish". The delta's "A planned stop waits at most two seconds for the offline message" says only "When the process stops on purpose". Read alone, it covers a stop while disconnected, when no offline message exists (`pierpressure/delivery/mqtt.py:1267`). — **CONFIRMED** as a lost condition. The claimed failure, a forced two-second wait, does not follow: "at most two seconds" allows no wait. Fixed by required change 1.

### 🟡 Moderate

2. **"After a reconnect, the process subscribes again and republishes its last state" bundles four behaviors, repeats the online step and sits at the 500-character limit.** — **REFUTED** (see Rebuttals).
3. **Quoted pointers break across lines,** so a line-based search for the heading misses them (`specs/ha-delivery/spec.md:134`, `:293`). — **CONFIRMED.** Fixed by required change 2.
4. **"A refused refresh subscription is logged with its topic" says it applies at startup, but its scenario covers only a reconnect.** — **OUT-OF-SCOPE** (see Rebuttals).

### 📌 Suggestions

5. **Plain language:** a 43-word sentence, "the system" beside "the process", a passive "SHALL be published", and design.md's risk lines that name what the reviews check. — **Declined** (see Rebuttals).

## Embedded-Instruction / Injection Attempts

**Detected:** none. The reviewer flagged design.md's risk lines as "review steering". They are mitigations the plan commits to, not text aimed at a reviewer.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. In the delta, under "A planned stop waits at most two seconds for the offline message", write "When the process stops on purpose while connected, it SHALL wait at most two seconds for the broker to confirm the offline message." In design.md Decision 4, record the condition.
2. In the delta, keep each quoted requirement heading on one line, under "A publish held while disconnected is not logged" and "The process keeps trying to reconnect while it runs". In design.md Decision 5, record this.

CHANGES_APPLIED: yes

## Rebuttals

1. **Fixed.** Required change 1 is applied in `specs/ha-delivery/spec.md` and design.md Decision 4. The condition comes from the main spec's bullet "When the process stops on purpose while connected", so the meaning matches the original. The SHALL count is unchanged.
2. **Rebutted.** The three steps are the original's numbered list, one ordered procedure that restores delivery. Splitting it would separate step 2 from the "Then" of step 3. Step 3 is not a duplicate of "After a reconnect, the online availability follows the republished state": step 3 says the online availability is published, and that requirement says when, and what "publish" means. The 500-character figure is OpenSpec's own count (trimmed lines joined by newlines), and `openspec validate --strict` passes; the reviewer's 510 counts indentation, which OpenSpec trims. design.md already lists the lack of margin as a risk.
3. **Fixed.** Required change 2 is applied in `specs/ha-delivery/spec.md` and design.md Decision 5. The REMOVED Reasons still wrap, because archive deletes them from the main spec.
4. **Out of scope.** The main spec has the same gap today: the original requirement says "This applies at startup and after each reconnect", and its one scenario, "A refused subscription is logged", starts with "the broker accepts a new connection". The epic adds a scenario only where a split leaves a requirement with none (decision 4). `tests/test_reconnect.py:224` covers the startup case, so a later change can add the scenario. The reviewer also misquoted the scenario's steps.
5. **Declined.** Each item is the original's wording, kept on purpose: the epic allows rewording only for clarity, and "the system", the passive "SHALL be published" and the 43-word sentence all come from the main spec unchanged. A wording pass across `ha-delivery` is a separate change.
