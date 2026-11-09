## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- Strict validation also rejects an ADDED requirement with no scenario, or with no SHALL or MUST in its prose.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec.
- The 6 long requirements hold 32 scenarios and 51 SHALL, 9 of them SHALL NOT. None uses MAY or MUST.
- Several paragraphs of the originals carry no SHALL: what `dark_window.end` means, what the scoring instant is, when an empty scored window can arise, which window end qualifies, and what "narrowed" means. Each must sit in a new requirement that has a SHALL.
- No spec quotes any of the 6 headings, and none of the 6 points to another requirement by its heading.
- This branch stacks on `split-long-reqs-ha-delivery-entities` (PR #262). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-ha-delivery-entities`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 29 new requirements states one behavior in no more than 500 characters.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 6 added on purpose.
- After archive, no quoted pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Splitting the other 14 long requirements in `night-verdict`. #243 and #244 do that.
- Editing the three comments that echo a removed heading (proposal, Impact), or the code that drifts from the text at the exact poles (D12). The epic changes no code or test.
- Reordering requirements inside the main spec.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-night-verdict-window --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=night-verdict`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, the pointer check from the earlier layers' tasks, which resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. Each added scenario rests on an existing test. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/night-verdict/spec.md`. Nothing reads requirement headings.

## Decisions

1. **One requirement per behavior, following the original's own sentences, paragraphs and bullets.** The parts are:

   | Removed | Added |
   |---|---|
   | The verdict judges the remaining night | The verdict judges the scored window; Before astronomical dusk, the scored window is the whole dark window; Once the night has started, the scored window starts at the scoring instant; The gates, the score and the completeness part of confidence run over the scored window; The document carries the scored window beside the dark window; An empty scored window arises only in the last partial second of the dark window; On an ordinary night, an instant on the exact dawn crossing still selects the ending night; In continuous polar night, an instant on the exact solar-day boundary selects the next solar day; An empty scored window gives MAYBE with a score of 0; Less than an hour of dark time caps the verdict at MAYBE |
   | Night window is the astronomical-night boundary | The dark window is the astronomical night selected from the evaluation instant; The selected night is the one whose dawn comes first at or after the evaluation instant; A non-null dark window starts strictly before it ends; In continuous astronomical night, the dark window is non-null and covers the dark span; The continuous-night dark window is anchored to a stable boundary; In continuous non-night, the dark window's start and end are null |
   | Reasons name the scored span | Reasons keep their whole-night wording unless the scored window is narrowed; A narrowed scored window puts a span line first in the reasons; Over a narrowed scored window, reasons speak only of the rest of the night |
   | Conditions are evaluated across the whole scored window | The score reflects the extent and quality of the scored window's usable dark time; A scored window with some usably clear hours is not gated as overcast; Usable dark time is normalized to the scored window's actual duration; Hours without cloud data count as neither clear nor overcast |
   | Moon information across the dark window | The moon object carries its illumination and phase; The moon object reports whether and when the moon is up during the dark window; Moon horizon crossings use the moon's geometric centre at 0 degrees |
   | Astronomical fields are computed offline with stable precision | Astronomical fields are computed offline from bundled data; Astronomical numbers and document timestamps have a fixed precision from construction; Repeated runs on one platform yield byte-identical astronomical values |

   These stay together on purpose:
   - The meaning of `dark_window.end` stays with "The verdict judges the scored window", because it says how every scored-window rule reads that end. "The `dark_window` field SHALL keep the whole night" joins it: it is the other half of what the verdict judges.
   - The definition of the scoring instant stays with the rule that uses it first, "Once the night has started, the scored window starts at the scoring instant".
   - "`generated_at` is the scoring instant" stays with the `scored_window` object, because it says why `scored_window.start` names the span the verdict judged.
   - "The scored window's start SHALL never be later than its end" stays with the three facts that explain when the window is empty. The `scored_window` object repeats it as "never later than `scored_window.end`", as the original did.
   - The paragraph "Which exact end qualifies differs by case", and the one after it, split by case: the ordinary-night half goes with the dawn crossing, and the polar half goes with the solar-day boundary. "Which exact end qualifies differs by case" itself is a connective and is not carried; the two headings name the cases.
   - The short-span rule stays whole, including its reason wording. Its 496 characters fit, and no original scenario asserts the wording alone.
   - The continuous-astronomical-night bullet runs to 510 characters, so its non-null rule and its stable anchor become two requirements.
   - "The two extreme-latitude boundary cases SHALL be handled distinctly" goes with continuous non-night, reworded to name the other case. With continuous night it would run past 500 characters.
   - "In every case the field SHALL be present rather than omitted" joins "SHALL always be present", with "including both extreme-latitude cases" to keep what "every case" meant where it stood.
   - In "Conditions are evaluated across the whole scored window", "Its score SHALL reflect the extent and quality of the usable portion" leaves the overcast bullet and joins the opening sentence and the weighting of other terms. Together they say how the score reads the usable dark time, and "More usable clear darkness scores higher" asserts them.
   - The definition of "narrowed" stays with the not-narrowed rule. Its sentence "That is the test for every rule in this requirement" becomes "That is the test for every rule about a narrowed scored window", because the rules now sit in three requirements.
   - The three rules about narrowed wording stay in one requirement, as the original's one paragraph had them: no whole-night claim, and the cloud, overcast and wind wording that follows from it.
   - The moon rationale, "a bright moon above the horizon during darkness", goes with illumination and phase, so that the across-window fields fit in 500 characters.
   - Fixed precision and its use at construction stay together: the second says when the first applies. "This keeps Home Assistant and external services non-load-bearing" goes with the offline rule, and "This preserves the deterministic-emission guarantee" with the byte-identical rule.
2. **Where each scenario goes** (D3–D8). Each moves whole, under the requirement it fits best:
   - Remaining night: "In continuous polar night, the scored window ends with the solar day" with the scored window; "Before dusk, the scored window is the whole night" with before dusk; "Mid-session, the scored window starts at the generation second" with the scoring instant; "Clear hours that have passed no longer lift the score", "A gust that has already passed does not gate the night" and "Missing wind data in a passed hour does not cap the verdict" with the gates and the score; "The scored window is null without a dark window" with the `scored_window` object; "A verdict after the exact dawn crossing judges the next night" with the dawn crossing; "In continuous polar night, the exact solar-day boundary starts the next window" and "In continuous polar night, the floored second before the boundary is empty" with the solar-day boundary; "A verdict in the last partial second of the night has no usable time left" with `MAYBE` and a score of 0, since four of its five THEN lines assert that verdict; "Less than an hour of dark time caps the verdict at MAYBE", "A whole night shorter than an hour is capped the same way" and "An hour or more left can still be GO" with the short span.
   - Night window: "A real astronomical-night window is computed when night exists" with the selected astronomical night; "The current night is selected when the instant is already dark" with the selection; "Continuous astronomical night yields a non-null window" with the non-null continuous night; "Continuous non-night yields a null window" with continuous non-night.
   - Span: "A verdict before dusk keeps the whole-night wording" and "A verdict in the dusk second keeps the whole-night wording" with the whole-night wording; "A mid-session missing-cloud verdict names the span it judged" with the span line; "A mid-session scored verdict names the span it judged" and "A mid-session gated verdict names the span it judged" with the rest-of-the-night wording, since each asserts that wording beyond the span line.
   - Conditions: "More usable clear darkness scores higher" with the score; "A partly clear night is not gated as overcast" with not gated; "A window that does not align to whole hours still yields a bounded score" with normalizing; "Hours without cloud data lower the score without gating" with missing cloud data.
   - Moon: "Moon object carries illumination and a bounded phase name" with illumination and phase; "Moon above-horizon behaviour is reported across an existing dark window" and "Across-window moon fields are null when there is no astronomical night" with the across-window fields.
   - Astronomy: "Verdict production performs no runtime network access" with offline; "Astronomical numeric and time fields are emitted at a fixed precision" with fixed precision, since two of its three THEN lines assert precision.
3. **Add six scenarios, each backed by an existing test** (D9). The first five go to new requirements that none of the original scenarios fits:
   - "A grazing night that whole seconds collapse is reported as null", under "A non-null dark window starts strictly before it ends". `test_subsecond_night_collapses_to_null_on_whole_second_truncation` asserts it.
   - "Two recomputes in one continuous-night period give the same window", under "The continuous-night dark window is anchored to a stable boundary". `test_continuous_astronomical_night_is_nonnull_and_stable` asserts it with two instants eight hours apart. "Continuous astronomical night yields a non-null window" also asserts this in its last line, and stays whole under the non-null rule.
   - "In the floored dawn second, the scored window closes on the end of the dark window", under "An empty scored window arises only in the last partial second of the dark window". `test_an_instant_in_the_floored_dawn_second_has_no_dark_time_left` asserts that the scored window is the end of the dark window twice over.
   - "Moonrise and moonset are the geometric centre crossing 0 degrees", under "Moon horizon crossings use the moon's geometric centre at 0 degrees". `test_moon_rises_within_window_is_reported_and_up_during_dark` and `test_moon_sets_within_window_is_reported` assert it against a refraction-free oracle.
   - "Two offline runs give byte-identical astronomical fields", under "Repeated runs on one platform yield byte-identical astronomical values". `test_two_runs_are_byte_identical_offline` asserts it, at an instant whose night has a moonrise.

   - "An instant exactly on the dawn crossing still judges the ending night", under "On an ordinary night, an instant on the exact dawn crossing still selects the ending night". The original scenario there, "A verdict after the exact dawn crossing judges the next night", tests an instant after the crossing, not on it (plan review, finding 1). `test_an_instant_exactly_on_the_dawn_crossing_has_no_dark_time_left` asserts it.

   Alternative: join each of these requirements to a neighbor so that an original scenario covers it. Each join runs past 500 characters, or puts two behaviors under one heading.
4. **Reword only so each requirement reads on its own** (D13):
   - "the reasons keep their whole-night wording" becomes "the reasons SHALL keep their whole-night wording", so the narrowed-definition requirement has a SHALL. "no span line is present" stays as it was.
   - A dawn crossing or a solar-day boundary that "qualifies" becomes one that "SHALL qualify as the exact end of the selected window", so each case has a SHALL. The ordinary-night rule restates the selection rule that "The selected night is the one whose dawn comes first at or after the evaluation instant" already holds.
   - "So the scoring instant equals `dark_window.end` only when the evaluation instant lies in that floored second and the selection still picks that window" names the second: "the floored second that `dark_window.end` names". Each case requirement then ends with its own half of the original's last two sentences, after a colon.
   - "Which exact end qualifies differs by case." is not carried. It only introduced the two cases, and each case is now its own requirement.
   - "The rules below read `dark_window.end`" becomes "The rules that read `dark_window.end`", because the rules no longer sit below.
   - The `moon` field list becomes two requirements, so its "SHALL contain" opens both, as "SHALL also contain" in the second.
   - "The two extreme-latitude boundary cases SHALL be handled distinctly" becomes "Continuous non-night SHALL be handled distinctly from continuous astronomical night", and the bullets become sentences that open "In continuous ...". "e.g." becomes "as in".
   - "The window SHALL be anchored" becomes "In continuous astronomical night, the dark window SHALL be anchored".
   - "In every case the field SHALL be present rather than omitted" gains ", including both extreme-latitude cases,".
   - "That is the test for every rule in this requirement" becomes "That is the test for every rule about a narrowed scored window".
   - In the conditions requirement, "Its score SHALL reflect" becomes "The score SHALL reflect", because it no longer follows the overcast sentence.
   - The `moon` list's "with these fields: `illumination` (...), `phase` (...)" becomes "with `illumination` (...) and `phase` (...)", and "This gives later milestones" becomes "This object gives later milestones".
   - The original's last sentence on astronomy splits in two: "This keeps Home Assistant and external services non-load-bearing for correctness" ends the offline requirement, and "This preserves the deterministic-emission guarantee once real sky math is introduced" ends the byte-identical one.
   - A bullet that becomes a requirement, or part of one, becomes a sentence: the scoring instant, before dusk, the empty-window rule, the four conditions bullets and the two extreme-latitude cases. The list of rules that run over the scored window, the `scored_window` fields and the three facts about an empty scored window stay bullets.
   - Decision 1 lists the sentences that move between requirements, such as "The `dark_window` field SHALL keep the whole night", which joins "The verdict judges the scored window".
   - So the count goes from 51 SHALL (9 SHALL NOT) to 55 SHALL (9 SHALL NOT), with no MAY or MUST. Per original: 19 → 21, 11 → 11, 6 → 7, 8 → 8, 2 → 3 and 5 → 5 SHALL. Nothing new is required, and nothing is dropped.
5. **No pointers to change** (D10). No spec quotes a removed heading.
6. **Note the drift, keep the text** (D12). "The verdict judges the scored window" keeps "the end of the local solar day that anchors the dark window". The REMOVED Reason for "The verdict judges the remaining night" says that the code uses the UTC calendar day at the exact poles.
7. **Headings use the spec's own words** (D14). No ADDED heading repeats one the delta removes or one the spec keeps. "Less than an hour of dark time caps the verdict at MAYBE" is both a new heading and a scenario name. Requirement and scenario names are separate, and the epic's check compares scenario blocks only.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from the main spec. It copies each scenario block exactly as its source requirement has it, and fails if a name matches no block in that requirement, if a block is placed twice, or if a source scenario is left unplaced. It also writes each REMOVED Reason from the plan.
9. **Accept archive's order.** The 29 new requirements land at the end of the spec, after the requirements #243 and #244 will split. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: night-verdict` with exactly the 6 added scenarios. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 55 SHALL, 9 of them SHALL NOT, and no MAY expected (Decision 4). The plan review compares each original with its parts.
- [An added scenario asserts something the code does not do] → Each rests on an existing test (Decision 3). The code review checks them against `pierpressure/core/sky.py`, `pierpressure/core/scoring.py` and the tests.
- [Four requirements sit close to the limit] → "Less than an hour of dark time caps the verdict at MAYBE" is at 496 characters, "Astronomical numbers and document timestamps have a fixed precision from construction" at 490, "An empty scored window arises only in the last partial second of the dark window" at 485, and "The moon object carries its illumination and phase" at 484. A later change that MODIFIES one and adds words may need to split it again.
- [The spec's scored-window rules end up apart from the rules #243 and #244 split] → Accepted for now (Decision 9). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
