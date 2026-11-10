## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It counts the trimmed lines of prose joined by line breaks, so a wrapped line costs one character, as a space would.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario (#232, design Context).
- The 2 long requirements hold 29 scenarios and 61 normative words: 57 SHALL, 3 SHALL NOT and 1 MAY.
- #238 will split "The form sets each pier's equipment" and "The form sets each pier's GO threshold and wind-gust limit", so those headings will not last.
- This branch stacks on `split-long-reqs-conditions` (PR #257). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-conditions`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 26 new requirements states one behavior in no more than 500 characters. The longest, "Each pier on the form has four optional equipment fields", is 467 by OpenSpec's own count.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 5 added on purpose.

**Non-Goals:**

- Splitting the 8 other long `ha-addon` requirements, which #238 and #239 own.
- Reordering requirements inside the main spec.
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-ha-addon-form --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=ha-addon`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved. Existing tests assert each added scenario, as Decision 3 names. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/ha-addon/spec.md`. No code, test or doc refers to a requirement heading (D2).

## Decisions

1. **One requirement per group of the original, and keep a group whole when its scenarios test it as one.** The split follows the original's own paragraphs and bullet lists. These stay together on purpose:
   - The form's top-level settings, `interval_seconds` and `piers`, stay in one requirement with their defaults. "Add-on config declares the form" asserts them together.
   - The fixed list of horizon points the save check accepts and rejects stays with the horizon fields. "The save check on horizon points" tests it.
   - The rule that an `id` only matches the two sources, and is not a setting, stays with the rule that a file pier adds its settings to the form pier with that `id`. Both describe one match.
   - "Each setting comes from one source", the error for a setting in both, and "every other setting counts as its own" stay in one requirement. They are one rule and its error.
   - "The `piers` of `config.yaml` is not a list" stays with the pier-entry shape errors, as one rule about the shape of the file's pier list. It has no scenario of its own.
   - "The form SHALL list at least one pier" moves from the opening paragraph to "A Configuration form with no piers stops the add-on", where the rule is enforced.
2. **Split the four groups that count as one setting into two requirements.** "A pier's horizon and its equipment each count as one setting" and "The broker connection and the recompute interval each count as one setting" each keep two of the four scenarios. Kept as one requirement, the list runs to 531 characters.
   - Alternative: shorten the lead sentence. That leaves the requirement within a few characters of the limit, and it still holds two kinds of group.
3. **Add a scenario only where a behavior has none, and only one an existing test asserts.** Five behaviors need one (D5):

   | Added scenario | Under | Test that already asserts it |
   |---|---|---|
   | The form declares the broker's four fields | The form's broker block has four optional fields | `tests/test_ha_addon.py` `test_addon_form_schema_declares_the_broker` and `test_addon_form_defaults_to_the_interval_and_no_piers` |
   | The form declares the four equipment fields | Each pier on the form has four optional equipment fields | `tests/test_ha_addon.py` `test_addon_form_schema_declares_the_interval_and_piers`, through `PIER_FIELDS` |
   | The form declares the two gate fields | Each pier on the form has two optional gate fields | `tests/test_ha_addon.py` `test_addon_form_schema_declares_the_interval_and_piers`, through `PIER_FIELDS` |
   | Flat form fields become the file's horizon and equipment blocks | The form's setting names match the names in config.yaml | `tests/test_addon_options.py` `test_horizon_and_equipment_blocks_sit_side_by_side` |
   | A broker from config.yaml is logged as from both sources | The log says whether config.yaml added a setting | `tests/test_main.py` `test_the_files_broker_wins` |

   Each restates only SHALLs its requirement keeps, so it adds no rule (epic decision 4). The first three repeat a THEN that "Add-on config declares the form" already asserts. That scenario can sit under only one requirement, and it moves whole.
   - Alternative: keep the broker, equipment and gate fields with the top-level settings. That requirement would run to over 1,200 characters again.
   - Alternative: fold the log rule into "The add-on builds one set of settings from the form and config.yaml". That runs to about 580 characters.
4. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "Add-on config declares the form" goes with the top-level settings. It also asserts the broker, horizon, equipment and gate fields (Decision 3).
   - "Form setup gives a verdict without a file" goes with "The add-on builds one set of settings from the form and config.yaml". It also asserts the log line, but its name is about a form with no file.
   - "The file adds the topic names" goes there too, because its THEN shows the file adding a setting the form leaves unset.
   - "A file pier with only an id adds nothing" goes with the `id` match. It also asserts the log line.
   - "A form pier takes its horizon file from config.yaml" goes with "A relative horizon file path in config.yaml is read from the add-on's config folder". It also asserts that the file adds the horizon, and the log line.
   - "A horizon floor of 0 counts as set" goes with "An empty or blank form field counts as not set". Its THEN is the conflict error that a set 0 causes.
   - "A YAML error does not quote the file" goes with "No combine error quotes config.yaml or a setting's value", which its name fits. It also asserts the line the YAML error names. "A config.yaml that is not valid YAML stops the add-on" stays with the YAML requirement.
   - "A broker connection split across both stops the add-on" goes with the broker group. It also asserts that no value is quoted.
   - "A skipped form pier still counts as listed" goes with the unlisted-pier requirement, which holds that rule.
5. **Reword only so each requirement reads on its own** (D7):
   - Each new requirement names its subject again, such as "the Configuration form", "a pier in `config.yaml`" or "inside an add-on". "Each pier SHALL also have" becomes "Each pier on the Configuration form SHALL have".
   - The original's one "The add-on SHALL stop with a configuration error in each of these cases" becomes one "SHALL stop" sentence in each of the five requirements its list covered. That adds 4 SHALL.
   - Splitting the four groups repeats "each of these groups SHALL count as one setting". That adds 1 SHALL.
   - "`mqtt`: the broker, as a block of four optional fields. The default SHALL be an empty block" moves to the broker block's requirement as "The `mqtt` setting of the Configuration form SHALL be a block of four optional fields. Its default SHALL be an empty block". That adds 1 SHALL. The top-level requirement still names `mqtt`, the broker, as its third setting.
   - So the count goes from 61 to 67: 63 SHALL, 3 SHALL NOT and 1 MAY. Nothing new is required.
   - "The service then rejects 0, as described in "The form sets each pier's equipment"" ends at "rejects 0". The gate fields drop "as described in "The form sets each pier's GO threshold and wind-gust limit"". #238 splits both of those requirements, so the pointers would soon name headings that no longer exist. The pointers require nothing, and the rule that the service rejects 0 stays.
   - "Every other setting" becomes "Every setting outside the groups that count as one setting", because the groups now sit in their own requirements.
   - "The error SHALL list every such problem it finds" becomes "When the add-on finds problems in combining the Configuration form with `config.yaml`, its configuration error SHALL list every problem it finds".
   - "No error SHALL quote …" and the escaping rule each open with "When the add-on combines the Configuration form with `config.yaml`", the scope the original sentence had inside its requirement.
   - "as it did before this change" becomes "as it did before the add-on could read the form", because "this change" would now mean the split. The scenario keeps its own words.
6. **No drift to report** (D6). Each requirement's SHALLs match the code named in the ledger.
7. **Headings use the spec's own words** (D8). No ADDED heading repeats one the delta removes or one the spec keeps.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if any of the 29 scenarios is left out or used twice.
9. **Accept archive's order.** The 26 new requirements land at the end of the spec, after the 14 kept ones. The form requirements then sit apart from "The form sets each pier's horizon" and its neighbours. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: ha-addon: 5 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 67 expected, 3 of them SHALL NOT, against 61 in the originals (Decision 5). The plan review compares each original with its parts.
- [An added scenario states a rule the spec did not have] → Its WHEN and THEN restate only the SHALLs of the requirement it sits under, and a test already asserts it (Decision 3). The pull request lists all five.
- [Three added scenarios repeat a THEN of "Add-on config declares the form"] → Accepted. Strict validation needs a scenario under each requirement, and that scenario cannot be split (epic decision 2).
- [Dropping two "as described in" pointers loses a link a reader could follow] → Accepted. The pointers would dangle once #238 lands, and the rule they introduce stays in the text.
- [The spec loses its grouping, so a reader finds the form rules in two places] → Accepted for now (Decision 9). #238 and #239 append more requirements, and reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
