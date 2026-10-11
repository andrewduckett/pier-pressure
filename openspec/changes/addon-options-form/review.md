## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model — OpenAI Codex CLI 0.159.3, model `gpt-6-sol`, reasoning effort medium. (The reviewer's own label said "fresh-context subagent": it tried to launch a further CLI from inside its sandbox, which failed, and then wrote the review itself. The run log confirms `gpt-6-sol` wrote it.)
- **Tool restrictions**: read-only: view, grep, glob only
- **Artifacts reviewed**: `openspec/changes/addon-options-form/proposal.md`, `design.md`, `specs/ha-addon/spec.md`, `adr.md`; `docs/decisions/0020-addon-form-translated-to-config-file-shape.md`; relevant current specifications, decisions, add-on files, application code, and tests. GitHub issues #67 and #69 were not read.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **Broker recovery advice will be wrong for form users.** The proposal says a populated form makes the service use “only the form” (`proposal.md:29–34`), and the spec says it “SHALL NOT read settings from `config.yaml`” (`specs/ha-addon/spec.md:37–45`). Existing Supervisor errors advise users to “set mqtt.host in config.yaml” (`pierpressure/supervisor.py:41–45,112–116,137–149`), as does rejected-login advice (`pierpressure/__main__.py:50–52`). Editing that file while form piers remain will not resolve the failure.

2. **The bad-pier scenario lacks a reachable form input.** The design says the Supervisor rejects an out-of-range coordinate when the user saves and requires every pier field (`design.md:18–20,131–147`). The spec nevertheless starts with a saved form whose pier fails the same validation (`specs/ha-addon/spec.md:87–92`). Name an input the Supervisor accepts but `PierConfig` rejects, or describe this as a malformed saved-data test.

3. **ADR-0020 obscures the current file fallback rule.** “The config file stays available to add-on users for settings the form cannot hold” (`docs/decisions/0020-addon-form-translated-to-config-file-shape.md:38–40`) can imply that file settings apply alongside form piers. This change ignores the whole file when the form lists a pier (`proposal.md:29–31`; `design.md:168–174`).

### 📌 Suggestions

1. **Check for a stale pier after switching sources.** The spec says the current run publishes `backyard` only (`specs/ha-addon/spec.md:79–85`), while the README describes retained MQTT messages (`README.md:188–194`). Verify whether a previously published `roof` entity remains visible, and document cleanup if needed.

2. **Make the live form check repeatable.** Record the Home Assistant version and acceptance steps for the real-instance check proposed in `design.md:164–167`.

3. **Plain language:** The proposal and `adr.md` are structured and readable; no material length, passive-voice, filler, or terminology issue was found. The design’s risk entry at `design.md:168–171` combines a condition, consequence, and future work; split it for easier scanning. The spec sentence beginning “When the service uses the form, it SHALL take the broker’s host...” (`specs/ha-addon/spec.md:43–45`) exceeds 30 words; shorten it and state the source rule directly. ADR-0020’s practical examples explain its nesting limit, subject to the ambiguity in moderate finding 3.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. Specify and test broker failure advice that works when form piers cause the file to be ignored.
2. Make the bad-pier scenario reachable or identify it as malformed saved-data testing.
3. Clarify in ADR-0020 that users who need file-only settings must also configure their piers in the file until the later merge change.

CHANGES_APPLIED: yes

## Rebuttals

- **Moderate 1 — fixed; accepted by reviewer after re-check 2.** The delta spec adds a rule: on the form path, a broker error says `config.yaml` is not read while the form lists piers, and does not tell the user only to set `mqtt.host` in the file. A new scenario, "A form user's broker error does not point only to the file", covers it. The design's risks section says how: `load_app_config` adds a note to each broker error on the form path, including the rejected-login advice. *Re-check 1:* the reviewer did not accept this, because `load_app_config` runs before a login can be rejected. The design now splits the fix: `load_app_config` notes `SupervisorError`s, and `main` passes the form source to `build_delivery_and_explainer`, which picks login advice for form users. *Re-check 2:* accepted by reviewer — "the design now passes the form configuration source to the delivery adapter, where rejected logins are handled at connection and reconnection time."
- **Moderate 2 — fixed; accepted by reviewer** (re-check 1: the scenario names malformed saved values and why the service still checks them). The scenario is now "A bad pier in the saved form values is skipped", with a latitude of 95. It says that the Supervisor normally refuses this value, and that the service still checks each pier.
- **Moderate 3 — fixed; accepted by reviewer** (re-check 1: the decision now says the form and the file are exclusive). ADR-0020 now says that at first the service uses the form or the file, never both, and that a user who needs a file-only setting lists their piers in the file too.
- **Suggestion 1 — declined.** A retained entity for a pier that is no longer configured is existing behaviour. Removing a pier from `config.yaml` has the same effect today. Cleaning up such entities is outside this story.
- **Suggestion 2 — accepted.** tasks.md will record the Home Assistant and Supervisor versions and the steps for the live form check.
- **Suggestion 3 — applied.** The long spec sentence about the broker is split. The design's first risk entry is split into condition and mitigation.