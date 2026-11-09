## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario (#232, design Context). Four of the split-out behaviors have no scenario of their own (D5, D6, D7).
- The main spec has 7 requirements and 30 scenarios. The 5 long requirements hold 25 of the scenarios, 29 SHALL statements (two of them SHALL NOT) and 1 MAY.
- This branch stacks on `split-long-reqs-horizon-mask` (PR #250). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-horizon-mask`.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement states one behavior in no more than 500 characters. The longest, "The verdict gets one framing sentence about the top pick", is 492 by OpenSpec's own count, and strict validation accepts it.
- After archive, the spec holds every one of its 30 scenario blocks word for word, plus the 4 added on purpose.

**Non-Goals:**

- Reordering requirements inside the main spec.
- Rewording the two catalog requirements, which are under the limit.
- Fixing the framing requirement's drift from the code (D9).
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-target-ranking --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=target-ranking`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved. Existing tests assert the 4 added scenarios, as Decision 2 names.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/target-ranking/spec.md`. No code, test or doc refers to a requirement heading (D2).

## Decisions

1. **One requirement per SHALL group, and keep a group whole when its scenarios test it as one.** The split follows the original's own sentences and bullets. Four groups stay together on purpose:
   - The two gate outcomes (never clears the mask, or clears it too briefly) stay in one requirement. They are two halves of one gate, and each has its own scenario under it.
   - The order by score and the top-10 bound stay in one requirement. Their one scenario, "The list is bounded and stably ordered", tests both.
   - The field-of-view fit's three rules (judged against the short edge, both extremes penalised, a mid-size band best) stay in one requirement. They describe one curve, and its scenarios test it as one.
   - The four conditions for adding a framing sentence, how the sentence names the pick, and where it goes in `reasons[]` stay in one requirement. Splitting off the placement would need a scenario that no test asserts (Decision 2).
   - Alternative: split each of these further and add scenarios. Every new scenario would repeat a THEN an existing one already asserts, or would have no test behind it.
2. **Add a scenario only where a behavior has none, and only one an existing test asserts.** Four behaviors need one (D3):

   | Added scenario | Under | Test that already asserts it |
   |---|---|---|
   | A circumpolar target's daytime transit falls before its window | A target's transit time is that day's meridian crossing | `tests/test_ranking_geometry.py` `test_circumpolar_daytime_transit_is_outside_the_window` (`geo.transit_time < geo.window_start` for NGC6543 over London) |
   | Target times carry no fraction of a second | Target times are UTC at whole-second precision | `tests/test_ranking_pipeline.py` `test_every_emitted_target_is_whole_second_and_scored` (window start, window end and transit time have `microsecond == 0`) |
   | The moon factor is neutral when the moon is down | The moon factor is neutral when the moon is down or dark | `tests/test_ranking_score.py` `test_moon_subscore_neutral_when_moon_down` (`moon_subscore(0.0, illumination=1.0, moon_up=False) == 1.0`) |
   | A target with a surface brightness carries the catalog magnitude | The ranking's brightness choice changes no carried value | `tests/test_ranking_pipeline.py` `test_targets_carry_the_raw_catalog_facts` (every target's `magnitude` equals the catalog's, rounded to the document's precision) |

   Each restates a SHALL the requirement keeps, so it adds no rule (epic decision 4).
   - Alternative: keep these behaviors inside a larger requirement. Each would push that requirement back past 500 characters, or bundle two behaviors again.
3. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "Higher-quality targets rank first" goes with "A target's score combines six factors". It also shows ordering, but its WHEN varies one factor, maximum altitude.
   - "An equipment change changes the ranking" goes with "Field-of-view fit is judged against the short edge". Equipment reaches the score only through that factor.
   - "A missing field-of-view factor drops rather than guesses", "A missing brightness factor drops rather than guesses" and "A target with neither brightness nor a framed size scores on geometry alone" go with "A factor contributes only when its inputs are known". Their AND, that the score is renormalised, is the next requirement's rule; their WHEN and first THEN are this one's.
   - "A geometry-only target can still reach the top of the range" goes with "Factor weights are renormalised over the contributing factors". It tests that renormalising keeps the full range.
   - "A pier without equipment gets no framing sentence" and "A NO-GO verdict gets no framing sentence" go with "The verdict gets one framing sentence about the top pick", whose conditions they test.
4. **Reword only so each requirement reads on its own** (D10):
   - Each new requirement names its subject again, such as "a target's observable window" or "the moon separation factor".
   - The six factors become one list with each factor's direction. The sub-rules that followed some factors (the moon's neutral case, how brightness is judged, how framing is judged, the oversize penalty) each become a requirement of their own. "The four geometry factors" is defined where it is used, in "A factor contributes only when its inputs are known", by naming the four.
   - "The sentence SHALL be the first of these that applies" and its numbered list become four requirements. Each states the condition that picks its sentence, including the precedence the list gave: frames-well comes first, larger-than and small apply only when the pick does not frame well, and fills-most applies when no other does. This is why the SHALL count goes from 29 to 33: one "SHALL be the first of these" becomes four "SHALL be" statements and one "SHALL take precedence". Nothing new is required.
   - The framing requirement's opening "When the pier has equipment" is dropped, because its third condition, "The pier has equipment configured", says the same. "naming it by its name, or its designation when it has no name" becomes "naming the top pick by its name, else by its designation".
   - "An object larger than the field of view SHALL be penalised progressively" gains "by the field-of-view fit", since it no longer sits under that factor's bullet.
5. **Keep the framing requirement's meaning, though the code has moved on** (D9). `pierpressure/core/ranking.py` `equipment_reasons` also adds "Top pick `<name>` is a bright target." for a bright pick. `pierpressure/core/producer.py` adds no top-pick sentence when the scored window is shorter than `MIN_USABLE_WINDOW`, and `tests/test_producer_targets.py` `test_a_window_not_worth_setting_up_for_carries_no_equipment_reason` asserts that. The requirement names neither. Fixing that changes what is required, which the epic rules out. The REMOVED **Reason** and the pull request report the drift so the maintainer can decide on a fix.
   - Alternative: fix the requirement here. That breaks epic decision 3 and mixes a behavior change into a text-only review.
6. **Headings use the spec's own words** (D11). No ADDED heading repeats one the delta removes or one the spec keeps.
7. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if any scenario of a removed requirement is left out or used twice.
8. **Accept archive's order.** The 23 new requirements land at the end of the spec, after the two catalog requirements. This is what the pilot chose (#231, design Decision 2), and the catalog requirements already come first.

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: target-ranking: 4 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count SHALL and MAY in the ADDED requirements: 33 SHALL (two of them SHALL NOT) and 1 MAY expected, against 29 and 1 in the originals (Decision 4). The plan review compares each original with its parts.
- [An added scenario states a rule the spec did not have] → Each one's WHEN and THEN restate only the SHALL of the requirement it sits under, and a test already asserts it (Decision 2). The pull request lists all 4.
- [A drifted requirement gets new headings, so it looks freshly agreed] → Its REMOVED **Reason** names the drift, and so does the pull request (Decision 5).
- [The framing requirement sits 8 characters under the limit, so any later wording change may push it over] → Accepted. A later change that touches it can split off the placement rule, with a test.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
