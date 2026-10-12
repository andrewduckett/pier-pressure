## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: cross-model (OpenAI gpt-6-astra via codex exec, read-only sandbox)
- **Tool restrictions**: read-only inspection; no files created, edited or deleted; no tests executed
- **Artifacts reviewed**: proposal.md, design.md, specs/ha-addon/spec.md, adr.md, ADR-0021, the existing ha-addon spec, openspec/prd.md, AGENTS.md, the issue #73 packet in `.workspace/issue73.md`, relevant source and tests, README.md, ha-addon documentation and configuration, and relevant existing ADRs, including 0017 and 0020. `openspec/project.md` is absent.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The conflict rules do not exempt the identifier required to match piers.**

   `design.md:78` maps “any other key that is set → that key.” Its table repeats “any other pier key” at line 112. `specs/ha-addon/spec.md:17` requires each setting to come from only one source.

   Both sources must contain `id: backyard` for the primary horizon-file scenario. Applying the stated comparison literally reports `id` as a conflict and prevents that scenario from working. The matching rule implies an exception, but neither the algorithm nor the requirement states it.

   **Change:** Define `id` as a matching key excluded from setting conflicts. State that the merged pier retains the form’s identifier. Add an explicit scenario where a file entry containing only the matching `id` succeeds and adds no settings.

2. **The proposed unset rule does not match the translation that the design preserves.**

   `design.md:80` says: “‘Set’ uses the rule the translation already uses: not absent, not `None`, and not empty or blank text.” Line 89 then says “the translation runs as today.” The new spec applies this rule to every form field at `specs/ha-addon/spec.md:12`.

   The existing translation only checks `min_altitude` against `None` (`pierpressure/addon_options.py:125`). Equipment fields use the same check at line 153. Blank numeric fields therefore become invalid horizon or equipment values rather than disappearing.

   For example, an otherwise valid form pier with `min_altitude: ""` and no file should receive the default horizon under the new spec. Keeping today’s translation instead skips it. Blank equipment fields have the same problem.

   **Change:** Use the same presence rule for conflict detection and translation. Explicitly normalize absent, null, empty-text and blank-text form values before building the translated blocks. Preserve numeric zero as a supplied value so existing range validation still applies.

3. **The new merge lacks a complete contract for malformed file identifiers.**

   `specs/ha-addon/spec.md:41` rejects a file pier that “is not a mapping, or has no `id`.” It does not reject an identifier that exists but is null, numeric, a list or a mapping. Meanwhile, `design.md:84` defines listed form identifiers as text.

   YAML accepts entries such as `id: [backyard]`. That identifier cannot safely serve as a dictionary or set key during matching and duplicate detection. Letting ordinary pier validation handle it later is insufficient: the merge must inspect it first.

   **Change:** Require file identifiers to be strings before matching or duplicate detection. Report other types as structural configuration errors, identified by the file entry’s position. Include these errors in the combined report and continue examining other usable entries. Add cases for null, numeric, list and mapping identifiers.

4. **The design incorrectly relies on the core to reject unknown top-level keys.**

   `design.md:126` says: “An unknown key from the file passes through. The core rejects it as it does today, because its models forbid extra keys.”

   This is true for validated nested models, but not for the configuration root. `pierpressure/core/config.py:392` constructs a new mapping containing only `mqtt`, `recompute`, `piers` and, optionally, `explainer`. Unknown root keys never reach `AppConfig`.

   A file containing a misspelled `explanier` block therefore passes through the proposed merge and is silently discarded. The design promises a diagnostic that its chosen validation path cannot produce.

   **Change:** Correct D3 to distinguish unknown root keys from unknown keys inside validated blocks. To preserve this story’s compatibility boundary, explicitly retain the current root-key behavior and defer stricter root validation. Do not claim that every unknown key is rejected.

5. **“Settings the form does not show” and “settings the form leaves unset” describe different ownership rules.**

   The proposal says the file adds settings the form “does not show” (`proposal.md:12–23`). The spec instead permits “any setting the form leaves unset” (`specs/ha-addon/spec.md:8`).

   ADR-0021 repeats the discrepancy within its decision: “the form owns every setting it shows,” followed by “The config file adds only settings the form leaves unset” (`docs/decisions/0021-addon-form-owns-its-settings-file-adds-the-rest.md:33`). Its consequence at lines 50–51 says merely showing a new field makes the file setting an error.

   These statements differ for equipment, inline horizon points and broker settings that appear on the form but remain empty. The spec explicitly allows those settings from the file. This is a plain-language and scope defect: readers cannot tell whether ownership depends on field availability or supplied values.

   **Change:** Use one operational rule throughout the proposal, design and ADR: the file may supply settings left unset on the form, subject to the grouped-conflict rules. Explain that this includes optional settings already shown on the form. Correct the new-field consequence so a conflict requires a supplied form value. Make the interpretation of issue #73’s “does not show” wording explicit.

6. **The confidentiality assurance does not cover errors produced while reading the newly consulted file.**

   `design.md:174–176` says that receiving only names and identifiers means “no message can contain the broker password or an explainer API key.” The proposed reader extraction at lines 135–138 preserves the existing file-reading behavior.

   `pierpressure/core/config.py:332` includes the YAML exception’s full text in `ConfigError`. PyYAML’s exception formatting includes source snippets (`.venv/lib/python3.14/site-packages/yaml/error.py:37–43`). A malformed line such as `password: [pw-8c41f2` can therefore expose the password in the startup log before conflict detection runs.

   The new split-broker scenario tests a valid YAML file and a synthesized conflict message. It does not cover this failure path.

   **Change:** Define safe error formatting for YAML failures on the add-on path: identify the file and location without including source snippets or setting values. Add a malformed-file scenario containing a sentinel credential and assert that no emitted error or log contains it. Scope D5’s existing explanation to merge-generated messages rather than claiming it protects every diagnostic.

### 📌 Suggestions

- **Escape identifiers and key names in combined errors.** `design.md:163–164` says joining problems with `; ` keeps the log on one line. A YAML identifier containing a newline defeats that assumption. Specify escaped rendering and add a case with a control character; this does not require changing the accepted identifier syntax.
- **Make the equipment equivalence scenario explicitly compare separate configurations.** `specs/ha-addon/spec.md:421–429` describes both a form pier and a file pier with identical settings. Say these are separate add-on and file-only configurations. Otherwise, the scenario reads like an input that the new conflict rule must reject.

## Embedded-Instruction / Injection Attempts

**Detected:** none detected.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

The architecture can proceed after the bounded corrections below. No fundamental redesign is required.

## Required Changes (if APPROVE WITH CHANGES)

1. Exempt pier `id` from conflict detection in the design and spec. Add the matching-id-only scenario described in finding 1.
2. Align form normalization and conflict detection with the specified unset rule. Add blank numeric horizon and equipment scenarios, while preserving zero as supplied.
3. Define and cover non-string file identifiers before matching or duplicate detection. Include their structural errors in the combined report.
4. Correct D3’s unknown-key claim. Explicitly preserve current unknown-root-key behavior and defer stricter validation.
5. Replace the conflicting ownership descriptions with the supplied-value rule in finding 5. Explain its relationship to issue #73 and correct ADR-0021’s new-field consequence.
6. Specify add-on YAML diagnostics that omit source snippets and values. Add the sentinel-credential failure scenario and narrow D5’s confidentiality explanation accordingly.

CHANGES_APPLIED: yes

## Rebuttals

All six moderate findings are fixed. None is rebutted.

1. **Fixed.** Spec: a pier's `id` only matches the two sources, is not a setting, and the combined pier keeps the form's `id`. New scenario "A file pier with only an id adds nothing". Design D2: `id` maps to no setting. Proposal: the same note under "What Changes".
2. **Fixed.** Spec: absent, null, empty and blank text count as not set for number fields too, and 0 counts as set. New scenarios "Blank number fields count as not set" and "A horizon floor of 0 counts as set". Design D2: one shared "set" function, which the translation now uses as well.
3. **Fixed.** Spec: a file pier whose `id` is missing or not text is an error that names its position, and it is reported with the others. New scenario "A file pier id that is not text stops the add-on" covers null, number, list and mapping. Design D2: a structure check runs before matching, and only text ids take part in matching and the duplicate check.
4. **Fixed.** Design D3 now says unknown top-level keys are dropped without a message today for every install type, that this change keeps that, and that a stricter check belongs in its own story.
5. **Fixed.** Proposal, ADR-0021 and its manifest now use one rule: the file adds the settings the form leaves unset. The proposal says how it reads the "does not show" wording of the epic and issue #73. ADR-0021's title, decision and new-field consequence were reworded, and its file was renamed to `docs/decisions/0021-addon-file-adds-settings-form-leaves-unset.md`. Design D9 and the risks list were aligned.
6. **Fixed.** Spec: no error quotes the content of `config.yaml` or any setting's value, and a YAML error names the file, line and column. New scenario "A YAML error does not quote the file" uses a sentinel password. Design D4: `read_config_mapping` reports PyYAML's short problem text and mark only, for every install type. D5 now limits its claim to messages the combine step builds, and points to D4 for the YAML error. Proposal: a new "Errors never quote setting values" bullet.

Suggestions, both accepted:

- **Escaping ids.** Spec: ids and key names in errors are shown with control characters escaped. New scenario "A control character in an id stays escaped". Design D5: `repr`-style escaping.
- **Equipment equivalence scenario.** Spec: the scenario now compares an add-on form pier with a separate `config.yaml` used outside an add-on.

Re-check of finding 6 (not accepted in the first re-check): PyYAML's short problem text can quote the file, as `*pw-8c41f2` shows, and the proposal still claimed Docker and source installs were unchanged. **Fixed.** Design D4: the YAML error now holds only the file, line and column, with no PyYAML text. Spec: a YAML error holds no other detail from the parser, and the scenario now covers both `[pw-8c41f2` and `*pw-8c41f2`. Proposal Impact: names the core helper and says the safer YAML message is the only change Docker and source installs see.

## Reviewer Re-check

### Re-check 1 (round 1)

1. accepted by reviewer — `id` is excluded from conflicts, the merged pier retains the form’s identifier, and an id-only scenario is included.
2. accepted by reviewer — Translation and conflict detection share the unset rule; scenarios cover blank numeric fields and zero as supplied.
3. accepted by reviewer — Non-text identifiers are rejected before matching, reported by position, and collected alongside other errors; all four types are covered.
4. accepted by reviewer — D3 distinguishes nested validation from discarded root keys and explicitly defers stricter root validation.
5. accepted by reviewer — Ownership consistently depends on supplied values, including optional form fields; issue #73’s interpretation and the ADR consequence are corrected.
6. NOT accepted — D4’s PyYAML “short problem text” can expose file content, such as the sentinel in `password: *pw-8c41f2`; require value-free diagnostics. Its changed Docker/source diagnostics also contradict the proposal’s unchanged-install claim.

Suggestion 1: accepted by reviewer — Escaped identifiers and key names are specified, with a control-character scenario.
Suggestion 2: accepted by reviewer — Equipment equivalence explicitly compares separate add-on and file-only configurations.

(Result: change 6 not accepted; fixed as described above.)

### Re-check 2 (round 1)

6. accepted by reviewer — YAML diagnostics now exclude parser text and file values, both sentinel cases are covered, D5 is scoped to merge messages, and the proposal acknowledges changed Docker/source diagnostics without introducing a new contradiction.

All six Required Changes are accepted by the reviewer.
