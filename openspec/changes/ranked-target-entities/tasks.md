Practice TDD: for each behavior, write the failing test first, then implement.
`just check` (ruff lint, mypy strict, pytest) is the CI gate and must be green
before the PR is marked ready. New tests go in `tests/test_rank_targets.py` and use
the existing `FakeMqttClient` and `make_document` helpers.

## 1. Shared display-name rule

- [x] 1.1 Extract a helper in `pierpressure/delivery/mqtt.py` that returns a target's name, or its id when the name is null. Make `top_target_state` use it. Verify that `tests/test_top_target.py` still passes unchanged (design D4).

## 2. Rank topics and discovery

- [x] 2.1 Write failing tests for the rank topic helpers: rank `n` of pier `<pier>` uses `pierpressure/<pier>/target_<n>/state` and `.../attributes`. Implement the helpers and verify the tests pass (design D1).
- [x] 2.2 Write failing tests for the rank discovery builder: for each rank from 1 to `TOP_N`, the payload validates against the sensor schema in `ha_schema.py`, has the name `Target <n>`, and has the `unique_id` `pierpressure_<pier>_target_<n>`. It must also use the two-entry availability list with the `available` flag template and not disable the entity by default. Implement and verify (spec: "Rank discovery is published for every rank").

## 3. Rank state and attributes

- [x] 3.1 Write failing tests for a filled rank: the state is the target's name, and the attributes are `available: true` and `rank: n`, followed by the target's fields at the top level, with `window` still nested. Implement and verify (spec: "A filled rank shows its target"; design D2).
- [x] 3.2 Write a failing test that a filled rank whose target has no common name shows the target's id as its state. Verify it passes with the helper from 1.1 (spec: "A filled rank falls back to the catalog id").
- [x] 3.3 Write failing tests for an empty rank: the state is an empty string and the attributes are exactly `{"available": false, "rank": n}`. Implement and verify (spec: "An empty rank renders unavailable").

## 4. Publishing

- [ ] 4.1 Write failing tests that `publish_verdict` publishes retained discovery, state, and attributes for every rank from 1 to `TOP_N`, for a full list, a short list, and an empty list. Wire the rank sensors into `publish_verdict` in the order design D6 gives, and verify.
- [ ] 4.2 Write a failing test that publishing 5 targets and then 2 for the same pier leaves ranks 3 to 5 with `available: false` as their last retained attributes, and that no last retained state still names an earlier target. Verify it passes (spec: "A shrinking list clears the old ranks"; design D3).
- [ ] 4.3 Write a test that the verdict, score, top-target, and refresh entities publish the same topics and payloads as before. Also check that re-publishing for the same pier adds no new rank `unique_id`. Verify it passes, along with `tests/test_publish.py` and `tests/test_narrative_delivery.py` (spec: "Existing entities are unchanged by the rank sensors").

## 5. Documentation

- [ ] 5.1 Update `README.md`: add a `Target 1` to `Target 10` row to the entities table, add the rank topics to the MQTT topics table, and add the rank discovery topics to the entity-removal example. Verify by reading the rendered sections.
- [ ] 5.2 Update the Home Assistant section of `docs/target-ranking.md` to mention the rank sensors. Verify that `tests/test_docs.py` passes.

## 6. Gate

- [ ] 6.1 Run `just check` and verify that ruff, mypy, and pytest are all green.
