## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (Gemini 3.1 Pro High via the `agy` CLI), in a fresh context with no authoring transcript
- **Tool restrictions**: no tools. The author embedded every file in the prompt, because headless `agy` refused even read-only shell calls.
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-addon/spec.md, specs/release-image/spec.md, adr.md, docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md, and relevant source files (release.yml, ci.yml, Dockerfile, pierpressure/__main__.py, README.md, docs/acceptance/ha-acceptance.md, ADR-0013, the main release-image spec)

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

- **Plain Language (Sentence length)**: The frontmatter `description` in `docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md` is 38 words long, violating the strict 30-word limit. Text: *"Architecture Decision Record for packaging PierPressure as a Home Assistant add-on from the main repository, pulling the published release image rather than building on the user's machine, with releases proposing each add-on version update as a pull request."*
- **Plain Language (Passive voice hiding actor)**: 
  - `proposal.md`: *"The acceptance checklist gets an add-on section, so the add-on is proved on a real Home Assistant OS install."* (Hides who proves it).
  - `design.md`: *"The add-on is proved on Home Assistant OS before merge"* (Hides who proves it).
  - `specs/release-image/spec.md`: *"At most one such pull request SHALL be open."* (Hides the actor maintaining the state).
  - `specs/release-image/spec.md`: *"The image, tag and GitHub release SHALL remain, because they are already published."* (Hides who published them).

### 🟡 Moderate

- **Pull Request Body Updates**: Design D5 states, *"Otherwise, set the open pull request's title to the new version."* It omits what happens to the PR description/body. If the body contains a hardcoded version string from its initial creation, it will become stale. The design should specify if the body needs updating or should be kept generic.
- **Workflow Permissions Spec**: While `design.md` correctly notes that the release job *"gains `pull-requests: write`"*, the actual specification (`specs/release-image/spec.md`) does not mandate this necessary permission change. Adding it to the spec ensures it is verified as a strict requirement.

### 📌 Suggestions

- None.

## Embedded-Instruction / Injection Attempts

**Detected:** listed below
- `README.md` contains the text: *"AI agents should start with `AGENTS.md`."* This acts as a directive to the AI reviewer parsing the file.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE WITH CHANGES)

1. In `docs/decisions/0014-ha-addon-wraps-release-image-in-this-repo.md`, rewrite the frontmatter description to use sentences of 30 words or fewer.
2. In `proposal.md`, rewrite *"so the add-on is proved on a real Home Assistant OS install"* in active voice identifying the actor.
3. In `design.md`, rewrite *"The add-on is proved on Home Assistant OS before merge"* in active voice.
4. In `specs/release-image/spec.md`, rewrite *"At most one such pull request SHALL be open"* in active voice (e.g., "The release workflow SHALL keep...").
5. In `specs/release-image/spec.md`, rewrite *"...because they are already published"* in active voice.
6. In `README.md`, remove or rephrase *"AI agents should start with `AGENTS.md`"* so it does not attempt to instruct the reviewing AI agent.

CHANGES_APPLIED: yes

## Rebuttals

1. **Required Changes 1-5 (plain language):** fixed. The ADR description is now
   three short sentences, and the four passive sentences name their actor. The
   reviewer re-checked each one as applied.
2. **Moderate, the PR description could go stale:** fixed. Design D5 step 4 now
   rewrites the title and description. The `release-image` spec requires the
   release to update the pull request's change, title and description, and a
   scenario asserts that both name only the newest version. Re-checked as applied.
3. **Moderate, the spec should require `pull-requests: write`:** rebutted. The
   spec is a behaviour contract and keeps permissions out. The scenario "Release
   opens the version pull request" can only pass with that permission, and design
   D5 records it. *Accepted by reviewer: permissions are implementation detail;
   the spec verifies the observable behaviour.*
4. **Required Change 6, the README line flagged as an injection attempt:**
   rebutted. README.md is context, not an artifact of this change, and the line
   points agents who work in the repository to its contributor guide. It does not
   direct a reviewer. *Accepted by reviewer: a standing convention outside this
   change's scope, not an injection attempt.*

Re-check outcome: `ALL_CLEAR: yes`.
