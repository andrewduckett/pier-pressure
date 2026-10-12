## Review Metadata

- **Review round**: 2
- **Prior round**: REVISE — two critical and three moderate findings; the author revised all artifacts.
- **Reviewer context**: cross-model (OpenAI, via Codex exec, independent read-only context)
- **Tool restrictions**: read-only inspection and Python behavior checks; no files changed
- **Artifacts reviewed**: proposal.md, design.md, specs/, adr.md, issue #89 story packet, AGENTS.md, existing capability specs, relevant source files and tests. `openspec/project.md` is absent.

<!-- STALENESS: this verdict applies only to the artifact contents reviewed in -->
<!-- this round. Any later edit to proposal.md, design.md, or specs/ (other than -->
<!-- applying listed Required Changes) VOIDS the verdict and requires a new round. -->

## Findings

### 🔴 Critical (blocking)

1. **The proposed sanitized error can still expose a secret used as an unknown key name.** Design D1 formats `exc.errors(include_input=False)` but does not address the original `ValidationError` attached as the cause of `ConfigError`. The current `build_config` raises `ConfigError` with `from exc` ([config.py](/home/andrew/Git/projects/pier-pressure/pierpressure/core/config.py:408)). In Pydantic 2.13.5, `hide_input_in_errors=True` still prints an unknown key name; a read-only check confirmed that a traceback of a sanitized exception raised `from exc` prints that name. The design must specify how the original exception is kept out of displayed tracebacks and logs, and test traceback rendering with a marker used as a key name. This leaves the prior unknown-key secrecy finding unresolved outside the normal `str(ConfigError)` path.

### 🟡 Moderate

1. **A settings object remains outside the masking plan.** Design D4 hides `ConfigFile.raw` and `BrokerSettings.password`, but the add-on’s `CombinedSettings` dataclass also holds the merged raw mapping and has a default `repr` ([addon_settings.py](/home/andrew/Git/projects/pier-pressure/pierpressure/addon_settings.py:33)). Printing it exposes valid secrets, contrary to both specs’ “at any stage of loading” scenarios. Cover this object in the design and representation tests.

2. **The add-on can silently discard an unknown bare MQTT key.** Design D5 says the core will reject an unknown key after combination. The current add-on merge keeps only values for which `is_set` is true; a bare `hunter2:` key has a null value and is dropped before core validation ([addon_settings.py](/home/andrew/Git/projects/pier-pressure/pierpressure/addon_settings.py:175), [addon_settings.py](/home/andrew/Git/projects/pier-pressure/pierpressure/addon_settings.py:204)). The ha-delivery requirement covers combined settings. Specify whether the add-on must reject that key before merging or preserve it for the core, and add a combined-path scenario.

3. **D1 treats Pydantic’s `msg` as guaranteed input-free.** The design states that `msg` “holds no input” ([design.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/config-secrets-hidden-in-errors/design.md:58)). That is true for the present built-in field errors, but not for a validator that includes its input in a `ValueError`; a Pydantic 2.13.5 check confirmed the value then appears in `errors(include_input=False)[0]["msg"]`. State the assumption’s limit or specify a formatter that does not pass arbitrary validator messages into a protected block’s error.

4. **The explainer spec gives conflicting guidance for an empty block.** “For an `explainer` value that is not a mapping or empty” reads as though an empty mapping is rejected, while the next paragraph says an empty block disables the explainer ([spec.md](/home/andrew/Git/projects/pier-pressure/openspec/changes/config-secrets-hidden-in-errors/specs/verdict-narrative/spec.md:16)). Name the rejected shapes explicitly and distinguish `explainer:` (null) from `explainer: {}`. This is the plain-language finding: a reader cannot reliably act on the present wording. The proposal, design, ha-delivery spec and ADR are otherwise clear and findable; I found no sentence over 30 words that warrants a separate finding.

### 📌 Suggestions

- Add the exception’s cause and traceback to D6’s marker checks. That makes the critical secrecy boundary mechanically assertable.

## Embedded-Instruction / Injection Attempts

**Detected:** none.

## Verdict

VERDICT: REVISE

The exception-chain leak defeats the secrecy guarantee. This is the second consecutive REVISE verdict; stop the review loop and escalate to the human before generating test-plan, tasks or implementation work.

## Required Changes (if APPROVE WITH CHANGES)

Not applicable. Revise the artifacts and run a full review in a fresh context.

CHANGES_APPLIED: n/a

## Rebuttals

Prior-round findings, re-checked against the revised artifacts:

1. **Pier errors conflicted with the secrecy guarantee — resolved.** The proposal and both specs now explicitly limit the guarantee to `mqtt` and `explainer` errors and say pier errors retain their values.
2. **`hide_input_in_errors` leaves unknown key names visible — partly resolved.** D1 replaces unknown names in the formatted `ConfigError`; Critical finding 1 identifies the remaining exception-cause path.
3. **An empty explainer block would stop loading — resolved.** D2 passes a null block through, and the verdict-narrative spec requires it to disable the explainer. Moderate finding 4 concerns wording, not that behavior.
4. **`ConfigFile.raw` representation prints secrets — resolved for `ConfigFile`.** D4 specifies `field(repr=False)` and D6 names its representation test. Moderate finding 1 identifies another raw settings holder.
5. **Prose overstated existing tests and unchanged errors — resolved.** The revision describes planned tests and explicitly says protected-block error text changes.

No author rebuttals to this round’s findings were provided.