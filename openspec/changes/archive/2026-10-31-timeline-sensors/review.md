## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family. Gemini 4 Argon (gemini family), as a T3 child task on the antigravity provider, sharing this worktree. `lets delegate review run` could not open an antigravity session, so the task ran through T3's `delegate_task` directly.
- **Independent**: yes. The plan was written by the claude family.
- **Tool restrictions**: read-only by instruction; `git status --porcelain` was empty before and after.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit 45c605c
- **Raw output**: `.workspace/timeline-sensors-review-raw.md` (not committed)

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **An exact message pin breaks.** Check: test seams. `test_existing_entities_publish_the_same_topics_and_payloads` (`tests/test_rank_targets.py:277`) asserts every non-rank, non-Cloud-cover message `publish_verdict` sends. The eight new sensors fail it, and the design did not name the change. **CONFIRMED.**
2. **DD8 breaks two docs guards and misses stale text.** Check: contradictions. Widening the README's Cloud cover topic row breaks `test_readme_lists_the_cloud_cover_topics` (`tests/test_timeline_docs.py:72`). It also contradicts brainstorm D10, which asks for a new topic row. DD8 missed "Delivered on the Cloud cover sensor" (`README.md:259`) and "starting with Cloud cover" (`docs/night-timeline.md:62`). `<key>` already names a provider in the `mqtt.py` topic table. **CONFIRMED.**
3. **Test details collide with the model.** Check: test seams. `sun_altitude` and `moon_altitude` are never null (`pierpressure/core/model.py`, `TimelineEntry`), so a null-value test cannot run over all eight keys. `Quality` is an `Annotated` type, so a naive type check fails. Bare `SENSOR_SCHEMA` allows any extra key, while `tests/test_cloud_cover.py:96` closes it. **CONFIRMED.**
4. **The altitude sensors' limits are understated.** Check: assumption rows (D8). The altitudes go unknown when no weather source returned the current hour (`pierpressure/core/producer.py:84` builds entries only from source hours). A start-of-hour altitude can trail the live sky by up to one hour plus one recompute interval, not just one interval. **CONFIRMED.**

### 📌 Suggestions

5. **The recorder note misses a second pier.** Each pier has its own nine entities, and the literal example lists one pier's. The reviewer also raised the larger message count per publish and replay. **CONFIRMED** for the recorder note. The message count is declined: about seventy small retained messages per pier, once per recompute interval, which paho queues.
6. **Terms and sentence length.** Check: plain language. Once merged beside Cloud cover, "each timeline sensor" in the delta reads as covering Cloud cover too, though its scenarios cover the eight new keys only. The proposal said "forecast sensors" for the same things. Several sentences ran over 30 words, and two used a passive that hid the actor. **CONFIRMED.**

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md Test Seams and Blast radius: name the `tests/test_rank_targets.py` pin and its widened filter, and pin Cloud cover and the eight new sensors in `tests/test_timeline_sensors.py`.
2. design.md DD8: add a README topic row for the new sensors and keep Cloud cover's literal topics; write the removal-loop entries out without brace expansion; update `README.md:259` and `docs/night-timeline.md:62`; use `<var>` in the `mqtt.py` topic table.
3. design.md Test Seams and DD4: run null-value scenarios over the six nullable keys; unwrap `Annotated` in the field-type test; validate against the closed `SENSOR_SCHEMA`.
4. spec and design.md DD8: state that an altitude state can trail the live sky by up to one hour plus one recompute interval, and that every sensor, the altitudes included, shows unknown when no source returned the current hour.
5. spec and proposal.md: say "further timeline sensor" in the delta; say "timeline sensors", not "forecast sensors", in the proposal; split the long and passive sentences the reviewer listed.
6. design.md DD8: the recorder note says each pier has its own nine entities.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md Test Seams, "An existing pin that must change", and the Blast radius line.
2. Fixed: design.md DD8, `README.md` and `mqtt.py` bullets.
3. Fixed: design.md Test Seams, "Test details", and DD4.
4. Fixed: spec requirement "A further timeline sensor's state is its variable's current-hour value" states the bound, and the missing-hour scenario names the altitude sensors. design.md DD8 and a new Risks entry cover the outage case.
5. Recorder part fixed in design.md DD8. Message volume declined, for the reason under the finding.
6. Fixed: the delta's requirement headings and texts say "further timeline sensor"; proposal.md says "timeline sensors"; the listed sentences are split. brainstorm.md D10 keeps "forecast sensors", because the user confirmed the ledger as written. The term there means the same nine sensors.
