## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- Strict validation also rejects an ADDED requirement with no scenario, or with no SHALL or MUST in its prose.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec.
- The 8 long requirements hold 41 scenarios and 68 SHALL, 9 of them SHALL NOT. None uses MAY.
- No spec quotes any of the 8 headings, and none of the 8 points to another requirement.
- The spec already splits the further timeline sensors' current-hour state into a state requirement and an unknown-and-available requirement. The Cloud cover state can follow the same shape.
- This branch stacks on `split-long-reqs-ha-delivery-broker` (PR #261). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-ha-delivery-broker`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 37 new requirements states one behavior in no more than 500 characters, and `ha-delivery` has no long-requirement warning.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 4 added on purpose.
- After archive, no quoted pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Editing the three code and test lines that echo a removed heading (proposal, Impact). The epic changes no code or test.
- Reordering requirements inside the main spec.
- Splitting `night-verdict`, the one spec that still has long requirements. Other stories in epic #230 do that.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-ha-delivery-entities --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=ha-delivery`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, the pointer check from #239's and #240's tasks, which resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. Each added scenario rests on an existing test. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/ha-delivery/spec.md`. Nothing reads requirement headings.

## Decisions

1. **One requirement per behavior, following the original's own sentences, paragraphs and bullets.** The parts are:

   | Removed | Added |
   |---|---|
   | Per-pier entity auto-discovery | The verdict, score and refresh entities are announced by discovery; Re-publishing for a pier updates its verdict, score and refresh entities |
   | Verdict state and attributes are exposed | The verdict entity publishes the verdict and its details; The verdict attributes leave out only the timeline; The score entity shows the numeric score, or unavailable when the score is null |
   | Top target is exposed as an entity | The top-target sensor is announced by discovery; The top-target sensor shows the top target's name and the ordered list; Re-publishing updates the existing top-target sensor; An empty target list makes the top-target sensor unavailable |
   | Narrative is exposed as an optional entity | Disabled narrative delivery publishes no narrative entity; A narrative entity left by an earlier configuration is not removed automatically; Enabled narrative delivery announces a narrative sensor; The narrative prose is published in the attributes, not the state; With no narrative, the enabled narrative sensor is published as unavailable; A missing or disabled narrative does not hold back the other entities; Re-publishing updates the existing narrative sensor |
   | Each rank of the target list is exposed as an entity | A rank sensor is announced for every rank; A filled rank sensor shows its target; A rank with no target renders unavailable; Every publish updates every rank sensor; Each rank sensor's discovery is retained and keyed by the pier and the rank |
   | Provider health is exposed as diagnostic entities | Each configured provider has a health sensor named after it; A health sensor's discovery marks it as a diagnostic timestamp sensor; A health sensor's state is its provider's last success since the process started; On startup, provider health is reset before the process goes online; A startup health reset cut off by a dropped connection is published again; A health sensor's attributes name its provider, its variables and when tracking started; A health sensor's attributes describe its latest fetch; A health sensor's attributes give the issue time of the last success; The computed source's health attributes name its inputs; A failed fetch leaves the last success's details unchanged; A health sensor stays available while the process is online; Provider health travels beside the verdict document, not inside it |
   | The Cloud cover state is the current hour's value | The Cloud cover sensor's state is the current-hour cloud cover; With no current-hour value, the Cloud cover sensor shows unknown and stays available |
   | Each further timeline variable is exposed as an entity | A further timeline sensor is published for each of sixteen keys; A further timeline sensor's discovery is retained and keyed by the pier and the key |

   These stay together on purpose:
   - The verdict state and the list of details in its attributes form one requirement. Their one scenario, "Verdict state and attributes are published from the document", asserts both, and either half alone would have no scenario.
   - The score's numeric state stays with its null-score availability. The one score scenario asserts the availability, and the state alone would need a scenario the original never had.
   - For the top-target and narrative sensors, the discovery schema and the retained topic stay with announcing the sensor, and the identity goes to its own requirement with the "Existing entities are unchanged" scenario. Discovery, schema, topic and identity together run past 500 characters.
   - For the rank sensors, the schema, retained topic and identity stay together, as the original's last paragraph had them. With the first paragraph they run to 518 characters.
   - The top-target name and the ordered list in its attributes stay together, as the original's sentences had them, and the heading names both (plan review, finding 1). The added scenario asserts the name; "Top-target discovery and state are published" asserts the list.
   - "The system SHALL publish discovery for every configured provider, including a provider not tried on this publish" stays with one health sensor per configured provider. Both say the set of health sensors is the configured providers, not the ones tried on a publish (plan review, finding 2).
   - For a health sensor, the discovery flags, schema, topic and identity stay together, as the original's second paragraph had them. They fit in 436 characters, and no health scenario tests identity alone.
   - "Health SHALL be held in memory only, and the system SHALL NOT keep it across restarts" goes with the state. It is why the state is unknown after a restart, and the scenario "No success since a restart resolves to unknown" asserts both.
   - The health attribute list becomes three requirements and one for `inputs`, by what each attribute describes: the provider and when tracking started, which hold until a restart; the latest fetch; the last success's issue time; the computed source's `inputs`. The whole list runs past 1,000 characters.
   - "This entity is additive: every existing entity, topic, and mapping is unchanged" goes with each sensor's identity requirement, beside the "Existing entities are unchanged" scenario that asserts it. For health it goes with "Provider health travels beside the verdict document, not inside it".
   - The Cloud cover state splits the way the further timeline sensors already do (D9).
2. **Where each scenario goes** (D3–D10). Each moves whole, under the requirement it fits best:
   - Auto-discovery: "Discovery configuration is published on first publish" with discovery; "Re-publishing targets the same identities, not duplicates" with identity.
   - Verdict: "Verdict state and attributes are published from the document" with the verdict and its details; "The attributes payload leaves the timeline out" and "An empty timeline leaves the attributes payload as it was" with leaving out the timeline; "Null score is published as null, with availability requiring non-null" with the score.
   - Top target: "Top-target discovery and state are published" with discovery; "Existing entities are unchanged" with identity; "Empty target list renders unavailable" with the empty list.
   - Narrative: "Disabled narrative delivery publishes no entity" with disabled; "Narrative discovery and state are published when enabled and a narrative exists" with discovery; "A prior retained narrative is not shown as current" with the active unavailable publish; "Enabled but missing narrative renders unavailable without blocking the verdict" with holding back no other entity; "Existing entities are unchanged" with identity.
   - Rank: "Rank discovery is published for every rank" with a sensor for every rank; "A filled rank shows its target" and "A filled rank falls back to the catalog id" with a filled rank; "An empty rank renders unavailable" with an empty rank; "A shrinking list clears the old ranks" with updating every rank; "Existing entities are unchanged by the rank sensors" with discovery and identity.
   - Health: "Health discovery is published per provider" with discovery; "A successful fetch sets the last-success time" and "No success since a restart resolves to unknown" with the state; "Startup clears retained health before going online" with the startup reset; "A failed startup reset does not go online" with the reset after a drop; "The attributes list the provider's variables" and "The air-quality provider lists variables the timeline does not show" with the provider and variables; "A partly failed computation is ok and keeps its error" with the latest fetch; "A failed fetch keeps the earlier success" with the issue time, since its last THEN asserts the issue time from the earlier success; "The computed source's health names its inputs" and "Other providers carry no inputs" with `inputs`; "A failed computation keeps the earlier inputs" with a failed fetch leaving the details unchanged; "A failing provider keeps its health sensor available" with availability; "Existing entities and the verdict document are unchanged" with health beside the document.
   - Cloud cover: "The state is the current hour's cloud cover" with the state; "A missing or null current hour renders unknown" and "An empty timeline renders unknown" with unknown and available.
   - Further timeline: "A timeline sensor's discovery is published", "The first eight sensors are unchanged by the weather sensors" and "The cloud range sensors come last" with the sixteen keys; "Existing entities are unchanged by the timeline sensors" with discovery and identity.
3. **Add four scenarios, each backed by an existing test** (D11). Each goes to a new requirement that none of the original scenarios fits:
   - "An unnamed top target shows its designation", under "The top-target sensor shows the top target's name and the ordered list": an unnamed top target's state is its designation. `test_state_falls_back_to_id_when_no_common_name` asserts it.
   - "A narrative entity from an earlier configuration is left in place", under "A narrative entity left by an earlier configuration is not removed automatically": while disabled, the adapter publishes nothing to the narrative discovery topic, not even an empty removal. `test_disabled_delivery_publishes_no_narrative` asserts that no narrative topic gets a message.
   - "The narrative state does not carry the prose", under "The narrative prose is published in the attributes, not the state". `test_enabled_present_publishes_prose_in_attributes_with_short_state` asserts it. The scenario does not name the marker `ready`, because the requirement says only "a short marker".
   - "Each health sensor is named after its provider", under "Each configured provider has a health sensor named after it". It turns the requirement's example names into a scenario. `test_health_discovery_validates_and_is_a_diagnostic_timestamp` asserts "Open-Meteo health", and `pierpressure/core/providers.py` names 7Timer! "7Timer!".

   Alternative: join each of these requirements to a neighbor so that an original scenario covers it. Each join either runs past 500 characters or puts two behaviors under one heading.
4. **Reword only so each requirement reads on its own** (D15):
   - Each requirement that starts mid-story names its entity again: "the verdict entity's attributes payload", "the top-target sensor's state", "the narrative sensor's JSON attributes payload", "a rank sensor's rank", "a health sensor's state", "the Cloud cover sensor's state".
   - "Each entity's unique identity" becomes "The unique identity of the verdict, score and refresh entities", which is what "each entity" meant in the original.
   - "The system SHALL NOT attempt to auto-remove a narrative entity" gains "When narrative delivery is disabled", the condition of the paragraph it sat in.
   - "but no narrative is available for a publish — its provider failed or returned nothing —" becomes "but a publish has no narrative, because its provider failed or returned nothing,". "published retained" becomes "retained", and "an earlier retained narrative" becomes "an earlier narrative", in the same sentence. These keep the meaning and bring the requirement to 492 characters.
   - "When no entry has that hour" becomes "When no timeline entry has the hour that contains the document's generation timestamp", because "that hour" pointed to the sentence before.
   - "If the connection drops before the reset reaches the broker" becomes "before the startup health reset reaches the broker".
   - "for the computed source only, `inputs`" becomes "For the computed source only, the health sensor's JSON attributes SHALL carry `inputs`". The health attribute list's "SHALL carry" opens each of its four requirements.
   - So the count goes from 68 SHALL (9 SHALL NOT) to 71 SHALL (9 SHALL NOT), with no MAY. The 3 more are the repeated "SHALL carry". Per original: 5 → 5, 8 → 8, 7 → 7, 10 → 10, 10 → 10, 22 → 25, 3 → 3 and 3 → 3 SHALL. Nothing new is required, and nothing is dropped.
5. **No pointers to change** (D12). No spec quotes a removed heading, and none of the 8 points to another requirement.
6. **No drift to report** (D14).
7. **Headings use the spec's own words** (D16). No ADDED heading repeats one the delta removes or one the spec keeps. "The Cloud cover sensor's state is the current-hour cloud cover" is close to the removed "The Cloud cover state is the current hour's value", and differs from it. Two scenarios called "Existing entities are unchanged" move under different requirements. Their bodies differ, so the epic's check tells them apart.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from the main spec. It copies each scenario block exactly as its source requirement has it, and fails if a name matches no block or more than one inside that requirement, or if a source scenario is left unplaced.
9. **Accept archive's order.** The 37 new requirements land at the end of the spec. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: ha-delivery` with exactly the 4 added scenarios. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 71 SHALL, 9 of them SHALL NOT, and no MAY expected (Decision 4). The plan review compares each original with its parts.
- [An added scenario asserts something the code does not do] → Each rests on an existing test (Decision 3). The code review checks them against `pierpressure/delivery/mqtt.py`.
- [Two requirements sit close to the limit] → "With no narrative, the enabled narrative sensor is published as unavailable" is at 492 characters, and "The verdict, score and refresh entities are announced by discovery" at 476. A later change that MODIFIES one and adds words may need to split it again.
- [The spec loses its grouping, so a reader finds the entity rules after the broker rules] → Accepted for now (Decision 9). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
