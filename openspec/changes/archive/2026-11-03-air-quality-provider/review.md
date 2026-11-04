## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through `lets delegate review run`, resolver `t3`, effort medium)
- **Independent**: yes. The plan was written by Claude.
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was clean after the run.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, docs/decisions/0030-raw-input-variables-stay-out-of-the-verdict-document.md, relevant source files, at commit `2eaddea`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The spec and the URL could be paired wrongly** (check: contradictions). DD3 gave `OpenMeteoProvider` a `url` field independent of its `spec`. A caller that passes the air-quality spec without the air-quality URL sends `aerosol_optical_depth,pm2_5` to the forecast endpoint, which rejects them with HTTP 400. CONFIRMED.
2. **`Conditions.hours(variables)` left its default open** (check: test seams). `tests/test_conditions_model.py:64,70,128` call `hours()` with no arguments, and that file was not named as a seam. A default of "all variables" would let a bare call count raw variables' hours again. CONFIRMED.
3. **An all-null air-quality response reads as healthy** (check: assumptions). When the endpoint answers HTTP 200 with every value null, the fetch counts as `ok`, and no series is filled. CONFIRMED as behavior; OUT-OF-SCOPE as a fix. It is the existing rule for every provider (`openspec/specs/conditions/spec.md`, "Blank fields do not make a fetch fail").

### 📌 Suggestions

4. **Main specs still name two providers** (check: contradictions). The conditions scenario "The default order gives cloud to Open-Meteo and seeing to 7Timer!" and the night-dashboard requirement "one health chip for each weather source, Open-Meteo health and 7Timer! health" were written for a two-provider default. The reviewer also noted that `tests/test_conditions_provider.py:180` pins six Open-Meteo specs, which becomes seven. REFUTED as a plan defect; see the rebuttal.
5. **Two sentences exceed 30 words** (check: plain language): in ADR-0030's Context and in the night-verdict delta's timeline requirement. CONFIRMED.

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD3: choose the endpoint from the spec's key through an `ENDPOINTS` map, drop the separate `url` field, and name the `url` field as a rejected alternative.
2. design.md DD2: make `variables` required with no default, and say the existing callers pass their variables. Add `tests/test_conditions_model.py` to the reused seams.
3. design.md Risks: add the all-null response, and that health tracks whether the provider answered.
4. Split the long sentences in ADR-0030's Context and in the night-verdict delta's "The document carries an hourly timeline" requirement.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md DD3 now uses `ENDPOINTS` keyed by provider key, like `MODELS`, and lists the `url` field as a rejected alternative.
2. Fixed: design.md DD2 makes the argument required and names the existing callers; the Test Seams section lists `tests/test_conditions_model.py`.
3. Fixed as a recorded risk in design.md. The rule itself stays: a fetch with blank values succeeding is a requirement for all providers, and the user asked for a health record of reachability.
4. Rebutted. The fill scenario gives its order explicitly in its WHEN, and the new default still starts `open_meteo`, `seven_timer`, so it stays true once archived. The dashboard requirement names its two chips, so it stays true too. A third chip would be a dashboard change no ledger row asked for, and the device page in Home Assistant already shows the new health sensor. The pinned count in `tests/test_conditions_provider.py:180` is a test the tasks update, not a plan defect.
5. Fixed: ADR-0030's Context is now five short sentences, and the night-verdict requirement splits its hour rule into four sentences.
