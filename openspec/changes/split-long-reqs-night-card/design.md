## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario (#232, design Context). Four of the split-out behaviors have no scenario of their own (D4, D8, D9).
- The main spec has 123 requirements and 278 scenarios. The 7 long requirements hold 30 of the scenarios and 28 SHALL statements.
- This branch stacks on `split-long-reqs-verdict-narrative` (PR #248). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-verdict-narrative`.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement states one behavior in no more than 500 characters. The longest, "A Cloud range row with no column shows the first cause that applies", is about 486 by the counting rules in epic #230, and strict validation accepts it.
- After archive, the spec holds every one of its 278 scenario blocks word for word, plus the 4 added on purpose.

**Non-Goals:**

- Reordering requirements inside the main spec.
- Rewording the 116 requirements already under the limit, even where they repeat a rule a new requirement states.
- Any change to code, tests, docs or the card.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-night-card --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=night-card`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved. The 4 added scenarios are each asserted by an existing test, named in Decision 2.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/night-card/spec.md`. No code, test or doc refers to a requirement heading (D2).

## Decisions

1. **One requirement per SHALL group, and keep a group whole when its scenarios test it as one.** The split follows the original's own sentences. Two groups stay together on purpose:
   - The opening axis's start and its length stay in one requirement. Each of its 7 scenarios gives both ends of the axis, so a split would leave one half with no scenario of its own (D5).
   - The Cloud range message's three causes stay in one requirement with their order. The order is the behavior: "A missing sensor comes before an unavailable one" tests it.
   - Alternative: split start from length and add scenarios. Every new scenario would repeat a THEN an existing one already asserts.
2. **Add a scenario only where a behavior has none, and only one an existing test asserts.** Four behaviors need one (D3):

   | Added scenario | Under | Test that already asserts it |
   |---|---|---|
   | The strip comes after the verdict, score and confidence | The card draws the night strip below the verdict | `card/test/strip.test.ts` "are drawn under the verdict lines" |
   | Cloud high reads the sensor named from the pier | Each of the four cloud rows reads its cloud sensor | `card/test/strip.test.ts` "reads the cloud sensors named from the pier" |
   | A Cloud range row with one column | A Cloud range row with a column shows no message | `card/test/range.test.ts` "shows no message" and "draw one column for an hour both forecasts give" |
   | The strip section says when the Cloud range row is left out | The docs say when the Cloud range row is left out | `tests/test_night_card_doc.py` `test_docs_strip_section_says_when_the_cloud_range_row_is_left_out` |

   Each restates a SHALL the requirement keeps, so it adds no rule (epic decision 4).
   - Alternative: keep these behaviors inside a larger requirement. That keeps two behaviors in one requirement, which is what the epic removes.
3. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "The rows and their sensors" goes with the cloud rows' order. Its THEN is the order; its AND names the sensors.
   - "Before the first verdict" (from the night span) goes with "The strip opens on the opening axis". Its THEN says the card still draws the strip.
   - "The strip section covers the Cloud range row" goes with what the docs say the row reads and shows. Two of its three checks test that.
   - "A new night of another length" and "A new pier" go with "A panned strip keeps its start". Both say when the panned start holds and when it gives way.
   - "One cloud provider" and "Before the first verdict" (from the Cloud range message) go with "The card never says Needs two forecasts". Those are the cases that once showed that message.
4. **Reword only so each requirement reads on its own** (D11):
   - Both halves of "A missing sensor leaves its row empty" name the rows they cover. The second states its trigger again: a sensor that is missing, unavailable or has no `forecast` list.
   - "Each cloud row" becomes "Each of the four cloud rows", because the Cloud range row reads two sensors.
   - "An earlier pan" gets a definition that mirrors the one the original gives for a later pan. It requires nothing new.
   - Both docs requirements open with the original's lead sentence. This raises the SHALL count from 28 to 29. Nothing new is required.
5. **Headings use the spec's own words** (D12). No ADDED heading repeats one the delta removes or one the spec keeps.
6. **Copy scenarios with a script.** A script under `.workspace/` builds the delta. It copies each named scenario block exactly as the main spec has it, and fails if any scenario of a split requirement is left out.
7. **Accept archive's order.** The 21 new requirements land at the end of the spec. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: night-card: 4 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count SHALL in the ADDED requirements: 29 expected, against 28 in the originals (Decision 4). The plan review compares each original with its parts.
- [An added scenario states a rule the spec did not have] → Each one's WHEN and THEN restate only the SHALL of the requirement it sits under, and a test already asserts it (Decision 2). The pull request lists all 4.
- [The longest new requirement is close to the limit] → Strict validation measures it with OpenSpec's own counter, before and after archive. A later change that lengthens it gets the warning.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
