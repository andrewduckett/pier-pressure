## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario (#232, design Context). Three of the split-out behaviors have no scenario of their own (D4, D5).
- The main spec has 7 requirements and 26 scenarios. The 5 long requirements hold 22 of the scenarios, 42 SHALL statements (one of them SHALL NOT) and 4 MAY statements.
- This branch stacks on `split-long-reqs-night-card` (PR #249). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-night-card`.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement states one behavior in no more than 500 characters. The longest, "A repeated azimuth in inline points keeps one altitude", is about 488 by the counting rules in epic #230, and strict validation accepts it.
- After archive, the spec holds every one of its 26 scenario blocks word for word, plus the 3 added on purpose.

**Non-Goals:**

- Reordering requirements inside the main spec.
- Rewording "Terrain-clearance query" or "Unsupported formats fail clearly", which are under the limit.
- Fixing the verdict-document requirement's drift from the code (D9).
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-horizon-mask --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=horizon-mask`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved. Existing tests assert the 3 added scenarios, as Decision 2 names: two at the seam the scenario describes, and the empty-list one at the horizon builder only.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/horizon-mask/spec.md`. No code, test or doc refers to a requirement heading (D2).

## Decisions

1. **One requirement per SHALL group, and keep a group whole when its scenarios test it as one.** The split follows the original's own sentences and bullets. Three groups stay together on purpose:
   - The two repeated-azimuth outcomes (keep one pair, or reject) stay in one requirement. They are the two halves of one rule, and its two scenarios test one each.
   - The three ways points text can fail stay in one requirement with the error's wording. Both scenarios check the failure and the error together.
   - The two NINA quirks (360 and below 0) stay in one requirement. Their one scenario tests both, and the original states them as one tolerance.
   - Alternative: split each of these further and add scenarios. Every new scenario would repeat a THEN an existing one already asserts.
2. **Add a scenario only where a behavior has none, and only one an existing test asserts.** Three behaviors need one (D3):

   | Added scenario | Under | Test that already asserts it |
   |---|---|---|
   | A sample at azimuth 360 is held at azimuth 0 | A horizon is a set of azimuth and altitude samples | `tests/test_horizon.py` `test_azimuth_360_normalizes_to_zero_and_deduplicates` (the samples' azimuths are `[0.0]`) |
   | An imported file and the same inline points hold the same samples | Every horizon source gives the same samples | `tests/test_horizon.py` `test_nina_fixture_imports_to_the_equivalent_inline_points_horizon` (`imported.samples == equivalent.samples`) |
   | An empty points list is rejected | Inline points hold at least one pair | `tests/test_horizon.py` `test_at_least_one_point_is_required` asserts that `from_points([])` rejects the list. No test drives `points: []` through the configuration: `pierpressure/core/config.py` lines 202–203 pass the list to `from_points`, and a hand run of `validate_piers` while planning skipped the pier |

   Each restates a SHALL the requirement keeps, so it adds no rule (epic decision 4).
   - Alternative: keep these behaviors inside a larger requirement. Two of them would push that requirement past 500 characters again.
3. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "A single-sample horizon is flat" names the flat floor and open sky in its WHEN, but it tests the one-sample rule, so it goes with "A one-sample horizon has one altitude everywhere".
   - "A valid export imports to the equivalent horizon" goes with "A pier may import a NINA horizon export". Its WHEN is the import. It also shows that every source gives the same samples, but that requirement gets its own scenario (Decision 2).
   - "A malformed export invalidates only its pier" goes with "Malformed NINA content makes the pier's configuration invalid". Its AND, that other piers still produce verdicts, is per-pier isolation the config already gives.
4. **Reword only so each requirement reads on its own** (D10):
   - Each new requirement names its subject again, such as "a pier's inline points" or "a NINA `.hrz` export".
   - "As the representation requirement says" becomes "as the sample representation requires", since the original heading is removed.
   - The sentence on sub-precision noise moves from the representation to "A repeated azimuth in inline points keeps one altitude". It said "the duplicate-azimuth rule below compares rounded altitudes", so it is part of that rule.
   - "The list SHALL follow these rules" is dropped. It only introduced the bullets, and each bullet is now a requirement with its own SHALL. This is why the SHALL count goes from 42 to 41. Nothing is no longer required.
   - The verdict-document requirement loses 49 characters of wording: "Producing a verdict … SHALL yield a document byte-identical to the one produced for … with no horizon configured" becomes "A verdict … SHALL be byte-identical to the one for … with no horizon" (D8).
5. **Keep the verdict-document requirement's meaning, though it is out of date** (D9). `tests/test_horizon_contract.py` and `target-ranking` show that the horizon now changes `targets`. Fixing that changes what is required, which the epic rules out. The pull request reports the drift so the maintainer can file a bug.
   - Alternative: fix the requirement here. That breaks epic decision 3 and mixes a behavior change into a text-only review.
6. **Headings use the spec's own words** (D11). No ADDED heading repeats one the delta removes or one the spec keeps.
7. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if any scenario of a removed requirement is left out.
8. **Accept archive's order.** The 21 new requirements land at the end of the spec, after "Terrain-clearance query" and "Unsupported formats fail clearly". This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: horizon-mask: 3 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count SHALL and MAY in the ADDED requirements: 41 SHALL (one of them SHALL NOT) and 4 MAY expected, against 42 and 4 in the originals (Decision 4). The plan review compares each original with its parts.
- [An added scenario states a rule the spec did not have] → Each one's WHEN and THEN restate only the SHALL of the requirement it sits under, and a test already asserts it (Decision 2). The pull request lists all 3.
- [A stale requirement gets a new heading, so it looks freshly agreed] → Its REMOVED **Reason** says it is restated and names the drift, and so does the pull request (Decision 5).
- [Archive puts the new requirements after the two kept ones, so the spec reads out of its old order] → Accepted (Decision 8). Each requirement reads on its own.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
