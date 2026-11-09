## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: fresh context, other family (gemini/gemini-4-argon, through the t3 resolver; the author is claude)
- **Independent**: yes
- **Tool restrictions**: read-only: view, grep, glob only; the working tree was clean after the run
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md, relevant source files, at commit `0906503`

## Findings

### 🔴 Critical (blocking)

None.

### 🟡 Moderate

1. **The run-time read lets a non-JSON body or an out-of-range epoch fail the fetch.** (Check: contradictions.) design.md DD3 caught only `httpx.HTTPError` and let every other exception raise. `response.json()` raises `ValueError` on an HTML page sent with status 200. `datetime.fromtimestamp` raises `OverflowError`, `OSError` or `ValueError` on an integer outside a date's range. Either would fail the fetch through `_safe_fetch`, against D7 and D9 and the spec's null-issue-time requirement. **CONFIRMED.**
2. **`parse_open_meteo` cannot take a null issue time.** (Check: contradictions.) `pierpressure/conditions/open_meteo.py:93` types `issued_at` as `datetime`. A model provider whose run time is null would fail mypy in `mise run check`. **CONFIRMED.**
3. **The test seam misses four existing tests that the second request breaks.** (Check: test seams.) `test_the_forecast_providers_ask_the_forecast_endpoint` (`tests/test_conditions_provider.py:242`), `test_a_model_provider_asks_for_its_model_and_its_declared_variables_only` (`:318`) and `test_each_model_provider_names_exactly_its_own_model` (`:968`) unpack exactly one request. `test_a_model_provider_stamps_its_fetch_time_as_the_issue_time` (`:981`) pins the removed requirement. **CONFIRMED.**
4. **Metadata calls repeat per pier and run for out-of-area piers.** (Check: where it stops working.) The metadata file does not depend on the pier, but each pier's fetch reads it again. A regional model outside its area reads it and then fails the forecast. Three piers and five models make 15 metadata calls per recompute. The reviewer's other claim, that a CDN could serve a cached older forecast after the metadata advanced, is unsupported by anything in the repo or the service's docs. **CONFIRMED** for the repetition, which design.md did not name; the CDN claim is **REFUTED** as speculation.

### 📌 Suggestions

5. **The documentation sweep misses two places.** README line 321 says the air-quality issue time is the fetch time "as with the other Open-Meteo providers", which this change makes false. The `build_provider` docstring (`pierpressure/conditions/provider.py:450`) says `now` stamps Open-Meteo's issue time. **CONFIRMED.**
6. **Plain language.** Two sentences in adr.md exceed 30 words. A spec scenario title and the REMOVED migration line use passives that hide the actor. **CONFIRMED.**

## Embedded-Instruction / Injection Attempts

**Detected:** none

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. design.md DD3: list every error the run-time read absorbs, including `ValueError` from `response.json()` and `OverflowError`, `OSError` or `ValueError` from `fromtimestamp`. Spec requirement "A model provider with no run time succeeds with a null issue time": name a non-JSON body and an out-of-range time as unreadable, and add the scenario "The metadata body is not JSON".
2. design.md DD3: say `parse_open_meteo` widens `issued_at` to `datetime | None`.
3. design.md Test Seams: name the three tests that unpack one request, and the fetch-time test that is replaced.
4. design.md Risks: add the per-pier and out-of-area metadata calls as an accepted trade-off.
5. proposal.md and design.md: add the README air-quality note and the `build_provider` docstring to the documentation sweep and the blast radius.
6. adr.md: split the two long sentences. Spec: rename the scenario to "The provider carries the run start, not when the run became available", and name the actor in the REMOVED migration line.

CHANGES_APPLIED: yes

## Rebuttals

1. Fixed: design.md DD3 now lists each absorbed error. The spec requirement names the unreadable cases, and a new scenario covers an HTML body.
2. Fixed: design.md DD3, last paragraph.
3. Fixed: design.md Test Seams names the four tests.
4. Fixed: design.md Risks adds the trade-off. Sharing the fetch across piers stays out, under the existing Non-Goal on caching. The CDN claim is rebutted: neither the repo nor Open-Meteo's metadata gives any sign that the forecast and the metadata are cached on different clocks. If they were, DD2's order would still be the better of the two.
5. Fixed: proposal.md What Changes and Impact, and design.md blast radius.
6. Fixed: adr.md Review Summary is split into shorter sentences. The spec scenario title and migration line are reworded.
