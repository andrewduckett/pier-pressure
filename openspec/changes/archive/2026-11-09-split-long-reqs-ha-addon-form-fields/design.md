## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement, replaces each MODIFIED one in place, and appends the ADDED ones at the end of the main spec.
- Strict validation rejects an ADDED requirement that has no scenario.
- The 4 long requirements hold 35 scenarios and 53 SHALL, 3 of them SHALL NOT. They have no MAY. The broker requirement's "The log may still show the host" is a lowercase note, not a normative word.
- #237 removed "The add-on combines the Configuration form with config.yaml". Seven pointers in the main spec still name it: three in the requirements this story splits, one in "The add-on uses the Supervisor's MQTT broker when the settings name none", and three in other requirements #239 owns. The Supervisor requirement also points to "The form sets the broker", which this change removes.
- This branch stacks on `split-long-reqs-ha-addon-form` (PR #258). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-ha-addon-form`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 23 new requirements states one behavior in no more than 500 characters. The longest, "An equipment value beside an equipment field skips the form pier", is 471 by OpenSpec's own count.
- After archive, the spec holds every one of its scenario blocks word for word, and no new one.
- After archive, no pointer in the spec names a heading this change removes.

**Non-Goals:**

- Splitting the 4 other long `ha-addon` requirements, which #239 owns.
- Retargeting the pointers in "The add-on reads config from its own config folder" and "The core checks every saved setting". #239 splits both (D10).
- Reordering requirements inside the main spec.
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-ha-addon-form-fields --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=ha-addon`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, `grep` for pointers to removed headings, and `mise run check` to show that nothing else moved. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/ha-addon/spec.md`. No code, test or doc refers to a requirement heading (D9).

## Decisions

1. **One requirement per behavior, following the original's own sentences and bullets.** The parts are:

   | Removed | Added |
   |---|---|
   | The form sets each pier's horizon | A form pier's min_altitude sets a flat horizon floor; A form pier's horizon_points become its horizon points; A form pier with no horizon field takes its horizon from config.yaml; Horizon points the core cannot read skip the form pier; A form pier's horizon that breaks the horizon rules skips the pier; A horizon value beside a set horizon field skips the form pier |
   | The form sets each pier's equipment | A form pier's equipment fields set its equipment; A form pier's reducer defaults to 1.0; A form pier with no equipment field takes its equipment from config.yaml; Incomplete equipment skips the form pier; An equipment value of 0 or less skips the form pier; An equipment value beside an equipment field skips the form pier |
   | The form sets each pier's GO threshold and wind-gust limit | A form pier's go_threshold and max_gust pass to the pier; An unset go_threshold or max_gust on the form comes from config.yaml; A form pier with no go_threshold or max_gust uses the file defaults; A bad go_threshold or max_gust skips the form pier |
   | The form sets the broker | A broker host on the form sets all four connection settings; A blank broker field on the form counts as not set; Broker login fields on the form without a host stop the add-on; A rejected login from the form points to the form's login; The log names the Configuration tab as the broker's source; No log line or error reveals the form's broker password |
   | (the first three) | Skipping every pier on the Configuration form stops the add-on |

   These stay together on purpose:
   - The rule that blank `horizon_points` text is unset stays with `horizon_points`. "Blank horizon points are ignored" tests it.
   - The five horizon skip cases become three requirements. The two that name `horizon.points` share one requirement. The inline-point checks and the one-source rule share another, because both errors name only the pier. The `horizon` value case has its own, because the core, not a horizon rule, rejects the fields.
   - "What counts as not set" for the gate fields stays with "an unset value comes from `config.yaml`". "config.yaml fills an empty field" tests both.
   - The pointer to the Supervisor's broker rule, for a form with no host, stays with the rule for a form with a host. It requires nothing, so it needs no scenario of its own.
   - The gate skip requirement keeps the list of bad values, because its one scenario tests two of them.
2. **One shared requirement for "every pier skipped stops the add-on"** (D7). The horizon, equipment and gate requirements each said "When every pier is skipped, the add-on SHALL stop with a configuration error, as it does for any setup with no valid pier." Three requirements with one behavior would each need a scenario, and the gates have none. Like the originals, the shared requirement names no cause: the add-on stops whenever every form pier is skipped. Naming the three causes would narrow it, because a form whose piers fail for a mix of reasons, such as one bad latitude and one bad horizon, would fall outside it. It takes both scenarios that test the rule.
   - Alternative: keep the sentence in each skip requirement. That repeats one behavior in eight places.
3. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "Blank horizon points are ignored" goes with `horizon_points`. It also sets `min_altitude`.
   - "Malformed saved values skip only their pier" goes with the unreadable-points requirement. It also asserts that an entry in `piers` that is not a mapping is skipped.
   - "A horizon mapping beside unset horizon fields is used" and "An equipment mapping beside unset equipment fields is used" go with the requirement for a mapping beside a set field. Each is the case that does not skip.
   - "Equipment from the form ranks like file equipment" goes with "A form pier's equipment fields set its equipment". It also asserts the field-of-view reason.
   - "Saved null values count as unset" goes with "A form pier with no equipment field takes its equipment from config.yaml", as its name says. It also asserts the error for incomplete equipment.
   - "A gust over the form's limit is a NO-GO" goes with "A form pier's go_threshold and max_gust pass to the pier". It also asserts the core's wind gate.
   - "A value set in both places stops the add-on" goes with "An unset go_threshold or max_gust on the form comes from config.yaml". Its THEN is the rule in "A setting given on the form and in config.yaml stops the add-on".
   - "The log names the form as the broker's source" goes with the log requirement. It also asserts that no log line holds the password.
   - "A bad horizon on the only pier stops the add-on" and "Incomplete equipment on the only pier stops the add-on" go with the shared stop requirement. Each also asserts the skip error.
4. **Reword only so each requirement reads on its own** (D13):
   - Each new requirement names its scope again: "Inside an add-on", "a pier on the Configuration form".
   - Three lead sentences are dropped: "The service SHALL turn a form pier's horizon fields into that pier's horizon", its equipment twin, and "the form's broker fields SHALL work as follows". Each only introduced the bullets that follow it, and each bullet keeps its own SHALL. −3.
   - Each horizon and equipment skip requirement says "SHALL be skipped" and "SHALL still be published" again. The originals said each once for all their cases. +8.
   - The two "The error SHALL name `horizon.points`" sentences become part of the skip sentence: "skipped with a logged error that names the pier and `horizon.points`". −2.
   - In the two requirements for a `horizon` or `equipment` value beside a set field, "The error SHALL name each of those fields" becomes part of the skip sentence: "skipped with a logged error that names the pier and each of those fields". −2.
   - The three stop sentences become one (Decision 2). −2.
   - So the count goes from 53 to 52, 3 of them SHALL NOT. Each drop merges two SHALLs into one sentence that requires both. Nothing new is required.
   - "missing … while another equipment field is set" becomes "sets an equipment field but leaves out …". "When a pier's value fails these checks" becomes "fails the checks", because "these" pointed at the previous paragraph, which is now another requirement.
5. **Retarget pointers instead of dropping them** (D8, D9). #237 dropped two pointers because their targets were about to be split. These targets stay:
   - In the horizon, equipment and gate requirements, "as the requirement "The add-on combines the Configuration form with config.yaml" describes" names "A pier in config.yaml adds its settings to the form pier with its id". That requirement holds the rule that a file pier adds settings to a form pier.
   - "The add-on uses the Supervisor's MQTT broker when the settings name none" is MODIFIED. Its pointer to "The form sets the broker" names "A broker host on the form sets all four connection settings". Its pointer to the removed combine heading, about the form and file both setting connection settings, names "The broker connection and the recompute interval each count as one setting". Its other text and its 8 scenarios stay word for word.
   - Alternative: leave the Supervisor requirement alone for #239. Then this change would leave a pointer to a heading it removes.
6. **No drift to report** (D12).
7. **Headings use the spec's own words** (D14). No ADDED heading repeats one the delta removes or one the spec keeps.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, copies the MODIFIED requirement whole with the two pointer edits, and fails if any of the 35 scenarios is left out or used twice.
9. **Accept archive's order.** The 23 new requirements land at the end of the spec, after #237's. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: ha-addon` with no scenario added. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 52 expected, 3 of them SHALL NOT and no MAY, against 53 in the originals (Decision 4). The plan review compares each original with its parts.
- [The MODIFIED requirement changes more than its pointers] → A task diffs it against the main spec and allows only the two pointer edits.
- [The shared stop requirement reads wider or narrower than the originals] → Like the three originals, it names no cause (Decision 2).
- [Three pointers to the removed combine heading remain, in #239's requirements] → Accepted. The pull request names them for #239. They were left by #237, not by this change.
- [The spec loses its grouping, so a reader finds the form rules in several places] → Accepted for now (Decision 9). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
