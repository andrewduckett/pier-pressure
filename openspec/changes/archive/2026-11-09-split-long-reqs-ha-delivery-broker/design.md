## Context

- OpenSpec 1.16.0 warns when the prose of a requirement is over 500 characters. It checks ADDED requirements in a delta, and the main spec again after archive. It does not check MODIFIED requirements in a delta.
- Strict validation also rejects an ADDED requirement with no scenario, or with no SHALL or MUST in its prose.
- One delta cannot REMOVE and ADD the same heading (epic #230 decision 5). Archive deletes each REMOVED requirement and appends the ADDED ones at the end of the main spec.
- The 6 long requirements hold 42 scenarios, 67 SHALL (18 of them SHALL NOT) and 6 MAY.
- "Delivery failures are reported, not swallowed" states five behaviors but has only 4 scenarios.
- Two of the six use an unquoted pointer: "as the reconnect requirement describes" and "as the startup requirement describes". No spec quotes any of the six headings.
- This branch stacks on `split-long-reqs-ha-addon-broker` (PR #260). The local `main` is stale, so the epic's check uses `TARGET=split-long-reqs-ha-addon-broker`.

## Goals / Non-Goals

**Goals:**

- After archive, each of the 33 new requirements states one behavior in no more than 500 characters.
- After archive, the spec holds every one of its scenario blocks word for word, plus the 1 added on purpose.
- After archive, no quoted pointer in any main spec names a heading that does not exist.

**Non-Goals:**

- Splitting the other long `ha-delivery` requirements. #241 does that.
- Editing the test docstrings that restate a removed heading (D11). The epic changes no code or test.
- Reordering requirements inside the main spec.

## Test Seams

This change has no code, so the seams are the OpenSpec CLI and the epic's check.

- **Primary test seam:** `openspec validate split-long-reqs-ha-delivery-broker --strict` before archive, and the scenario-preservation check from epic #230 decision 6 after archive, with `CAPS=ha-delivery`.
- **Existing seams reused:** `openspec validate --specs` for the warning count, the pointer check from #239's tasks, which resolves every quoted requirement heading in `openspec/specs`, and `mise run check` to show that nothing else moved. The added scenario rests on an existing test in `tests/test_publish.py`. Adding a test is out of scope, because epic #230 changes no test.

## Scrutiny Tier & Blast Radius

- **Tier:** low
- **Blast radius:** the text of one main spec, `openspec/specs/ha-delivery/spec.md`. Three test docstrings restate a removed heading and stay as they are (D11). Nothing reads them.

## Decisions

1. **One requirement per behavior, following the original's own sentences, bullets and paragraphs.** The parts are:

   | Removed | Added |
   |---|---|
   | Persistent operation with periodic republish | The process publishes a verdict at startup and on an interval; Discovery, state, attributes and availability are published retained |
   | Availability reflects process liveness via last-will | The process registers a retained offline last-will; The process publishes a retained online availability while running; A planned stop publishes a retained offline availability; A planned stop waits at most two seconds for the offline message; A planned stop while disconnected publishes no offline message |
   | Delivery failures are reported, not swallowed | A delivery failure is logged, not reported as success; A failed publish does not stop the process; A publish held while disconnected is not logged; A refused publish is logged once as a warning; A refused online availability is sent again with the next verdict |
   | The process waits for the broker at startup | The process keeps trying to connect to the broker at startup; After a temporary failure at startup, the process pauses and tries again; The pauses between connection attempts grow from 1 to 120 seconds; The process may try once more at once with one detail changed; Each failed connection attempt is logged without the password; The process publishes only once the broker accepts the connection; A rejected login at startup stops the process |
   | The process restores delivery after a reconnect | The process keeps trying to reconnect while it runs; After a reconnect, the process subscribes again and republishes its last state; After a reconnect, the online availability follows the republished state; The MQTT client may send a message again after a reconnect; A refused refresh subscription is logged with its topic; A reconnect triggers no new verdict; A reconnect does not change the startup order; The outage and each reconnect are logged without the password; A rejected login during a reconnect is logged, and the process keeps trying; While disconnected, the process holds its publishes for the replay |
   | An error about the broker settings shows none of their text | An error about the mqtt block shows none of its values; An error about the mqtt block names no key the block does not define; An error about the mqtt block says what is wrong; The broker password is masked once the settings are valid |

   These stay together on purpose:
   - "The process SHALL NOT depend on Home Assistant" stays with publishing at startup and on an interval. Both scenarios assert a publish "without any external trigger", and no other scenario tests it.
   - "Both the online message and the last-will are retained, so a later subscriber reads offline" stays with the last-will. It is the reason the last-will is retained.
   - The three ways an attempt fails, and the definitions of a rejected login and a temporary failure, stay with the pause after a temporary failure. That requirement is the first to need them, and they hold no SHALL of their own.
   - The best-effort note on the offline publish goes with the two-second wait. It says what happens when the broker never confirms.
   - "A reconnect is any accepted connection after the first one" goes with "A reconnect does not change the startup order", beside "The first accepted connection is not a reconnect".
   - The two paragraphs on messages the MQTT client already holds, one still being sent at the drop and one handed over before the process learns of the drop, form one requirement. Both say the MQTT client may send a message again outside the process's order. Neither fits the 500-character limit beside the order or the hold.
   - "This order covers the messages the process publishes after the reconnect" goes with the order.
2. **Where each scenario goes** (D3–D8). Each moves whole, under the requirement it fits best:
   - Republish: "State is published on startup" and "State refreshes on the configured interval" with the interval; "Discovery, state, and availability are published retained" with the retain flag.
   - Last-will: one each to the last-will, online, two-second wait and stop-while-disconnected requirements; "A planned stop publishes a retained offline before disconnecting" and "A termination signal stops the process cleanly" with the planned stop.
   - Failures: "Unreachable broker is reported as a failure" with the log; "A publish during an outage does not stop the process" with keeping running; "A refused publish is logged and the process keeps running" with the single warning; "A refused online availability is published again" with sending it again.
   - Startup: "The broker starts after the process" with keeping trying; "A broker that is not ready is tried again" and "A broker that closes the connection is tried again" with the pause after a temporary failure; "The pauses grow to a limit" with the pauses; "A failure during an immediate try is tried again" with the immediate tries; "Each failed attempt is logged" with the log; "Nothing is published while attempts fail" with publishing only once accepted; "A wrong username or password stops the process" and "An unauthorized client stops the process" with the rejected login.
   - Reconnect: "A failed immediate try during a reconnect is tried again" with keeping trying; "Refresh works again after a reconnect", "Entities come back online after a reconnect" and "A broker that lost its retained messages gets them back" with the three steps; "The last state is published again before online" with the order; "A message still being sent at the drop does not change the order" with the MQTT client's own resends; "A refused subscription is logged" with the subscription; "A reconnect computes no new verdict" with no new verdict; "The first connection is not a reconnect" and "A reconnect during startup keeps the startup order" with the startup order; "The outage is logged" with the log; "A login rejected during a reconnect does not stop the process" with the rejected login; "State published during an outage is restored after the reconnect" and "Nothing is handed to the MQTT client while the process knows it is disconnected" with the hold.
   - Settings error: "The add-on's combined settings do not show the password" with no values; "An unknown key in the mqtt block is not named" and "An unknown key with a value is not named in the add-on" with undefined keys; "A password that is not text is rejected without its value" and "An mqtt block that is not a mapping does not show its value" with saying what is wrong, since each asserts the message as well as the missing value; "A valid password is masked when the settings are printed" with the mask.
3. **Add one scenario, backed by an existing test** (D9). "A publish held while disconnected is not logged" has none of the original's scenarios. "A publish held during an outage logs no warning" says: while disconnected, the process publishes a verdict and its online availability, and the log has no warning for them. `test_a_publish_paho_queued_while_disconnected_logs_no_warning` asserts exactly that. Alternative: join the rule to "A failed publish does not stop the process". That puts two behaviors under one heading.
4. **Reword only so each requirement reads on its own** (D13):
   - The planned-stop bullets become sentences. "The process SHALL wait at most two seconds" becomes "When the process stops on purpose while connected, it SHALL wait at most two seconds", which keeps the condition of the bullet before it (plan review, finding 1), and "When the process stops while its connection is down" becomes "stops on purpose while its connection is down". The bullets sat under "a planned stop", so the meaning is the same.
   - "for any other reason" becomes "for a reason other than a lost connection", because "other" pointed to the previous paragraph. The scenario uses the same words.
   - "An attempt fails in one of three ways" becomes "An attempt to connect to the broker fails". "No pause SHALL be" becomes "No pause between connection attempts SHALL be". "each failed attempt" becomes "each failed attempt to connect". "After a rejected login" becomes "After a rejected login at startup", since the reconnect rule for a rejected login differs.
   - "In this requirement, to publish a message means" becomes "After a reconnect, to publish a message means", so the definition still covers every reconnect requirement.
   - "for step 2" and "which step 3 then publishes" become "for the republish after the reconnect" and "which it publishes after that republish". "before or after step 2" becomes "before or after the republish of each pier's last state". "only after it has published the state in step 2" becomes "only after it has published each pier's last state again".
   - "The error SHALL still say what is wrong" becomes "An error about the `mqtt` block SHALL still say what is wrong". The unknown-key bullet becomes "For such a key, the error SHALL say …" in the undefined-key requirement. That requirement says "from any source of settings" instead of repeating "This SHALL hold for every source".
   - "The process does not hold such a message back" becomes "The process SHALL NOT hold such a message back". Its requirement needs a SHALL to pass strict validation, and its scenario already asserts "it does not withhold or remove the message the MQTT client was still sending". +1 SHALL NOT.
   - So the count goes from 67 SHALL (18 SHALL NOT) and 6 MAY to 68 SHALL (19 SHALL NOT) and 6 MAY. Per original: 4 → 4, 8 → 8, 10 → 10, 17 → 17, 19 → 20, 9 → 9 SHALL, and the MAY count stays 3 for the startup and 3 for the reconnect requirement. Nothing new is required, and nothing is dropped.
5. **Quote the two unquoted pointers** (D10). "as the reconnect requirement describes" names "While disconnected, the process holds its publishes for the replay". "as the startup requirement describes" names "The process may try once more at once with one detail changed". "the `ha-addon` capability describes" names a capability, not a heading, and stays. Each quoted heading sits on one line, so a line-based search finds it (plan review, finding 3).
6. **No drift to report** (D12).
7. **Headings use the spec's own words** (D14). No ADDED heading repeats one the delta removes or one the spec keeps. A few headings are close to a scenario's name, such as "A reconnect triggers no new verdict" beside the scenario "A reconnect computes no new verdict". They differ, so no pointer check confuses them.
8. **Copy scenarios with a script.** A script under `.workspace/` builds the delta from a template. It copies each named scenario block exactly as the main spec has it, and fails if a name matches no block or more than one.
9. **Accept archive's order.** The 33 new requirements land at the end of the spec. This is what the pilot chose (#231, design Decision 2).

## Risks / Trade-offs

- [A scenario changes in copying] → The script copies blocks byte for byte. After archive, the epic's check must print `OK: ha-delivery` with exactly the 1 added scenario. Any other result fails the task.
- [A SHALL is dropped or its meaning changes] → Count the normative words in the ADDED requirements: 68 SHALL, 19 of them SHALL NOT, and 6 MAY expected (Decision 4). The plan review compares each original with its parts.
- [The added scenario asserts something the code does not do] → It rests on an existing test (Decision 3). The code review checks it against `pierpressure/delivery/mqtt.py`.
- [One requirement sits at exactly 500 characters] → "After a reconnect, the process subscribes again and republishes its last state" is at the limit, which OpenSpec allows. A later change that MODIFIES it and adds words will need to split it again.
- [Three test docstrings restate a removed heading] → Accepted (D11). The pull request names them for a later change that may edit tests.
- [The spec loses its grouping, so a reader finds the broker rules away from the requirements #241 leaves] → Accepted for now (Decision 9). Reordering is a separate change that touches no requirement text.

## Migration & Rollback

N/A. Nothing changes shape. To roll back, revert the archive commit.
