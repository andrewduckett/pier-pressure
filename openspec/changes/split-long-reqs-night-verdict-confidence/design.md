## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- Strict validation also rejects an ADDED requirement with no scenario, or with no SHALL or MUST in its prose.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, in the delta's order.
- The 8 long requirements hold 37 scenarios and 33 SHALL, 4 of them SHALL NOT. None uses MAY or MUST.
- Some sentences carry no SHALL: what confidence expresses, that confidence is orthogonal to the score, the definition of a shown variable, the three agreement fields, the rule that the cloud band keys come last, and the list of variables the timeline does not show. Each must sit in a new requirement that has a SHALL.
- No spec quotes any of the 8 headings, and none of the 8 points to another requirement by its heading.
- They are the last 8 long-requirement warnings in any main spec.
- This branch stacks on `split-long-reqs-night-verdict-score` (PR #264). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-night-verdict-score`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 21 new requirements states one behavior in no more than 500 characters.
- After archive, `openspec validate --specs` gives no long-requirement warning in any main spec.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 1 added on purpose.
- After archive, no quoted pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Editing the test section comments that quote a removed heading (proposal, Impact). The epic changes no code, test or doc.
- Adding `--strict` to `mise run check`. #245 does that.
- Reordering requirements inside the main spec.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-night-verdict-confidence --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=night-verdict`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, the pointer check from the earlier layers' tasks, which resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. The added scenario rests on an existing test. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/night-verdict/spec.md`. Nothing reads requirement headings.

## Decisions

1. **One requirement per behavior, following the original's own sentences.** The parts are:

   | Removed | Added |
   |---|---|
   | Confidence is present and banded | Confidence is always present with a band and a value from 0 to 100; Confidence rises as the evaluation instant approaches the dark window; Confidence falls when the forecast is stale, data is missing or forecasts disagree; A NO-GO with no dark window has full confidence |
   | The document carries an hourly timeline | The timeline holds one entry per hour a shown variable's filled series covers; Hours that only an alternate or a hidden variable covers add no timeline entry; The timeline is empty, never absent, when no provider returned rows |
   | A timeline entry has a fixed flat shape | A timeline entry carries exactly eighteen keys in a fixed order; A timeline entry's time is the top of the hour |
   | The document carries cloud agreement | The agreement object has a cloud-cover entry only when two providers share a scored hour; The cloud-cover agreement entry holds a band, a spread and its providers |
   | Cloud agreement is the clarity-weighted mean gap over the scored window | An hour's cloud gap is the highest reading minus the lowest; The mean cloud gap weights each hour by its coverage and its clearest reading; The agreement band is decided on the rounded spread |
   | Confidence falls with low agreement | Confidence is multiplied by an agreement factor set by the band; Agreement alone never takes confidence below MEDIUM; Agreement changes no gate, score or verdict; An alternate's issue time never changes confidence |
   | Reasons name the agreement | A cloud-cover agreement entry adds exactly one reason line; The cloud agreement line comes after the gate and score lines |
   | Variables the timeline does not show never change the document | Variables the timeline does not show leave the document unchanged |

   These stay together on purpose:
   - What confidence expresses goes with the field's shape. It says what the band and value mean.
   - "Confidence is orthogonal to the score" goes with the rule that confidence falls. Its scenario, "Missing optional data lowers confidence", asserts both: confidence falls, and no gate fails and the score stays.
   - The definition of a shown variable, and the sort order, stay with the rule that sets the timeline's hours. Both say which hours the list holds and in what order.
   - The two hours that add no entry, an alternate's and a hidden variable's, stay together. Both say which hours do not count.
   - "The two cloud band keys come last" stays with the key list. It explains that list's order.
   - The agreement object's presence and the empty-object case stay together. They are one rule: the entry is there exactly when two providers share a scored hour.
   - The three agreement fields stay together. They are the entry's shape.
   - The zero-weight rule stays with the clarity weighting. It says what the weighted mean is when nothing weighs.
   - The factor's values and "a tuning constant fixed in code" stay together. Both say what the factor is.
   - The reason line's wording, its suffix and its absence stay together (brainstorm D9). The line is there exactly when the entry is.
2. **Keep "Variables the timeline does not show never change the document" as one requirement** (D10). It states one behavior, at 530 characters. Its last sentence only says where the rule stops. As a requirement of its own, it would need a new SHALL and a scenario, and no document-level test asserts it. So it becomes one ADDED requirement of 498 characters. The rewording:
   - "Some variables in the conditions are not shown on the timeline" becomes "The timeline does not show these variables in the conditions".
   - "the 36 variables of the seeing column" becomes "the seeing column's 36 variables".
   - "as the series of a variable the timeline shows, such as the computed source's `transparency` and `seeing` series in the snapshot" becomes "as a shown variable's series in the snapshot, such as the computed source's `transparency` and `seeing`". "Shown variable" is the spec's own term, defined in "The timeline holds one entry per hour a shown variable's filled series covers" as a variable the timeline carries as a key.

   Alternative: split off the last sentence as "A value derived from a hidden variable reaches the document only as a shown variable's series". That adds a SHALL and a scenario no test backs.
3. **Where each scenario goes** (D3–D9). Each moves whole, under the requirement it fits best:
   - Confidence: "Confidence carries a band and a bounded value" with the field's shape; "Confidence rises as the dark window nears" with rising; "Missing optional data lowers confidence" with falling; "Astronomy-only NO-GO is fully confident" with the no-dark-window `NO-GO`.
   - Timeline: "The timeline spans the union of both providers' hours" and "Past hours stay in the timeline" with the hours rule; "Hours only an alternate covers add no entry" and "Hours only a hidden variable covers add no entry" with the hours that add none; "No provider rows yield an empty timeline" with the empty list.
   - Entry shape: "A read-back entry equals the emitted one", "The keys before the weather keys keep their positions" and "The cloud band keys come last" with the key list. The read-back scenario asserts keys and their order as well as values.
   - Agreement: "One provider yields no agreement", "An alternate that covers no scored hour does not count", "Providers that never share an hour yield no agreement" and "No dark window means no agreement" with the entry's presence; "Two providers that nearly agree" and "A provider that shares no counted hour is not listed" with the fields.
   - Mean gap: "An hour one provider covers is left out of the mean" with the hour's gap; "Disagreement in an hour the filled series calls overcast still counts", "Clear hours weigh more than cloudy ones" and "Unanimous overcast is agreement" with the weighting, since each turns on the lowest reading's clarity weight; "A mixed and a disagreeing night" and "The band follows the rounded spread" with the band.
   - Agreement factor: "Disagreement lowers confidence further" and "An already LOW confidence still falls" with the factor; "Disagreement alone never reaches LOW" and "Disagreement at a long lead time stays MEDIUM" with the `MEDIUM` floor; "Mixed agreement lowers confidence" with no gate, score or verdict change, since its last line asserts the same `verdict` and `score`; "A stale alternate does not lower confidence" with the issue time.
   - Reasons: "A scored verdict names the agreement" and "One provider adds no line" with the line; "A gated verdict names the agreement" with the line's place, since it asserts the line on a gated `NO-GO`.
   - Hidden variables: all four scenarios with the one new requirement.
4. **Add one scenario, backed by an existing test** (D11). "An entry's time is emitted as a UTC timestamp" goes under "A timeline entry's time is the top of the hour", which no original scenario fits. `test_timeline_entry_time_is_aware_utc_at_whole_seconds` (`tests/test_model.py`) asserts it: an entry built for 01:00 on 2026-09-08 at UTC+02:00 serializes its `time` as `2026-09-07T23:00:00Z`.

   Alternative: put "A read-back entry equals the emitted one" under the `time` requirement. It asserts a round trip, not the top of the hour or the timestamp format, and it fits the key list better.
5. **Reword only so each requirement reads on its own** (D15):
   - "Confidence SHALL rise … and SHALL fall …" becomes two sentences, one per requirement.
   - "It SHALL be sorted by hour ascending" names "The list".
   - "Hours only an alternate covers SHALL NOT add an entry" and its twin say "a timeline entry".
   - "The list SHALL be empty, never absent" names "The `timeline` list".
   - "`time` SHALL be the top of the hour" names "A timeline entry's `time`".
   - "The entry SHALL hold three fields" names "The `cloud_cover` entry of `agreement`".
   - "`band` SHALL be decided on the rounded `spread`" names "The agreement `band`".
   - "The line SHALL come after the lines" names "The cloud agreement line".
   - The tightening in Decision 2.
   - So the count stays at 33 SHALL, 4 of them SHALL NOT, with no MAY or MUST. Nothing new is required, and nothing is dropped.
6. **No pointers to change** (D12). No spec quotes a removed heading.
7. **No drift to note** (D14). The REMOVED Reasons say only where each part went.
8. **Headings use the spec's own words** (D16). "Hidden variable" is the spec's word, from the scenario "Hours only a hidden variable covers add no entry". No ADDED heading repeats one the delta removes or one the spec keeps.
9. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from the main spec, as #243's did. It copies each scenario block exactly as its source requirement has it, and fails if a name matches no block in that requirement, if a block is placed twice, or if a source scenario is left unplaced. It also writes each REMOVED Reason from the plan.
10. **Accept archive's order.** The 21 new requirements land at the end of the spec, after #243's. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: night-verdict` with exactly the 1 added scenario. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 33 SHALL, 4 of them SHALL NOT, and no MAY or MUST (Decision 5). The plan review compares each original with its parts.
- [The tightened requirement reads differently] → Decision 2 lists each rewording, and the plan review compares it with the original.
- [The added scenario asserts something the code does not do] → It rests on an existing test (Decision 4). The code review checks it against `pierpressure/core/model.py` and the test.
- [Two requirements sit close to the limit] → "Variables the timeline does not show leave the document unchanged" is at 498 characters, and "A timeline entry carries exactly eighteen keys in a fixed order" at 474. A later change that adds a timeline key or a hidden variable MODIFIES one of them and may need to split it. With `--strict` in the gate (#245), that change would fail until it does.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
