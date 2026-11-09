## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- Strict validation also rejects an ADDED requirement with no scenario, or with no SHALL or MUST in its prose. A MAY alone is not enough.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, in the delta's order.
- The 6 long requirements hold 27 scenarios, 55 SHALL (12 of them SHALL NOT) and 1 MAY. None uses MUST.
- Some sentences of the originals carry no SHALL: the list of hard gates, the definition of the atmosphere factor, "These are the only tuning knobs", the target field list after its first half, and the knob definitions. Each must sit in a new requirement that has a SHALL.
- Two originals state one behavior: the banded score says that with no seeing or transparency the atmosphere factor is 1 and confidence falls, and the degrading rule says missing seeing or transparency drops only its own contribution and lowers confidence.
- No spec quotes any of the 6 headings, and none of the 6 points to another requirement by its heading.
- This branch stacks on `split-long-reqs-night-verdict-window` (PR #263). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-night-verdict-window`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 36 new requirements states one behavior in no more than 500 characters.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 10 added on purpose.
- After archive, no quoted pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Splitting the other 8 long requirements in `night-verdict`. #244 does that.
- Editing the comments and docs that use the terms "hard gates", "banded score" and "ranked list" (proposal, Impact). The epic changes no code, test or doc.
- Reordering requirements inside the main spec.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-night-verdict-score --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=night-verdict`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, the pointer check from the earlier layers' tasks, which resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. Each added scenario rests on an existing test. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/night-verdict/spec.md`. Nothing reads requirement headings.

## Decisions

1. **One requirement per behavior, following the original's own sentences, paragraphs and bullets.** The parts are:

   | Removed | Added |
   |---|---|
   | Targets list is an ordered ranked list | Each target carries its identity, ranking and observing fields; Each target carries its catalog size, magnitude and surface brightness; The targets list is ordered by score and holds at most 10 targets; The targets list is always present, and empty when nothing is rankable; Target catalog values are emitted at a fixed precision |
   | Hard gates decide a NO-GO | A failed hard gate is the only cause of a NO-GO; A failed hard gate leaves the score null and names the gate; A selected night with no dark window fails a hard gate; The overcast gate fails when every part of the scored window with cloud data is overcast; The wind gate fails when the forecast gust exceeds a configured limit |
   | A banded score decides GO versus MAYBE | A gate-passing night gets a deterministic integer score from 0 to 100; The score is the product of four factors; A half-way score rounds to the even integer; The atmosphere factor rests on a clarity-weighted mean of each hour's quality; The score never exceeds the usable-sky term; GO needs a score at the go-threshold, cloud data and no cap; A brighter night never scores higher; More cloud never raises the usable-sky term times the atmosphere factor; The reasons explain the atmosphere factor |
   | The verdict degrades honestly when conditions are unavailable | A verdict is always produced when conditions are missing; Missing seeing or transparency drops only its own contribution; The hard gates come before the missing-cloud rule; A wind-gust limit that wind data does not fully cover is unavailable; An unavailable wind-gust limit caps the verdict at MAYBE; Entirely missing cloud data gives MAYBE with a score of 0 |
   | Optional pier tuning configuration | A pier has three optional tuning knobs and no others; An omitted go-threshold takes the system default; An omitted wind-gust limit disables the wind gate; The dew margin defaults to 4 °C, and 0 turns the dew line off; A negative or non-finite dew margin is a configuration error |
   | High, thin cloud is a distinct score penalty | High, thin cloud has a score penalty apart from total cloud; The high-cloud penalty has its own reason line; More high cloud never raises the score; The high-cloud penalty only shapes the banded score; The high-cloud penalty is weighted toward the usably clear hours; A missing high-cloud component drops its own contribution |

   These stay together on purpose:
   - The target field list runs to about 540 characters, so it splits after `moon_separation`. The three catalog fields that can be null go together, with the sentence that says filling them is additive.
   - The list of hard gates stays with "the only cause of a NO-GO", as one sentence that names all three. It keeps the original's meaning that there are exactly three. Each gate then has its own requirement.
   - The overcast gate keeps its two cases where it does not fire, no cloud data and an empty scored window. They say when that one gate fires.
   - The determinism sentence, "The same inputs SHALL yield the same integer score", joins the sentence that a gate-passing night gets an integer score. Both say what score a night gets, and each alone has no scenario.
   - The two caps and the threshold-0 rule stay with the `GO` rule. They say when a gate-passing night is `GO`.
   - The monotonicity caveat for the moon and high-cloud factors stays with "More cloud SHALL NOT raise", because it says where that rule stops.
   - The banded score's sentence that with no seeing or transparency the factor is 1 and confidence falls joins the degrading rule for missing seeing or transparency (D6). Both state one behavior. Its scenario, "Missing seeing and transparency leave the score at the usable-sky term", moves with it.
   - "The missing-cloud rule SHALL NOT apply to an empty scored window" joins "The hard gates come before the missing-cloud rule". Both say what the missing-cloud rule yields to. With the missing-cloud verdict it would run past 500 characters.
   - The wind cap splits in two: when the limit is treated as unavailable, and what that does to the verdict. Together they run to 503 characters.
   - Each knob's definition, from the original's bullet list, goes with the rule for omitting that knob. The list of knob names stays with "the only tuning knobs".
   - The dew margin's default and "a dew margin of 0 SHALL turn the dew line off" stay together: both say how the margin's value is read. The rejected values get their own requirement, since a scenario asserts them alone.
   - The reason why high cirrus is penalized stays with the penalty.
   - "This term is additive" goes with "only shape the banded score". Both say what the high-cloud term leaves unchanged.
2. **Where each scenario goes** (D3–D9). Each moves whole, under the requirement it fits best:
   - Targets: "Targets list is present and ordered when targets are rankable" with the identity, ranking and observing fields, since its first THEN line lists the fields; "Catalog values absent for an object are null on the target" with the catalog fields; "Targets list present and empty when nothing is rankable" with the always-present list.
   - Gates: "An unusable night is never NO-GO without a failed gate" with the only cause; "No dark window gates to NO-GO", "An all-night overcast dark window gates to NO-GO" and "Configured wind-gust limit gates to NO-GO" with their gates.
   - Score: "Better seeing and transparency never lower the score" with the product, since its last line asserts `0.7 + 0.3 × A`; "Good seeing and transparency cannot lift a mostly cloudy night" with the ceiling; "A score at or above the go-threshold with cloud data is GO" and "A score below the go-threshold is MAYBE" with the `GO` rule; "A bright moon up during darkness lowers the score" with the brighter night; "Clouding out a poor-atmosphere hour never raises the score" with more cloud; "The reasons explain an atmosphere factor built on partial data" with the reasons; "Missing seeing and transparency leave the score at the usable-sky term" with missing seeing or transparency (Decision 1).
   - Degrading: "A verdict is always produced despite missing conditions" with always produced; "A failed wind gate yields NO-GO even when cloud data is missing" with the gates first; "Partial wind coverage caps the verdict at MAYBE when a limit is configured" with the limit treated as unavailable, since it tests the "only for some of its hours" case; "Missing wind data caps the verdict at MAYBE when a limit is configured" with the cap; "Missing cloud data caps the verdict at MAYBE when gates pass" with entirely missing cloud data.
   - Tuning: "Omitted go-threshold uses the default", "Omitted wind-gust limit disables the wind gate", "Omitted dew margin is 4 °C" and "A negative or infinite dew margin is rejected" with their knobs.
   - High cloud: "High cirrus lowers the score with its own reason" with the penalty; "The high-cloud penalty never gates the night" with only shaping the score; "Missing high-cloud component drops the term without penalty" with the missing component.
3. **Add ten scenarios, each backed by an existing test** (D10). Each goes to a new requirement that no original scenario fits:
   - "Rankable targets are listed in score order, at most 10", under "The targets list is ordered by score and holds at most 10 targets". `test_list_is_bounded_to_top_n` and `test_list_is_ordered_by_score_then_id` (`tests/test_ranking_pipeline.py`) assert it.
   - "Target catalog values are rounded to two decimal places", under "Target catalog values are emitted at a fixed precision". `test_target_catalog_values_round_to_fixed_precision` (`tests/test_target_model.py`) asserts it with the same values.
   - "A wind-gated verdict names the wind in its reasons", under "A failed hard gate leaves the score null and names the gate". `test_wind_gust_over_limit_gates_to_no_go` (`tests/test_verdict_eval.py`) asserts it with the same limit and gust.
   - "Two runs on the same inputs give the same score", under "A gate-passing night gets a deterministic integer score from 0 to 100". `test_two_runs_are_byte_identical_offline` (`tests/test_determinism.py`) asserts it for a gate-passing night with an integer score.
   - "A score of 12.5 rounds to 12", under "A half-way score rounds to the even integer". `test_a_half_way_score_rounds_to_the_even_integer` (`tests/test_scoring.py`) asserts it with one clear hour of eight.
   - "An hour with only seeing takes its quality from the seeing", under "The atmosphere factor rests on a clarity-weighted mean of each hour's quality". `test_atmosphere_mean_uses_the_one_term_an_hour_carries` (`tests/test_scoring.py`) asserts `A` is 0.4.
   - "A pier configuration sets all three tuning knobs", under "A pier has three optional tuning knobs and no others". `test_go_threshold_and_max_gust_load_from_yaml` and `test_dew_margin_loads_from_yaml` (`tests/test_config.py`) assert the three values, in two configurations.
   - "A 60% high-cloud penalty has one reason line of its own", under "The high-cloud penalty has its own reason line". `test_high_cloud_reason_is_a_distinct_line_when_the_penalty_bites` (`tests/test_scoring.py`) asserts both lines.
   - "Rising high cloud on a clear night never raises the score", under "More high cloud never raises the score". `test_assemble_score_is_monotonic_non_increasing_in_high_cloud` (`tests/test_scoring.py`) asserts it with the same five levels.
   - "High cloud over overcast hours adds no penalty", under "The high-cloud penalty is weighted toward the usably clear hours". `test_high_cloud_penalty_ignores_overcast_hours_via_clarity_weight` (`tests/test_scoring.py`) asserts a penalty of 0.2.

   Alternative: join each of these requirements to a neighbor so that an original scenario covers it. Each join runs past 500 characters, or puts two behaviors under one heading.
4. **Reword only so each requirement reads on its own** (D14):
   - "The hard gates are:" and its three bullets become one sentence, "There are three hard gates: no dark window, the overcast gate and the wind gate", and one requirement per gate. Each gate's requirement says it "SHALL fail" in the bullet's case. That adds three SHALL.
   - The wind bullet's "only when a wind-gust limit is configured for the pier" becomes "The wind gate exists only when a wind-gust limit is configured for the pier".
   - "The atmosphere factor rests on a per-hour quality `a`" becomes "SHALL rest", so that requirement has a SHALL.
   - "A value exactly half-way between two integers" becomes "A scaled score exactly half-way between two integers", because the sentence no longer follows the one that scales and rounds the score.
   - "When no hour carries seeing or transparency, the factor is 1" names "the atmosphere factor", because it now sits in another requirement.
   - "Each element SHALL be a structured target object" names "Each element of `targets`". The second half of its field list opens "Each target object SHALL also contain", and "Filling this list" becomes "Filling the `targets` list". "The list SHALL be ordered" names "The `targets` list".
   - "A pier configuration MAY set three tuning knobs:" keeps its MAY and lists the knobs by name. "These are the only tuning knobs" becomes "These SHALL be the only tuning knobs", so that requirement has a SHALL.
   - Each knob's bullet becomes a sentence in its own requirement: "The go-threshold is an integer from 0 to 100", "The wind-gust limit enables the wind gate" and "The dew margin is in °C: a finite number of 0 or more". They state what the bullets stated, with no SHALL added.
   - "When the limit is treated as unavailable this way" names "the wind-gust limit", because it opens its own requirement.
   - "The rules, in the order they apply:" is not carried. It only introduced the five bullets, which are now requirements. The order that matters is stated by "The hard gates SHALL be evaluated before the missing-cloud rule applies" and "Only when every hard gate passes does the missing-cloud rule apply".
   - The bold labels on the degrading bullets ("**Missing optional data.**" and the rest) are not carried. Each heading now names the case.
   - "defined below" stays in the product requirement. Archive appends the ADDED requirements in the delta's order, so the atmosphere factor's definition does land below it.
   - So the count goes from 55 SHALL (12 SHALL NOT) and 1 MAY to 61 SHALL (12 SHALL NOT) and 1 MAY, with no MUST. Per original: 6 → 7, 7 → 10, 14 → 14, 14 → 15, 6 → 7 and 8 → 8 SHALL. The banded score loses the confidence SHALL to the degrading rule and gains "SHALL rest". Nothing new is required, and nothing is dropped.
5. **No pointers to change** (D11). No spec quotes a removed heading.
6. **No drift to note** (D13). The REMOVED Reasons say only where each part went.
7. **Headings use the spec's own words** (D15). "No dark window" is named as a hard gate, not as a "no-dark-window gate", so no new term enters. No ADDED heading repeats one the delta removes or one the spec keeps.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from the main spec. It copies each scenario block exactly as its source requirement has it, and fails if a name matches no block in that requirement, if a block is placed twice, or if a source scenario is left unplaced. It also writes each REMOVED Reason from the plan.
9. **Accept archive's order.** The 36 new requirements land at the end of the spec, after the ones #244 will split. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: night-verdict` with exactly the 10 added scenarios. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 61 SHALL, 12 of them SHALL NOT, 1 MAY and no MUST (Decision 4). The plan review compares each original with its parts.
- [An added scenario asserts something the code does not do] → Each rests on an existing test (Decision 3). The code review checks them against `pierpressure/core/scoring.py`, `pierpressure/core/config.py`, `pierpressure/core/ranking.py` and the tests.
- [Four requirements sit close to the limit] → "More cloud never raises the usable-sky term times the atmosphere factor" is at 492 characters, "GO needs a score at the go-threshold, cloud data and no cap" at 478, "Entirely missing cloud data gives MAYBE with a score of 0" at 476 and "The score is the product of four factors" at 474. A later change that MODIFIES one and adds words may need to split it again.
- ["defined below" depends on order] → It holds after archive. A later change that reorders the spec should name the atmosphere factor's requirement instead.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
