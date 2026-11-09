## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-3.8-flash, through the t3 resolver; the author is Claude)
- **Independent**: yes
- **Tool restrictions**: read-only; the resolver reported a clean working tree after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 2bae505

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **"Each pier on the form has four optional equipment fields" is 467 characters, so a later edit may push it past 500.** Check: **CONFIRMED, accepted.** No story in the epic touches it: #238 splits "The form sets each pier's equipment", a different requirement. A later change that needs more words can split off the save check, with a scenario of its own.
2. **"A pier list of the wrong shape in config.yaml stops the add-on" states three failure cases, but its one scenario tests only an `id` that is not text.** Check: **CONFIRMED, rebutted.** The original requirement had the same coverage: no scenario for a `piers` that is not a list, or for an entry that is not a mapping (`openspec/specs/ha-addon/spec.md`, the stop-case list of "The add-on combines the Configuration form with config.yaml"). Adding scenarios for them would add coverage the epic does not ask for (#230, Won't). `tests/test_addon_settings.py` `test_a_file_piers_that_is_not_a_list_is_an_error` (line 268) and `test_a_file_pier_that_is_not_a_mapping_names_its_position` (line 242) assert both cases.
3. **The line-and-column rule sits in "A config.yaml that is not a valid YAML mapping stops the add-on", but the scenario that asserts line 3 sits under "No combine error quotes config.yaml or a setting's value".** Check: **CONFIRMED, rebutted.** Epic #230 decision 2 keeps a scenario that tests two behaviors whole, under the requirement it fits best. Its name, "A YAML error does not quote the file", fits the no-quote rule. design.md Decision 4 records this placement, so a later change to either requirement can find it.

### 📌 Suggestions

4. **"The Configuration form declares the interval, the piers and the broker" names three settings, but lists only two.** Check: **CONFIRMED, declined.** The lead sentence names `mqtt` as the broker, and "The form's broker block has four optional fields" defines it (design.md Decision 5).
5. **Four ADDED requirements have sentences over 30 words.** Check: **CONFIRMED, declined.** The text stays as close to the original as each requirement allows, so its meaning cannot drift (D7). Shorter sentences are fair work for a later change that touches these requirements.
6. **Two ADDED requirements use the passive voice for path reading and escaping.** Check: **CONFIRMED, declined.** Both sentences keep the original's wording, and each opens with the add-on or "inside an add-on", which names the actor's scope.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE

## Required Changes (if APPROVE_WITH_CHANGES)

None.

CHANGES_APPLIED: n/a

## Rebuttals

1. Accepted: no story in the epic edits this requirement, and a later change can split off the save check.
2. Rebutted: the original had the same scenario coverage, and `tests/test_addon_settings.py` lines 242 and 268 assert the two cases without a scenario.
3. Rebutted: epic #230 decision 2 places a two-behavior scenario whole under its best fit, and design.md Decision 4 records it.
4. Declined: the lead sentence names `mqtt`, and the next requirement defines it.
5. Declined: wording stays close to the original so the meaning cannot drift (D7).
6. Declined: the original's wording, with the add-on named as the scope.
