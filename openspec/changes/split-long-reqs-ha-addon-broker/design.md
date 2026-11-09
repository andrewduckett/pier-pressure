## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement, replaces each MODIFIED one in place, and appends the ADDED ones at the end of the main spec.
- Strict validation rejects an ADDED requirement that has no scenario.
- The 4 long requirements hold 17 scenarios, 36 SHALL (3 of them SHALL NOT, and one "Neither … SHALL") and 1 MAY.
- "The core checks every saved setting" states four behaviors but has only 2 scenarios.
- Three pointers in these requirements name "The add-on combines the Configuration form with config.yaml", which #237 removed (PR #259, "Pointers"). Two spec pointers name "The add-on uses the Supervisor's MQTT broker when the settings name none", which this change removes: one in "The add-on reads config from its own config folder", and one in "A broker host on the form sets all four connection settings".
- This branch stacks on `split-long-reqs-ha-addon-form-fields` (PR #259). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-ha-addon-form-fields`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 18 new requirements states one behavior in no more than 500 characters, and `ha-addon` has no long-requirement warning.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 2 added on purpose.
- After archive, no pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Editing the code comments that name a removed heading (D10). The epic changes no code or test.
- Reordering requirements inside the main spec.
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-ha-addon-broker --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=ha-addon`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, a pointer check under `.workspace/` that resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. The two added scenarios rest on existing tests in `tests/test_addon_options.py`. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/ha-addon/spec.md`. Two code comments name a removed heading and stay stale (D10). Nothing reads them.

## Decisions

1. **One requirement per behavior, following the original's own sentences and bullets.** The parts are:

   | Removed | Added |
   |---|---|
   | The add-on reads config from its own config folder | The add-on reads config.yaml from its own config folder; The add-on's config.yaml uses the same keys as outside Home Assistant; The add-on starts with the form's settings when config.yaml is missing |
   | The add-on uses the Supervisor's MQTT broker when the settings name none | The add-on wants the Supervisor's mqtt service but does not need it; A broker host in config.yaml sets all four connection settings; With no broker host set, the connection settings come from the Supervisor; The broker's topic settings come from config.yaml or their defaults; A broker port or login in config.yaml without a host is rejected; Outside an add-on, the service does not ask the Supervisor for the broker; Requests to the Supervisor bypass any proxy |
   | The add-on waits a bounded time for the Supervisor's broker | The add-on keeps asking for a Supervisor broker that is not provided yet; The wait for the Supervisor's broker lasts at most 60 seconds; No Supervisor broker within 60 seconds stops the add-on; A refused mqtt service stops the add-on at once |
   | The core checks every saved setting | The core checks each saved setting as it checks config.yaml; The add-on only reads, renames and combines the saved form values; A form field that is not set is left out before the core checks the pier; Saved form values of the wrong shape stop the add-on |

   These stay together on purpose:
   - The definition of the connection settings and the "one source" rule sit with the `config.yaml` source. "The file's broker wins" asserts that all four come from the file and none from the Supervisor.
   - The form-source sentence, "When the form sets `mqtt.host`, all four SHALL come from the form", sits with the Supervisor source. It names the case in which the Supervisor is not asked, and it points to the form's own requirement. Putting it with the file source would take that requirement over 500 characters.
   - The list of "not provided yet" cases stays with the rule to keep asking, because it says when that rule applies.
   - In the setting-check split, "the add-on SHALL NOT decide whether a value is valid" and "it SHALL pass on any value it does not expect" stay with the core's check. Together they say that only the core judges a value, and "Values the Supervisor would refuse get the core's errors" tests them together.
2. **Where each scenario goes** (D3–D6). Each moves whole, under the requirement it fits best:
   - Config folder: "Add-on config mounts the folder" goes with reading the folder; "Config file present" with the file's keys, since its pier gives only an `id` and the one setting it adds; "Config file missing" with the optional file.
   - Supervisor broker: one scenario per requirement, and "The log names the broker's source without the password" also goes with the Supervisor source. No requirement in the original states that log line; it describes what the log shows when the Supervisor gives the broker.
   - Bounded wait: "Mosquitto is still starting" goes with keeping asking; "The wait ends on time" with the 60-second limit; "No broker add-on is installed" with the stop after 60 seconds; "The Supervisor refuses access" with the refused service.
   - Setting check: "Values the Supervisor would refuse get the core's errors" goes with the core's check; "Saved values that are not a mapping stop the add-on" with the shape errors.
3. **Add two scenarios, each backed by an existing test** (D7). The setting-check split has four requirements and two scenarios:
   - "The add-on renames form fields for the core", under "The add-on only reads, renames and combines the saved form values". Tests: `test_a_form_with_piers_becomes_the_config_files_shape` and `test_a_horizon_floor_becomes_a_horizon_block`.
   - "A field saved as null is left out", under "A form field that is not set is left out before the core checks the pier". Test: `test_every_optional_pier_field_saved_as_null_is_left_out`, which covers `max_gust`.
   - Each restates a SHALL its requirement keeps. Neither asserts the rule to ignore undeclared top-level keys, which no test covers.
   - Alternative: fewer, larger requirements. Each pairing tried runs over 500 characters, or joins two behaviors under one heading.
4. **Reword only so each requirement reads on its own** (D12):
   - Each new requirement names its scope again, mostly "Inside an add-on".
   - "Neither error SHALL say that `config.yaml` is not read" becomes "It SHALL NOT say that `config.yaml` is not read" in each of the two error requirements. +1 SHALL.
   - "the service SHALL behave as it did before this change" becomes "as it did before the add-on could use the Supervisor's broker". "This change" named the change that added the Supervisor broker, which a split requirement no longer makes clear. The scenario "Outside an add-on, nothing changes" keeps its words.
   - "The add-on SHALL still stop with a configuration error" becomes "the service SHALL stop with a configuration error", because "still" pointed to the previous paragraph, which is now another requirement.
   - "any other top-level key" becomes "any top-level key … that the form does not declare", because "other" pointed to the sentence on declared settings, which is now another requirement.
   - So the count goes from 36 SHALL (3 SHALL NOT) and 1 MAY to 37 SHALL (5 SHALL NOT) and 1 MAY. Per original: 3 → 3, 14 → 14, 11 → 12, 8 → 8. Nothing new is required.
5. **Retarget pointers instead of dropping them** (D8, D9):
   - The config-folder pointer to the removed combine heading names "The add-on builds one set of settings from the form and config.yaml", which holds the rule that the file adds settings to the form.
   - The setting-check pointer on unset fields names "An empty or blank form field counts as not set". The pointer on combining rules names "The add-on builds one set of settings from the form and config.yaml".
   - The config-folder pointer to the removed Supervisor heading, about leaving out the connection settings, names "With no broker host set, the connection settings come from the Supervisor".
   - "A broker host on the form sets all four connection settings" is MODIFIED. "the requirement "The add-on uses the Supervisor's MQTT broker when the settings name none" decides" becomes "the requirements "A broker host in config.yaml sets all four connection settings" and "With no broker host set, the connection settings come from the Supervisor" decide". Its other text and its 2 scenarios stay word for word. It stays under 500 characters.
6. **No drift to report** (D11). The code also retries answers the "not provided yet" list does not name, such as a response that is not JSON. The list does not claim to be complete, so the spec and the code agree.
7. **Headings use the spec's own words** (D13). No ADDED heading repeats one the delta removes or one the spec keeps.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if a name matches no block or more than one.
9. **Accept archive's order.** The 18 new requirements land at the end of the spec, after #238's. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: ha-addon` with exactly the 2 added scenarios. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 37 SHALL, 5 of them SHALL NOT, and 1 MAY expected (Decision 4). The plan review compares each original with its parts.
- [An added scenario asserts something the code does not do] → Each rests on an existing test (Decision 3). The code review checks them against `pierpressure/addon_options.py`.
- [The MODIFIED requirement changes more than its pointer] → A task diffs it against the main spec and allows only the pointer edit.
- [Two code comments name a removed heading] → Accepted (D10). The pull request names them for a later change that may edit code.
- [The spec loses its grouping, so a reader finds the broker rules in several places] → Accepted for now (Decision 9). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
