## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec, as the pilot (#231) showed.
- Strict validation rejects an ADDED requirement that has no scenario (#232, design Context). One split-out behavior has no scenario of its own (D12).
- The main spec has 53 requirements and 166 scenarios. The 9 long requirements hold 57 of the scenarios and 50 SHALL statements, 3 of them SHALL NOT. They hold no MAY.
- This branch stacks on `split-long-reqs-target-ranking` (PR #256). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-target-ranking`.

## Goals / Non-Goals

**Goals:**

- After archive, each new requirement states one behavior in no more than 500 characters. The longest, "The computed outcome carries an error for each variable that computed nothing", is 488 by OpenSpec's own count, and strict validation accepts it.
- After archive, the spec holds every one of its 166 scenario blocks word for word, plus the 1 added on purpose.

**Non-Goals:**

- Reordering requirements inside the main spec.
- Rewording the 44 requirements that are under the limit.
- Any change to code, tests or docs.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-conditions --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=conditions`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, and `mise run check` to show that nothing else moved. An existing test asserts the added scenario, as Decision 2 names. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/conditions/spec.md`. No code, test or doc refers to a requirement heading (D2).

## Decisions

1. **One requirement per SHALL group, and keep a group whole when its scenarios test it as one.** The split follows the original's own sentences and bullets. Five groups stay together on purpose:
   - The cloud layers and the bundle they form with the total stay in one requirement. Its one scenario, "Cloud data carries the layer split alongside the total", reads the layers from "the provider that filled cloud cover", so it tests both.
   - The rule that the first provider in order fills a variable, the shape of its series, and "a variable no provider filled SHALL have no series" stay in one requirement. They describe one fill, and splitting off the empty case would need a scenario of its own.
   - The rule that later providers leave alternates and the rule for what an alternate carries stay in one requirement. Their scenario, "A later provider's cloud becomes an alternate", asserts both.
   - When the computed outcome carries an error, the shape of each part, how parts are joined, and that a successful outcome still carries a failed variable's part stay in one requirement. The three fixed reasons each become a requirement of their own.
   - The three safe parts of an error description stay in one bulleted list. They are one rule, stated as an allowlist.
   - Alternative: split each of these further and add scenarios. Every new scenario would repeat a THEN an existing one already asserts.
2. **Add a scenario only where a behavior has none, and only one an existing test asserts.** One behavior needs one (D3, D12):

   | Added scenario | Under | Test that already asserts it |
   |---|---|---|
   | A request just after midnight asks for no forecast days and for UTC | An Open-Meteo hourly request asks for no forecast days and for UTC times | `tests/test_conditions_provider.py` `test_every_open_meteo_request_asks_for_4_past_hours_and_72_ahead`, run for every Open-Meteo key in the catalog at 00:05 and 18:05 UTC, asserts `"forecast_days" not in params` and `params["timezone"] == "UTC"` |

   It restates the two SHALLs the requirement keeps, so it adds no rule (epic decision 4).
   - Alternative: keep this behavior inside the hours requirement. That requirement would then run to 544 characters again.
3. **A scenario that tests two behaviors stays with the one its name and THEN fit** (epic decision 2):
   - "Every Open-Meteo provider asks for the same hours" goes with "Every Open-Meteo hourly request asks for 4 past hours and 72 forecast hours". It also asserts no forecast days and UTC, but its name is about the hours.
   - "Both missing inputs are named in order" goes with "A computed error names the inputs that have no filled series". It also shows the parts joined, transparency first, but its name is about the inputs.
   - "A computed hour makes the outcome successful" goes with "The computed outcome succeeds when a computed hour carries a value". It also asserts the issue time, which "The outcome's issue time is the oldest computed one" tests on its own.
   - "A successful fetch is reported with its issue time" goes with "A successful outcome carries its data's issue time". It also asserts the time the fetch ran.
   - "Periods for different variables stay independent" goes with "Each NWS value is held across every hour its period covers", which now holds the rule that an uncovered hour stays absent (Decision 4).
   - "A split bundle leaves the high-cloud penalty neutral" goes with "A provider fills a bundle whole or not at all". Its WHEN is a split bundle; its THEN is the verdict's reading of it.
   - "Precipitation probability comes from the next provider that declares it" and "Column water vapour comes from the next provider that declares it" go with "HRDPS and RDPS declare no precipitation probability". "The seeing column comes from the next provider that declares it" and "RDPS declares no seeing column" go with "A provider that does not declare the seeing column declares none of its variables".
   - "Alternates do not change the verdict's cloud reading" goes with "Alternates never change the filled series", where it sat before.
4. **Reword only so each requirement reads on its own** (D14):
   - Each new requirement names its subject again, such as "an outcome's error description", "the computed source's outcome", "the NWS provider" or "each of the low, mid and high cloud components".
   - "Each part SHALL be the variable key, a colon and a space, then one of these fixed reasons" and its list become four requirements. The first ends "then a fixed reason that says why it computed nothing". Each of the other three states its condition and says the reason "SHALL be" its fixed text. This is why the SHALL count goes from 50 to 53: one "SHALL be one of these" becomes three "SHALL be" statements. Nothing new is required.
   - "each key once, in the order its inputs are listed above" names that order: for transparency, the provider of `column_water_vapour` comes before the provider of `aerosol_optical_depth`. "Above" pointed at "The computed series carries its oldest input's issue time", which lists them in that order. `pierpressure/conditions/provider.py` builds the inputs from `_TRANSPARENCY_INPUTS` in the same order.
   - "Precipitation probability is the exception: because …" becomes "Precipitation probability is the exception, as its own requirement says", and the precipitation requirement keeps the "because".
   - "hours within it that no period covers SHALL stay absent" moves from the horizon sentence to the held-across requirement, as "Hours within the provider's 72-hour horizon that no period covers SHALL stay absent". Its scenario tests the hours a period covers, not the horizon.
   - The ICON, HRDPS and RDPS requirements gain "as `open_meteo`" after "the same variables and the cloud bundle", which the original took from the sentence before.
   - "No such request" becomes "No request to Open-Meteo for hourly data", and "The outcomes" becomes "The fetch outcomes".
5. **No drift to report** (D13). Each requirement's SHALLs match the code named in the ledger.
6. **Headings use the glossary's and the spec's own words** (D15). No ADDED heading repeats one the delta removes or one the spec keeps.
7. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if any scenario of a removed requirement is left out or used twice.
8. **Accept archive's order.** The 33 new requirements land at the end of the spec, after the 44 kept ones. The NWS and Open-Meteo requirements then sit apart from their kept neighbours. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: conditions: 1 scenario(s) added`. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count SHALL in the ADDED requirements: 53 expected (3 of them SHALL NOT), against 50 in the originals (Decision 4). The plan review compares each original with its parts.
- [The added scenario states a rule the spec did not have] → Its WHEN and THEN restate only the SHALLs of the requirement it sits under, and a test already asserts it (Decision 2). The pull request lists it.
- [The computed-error requirement sits 12 characters under the limit, so any later wording change may push it over] → Accepted. A later change that touches it can split off the joining rule, with a scenario of its own.
- [The spec loses its grouping, so a reader finds the NWS or Open-Meteo rules in two places] → Accepted for now (Decision 8). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
