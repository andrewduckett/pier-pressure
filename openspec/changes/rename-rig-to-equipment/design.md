## Context

See proposal.md for why the rename happens now. Three facts shape how to do it:

- `PierConfig` sets `extra="forbid"`. A leftover `rig:` key therefore already
  makes that pier invalid, with Pydantic's "Extra inputs are not permitted"
  error. `validate_piers` logs and skips the pier, and the other piers keep
  running. Startup fails only when no valid pier remains. No new code is needed
  to reject the old key.
- Before this change, no spec stated the four framing sentences word for word.
  The target-ranking delta now adds them as a requirement. Only two tests check
  their wording: `tests/test_producer_targets.py` looks for "rig" in a reason,
  and `tests/test_ranking_suitability.py` looks for "frames well", "small",
  "fills most", and "larger than".
- OpenSpec has no way to rename a scenario. A MODIFIED requirement must keep
  every scenario title the main spec already has, and a requirement title cannot
  appear in both ADDED and REMOVED.

## Goals / Non-Goals

**Goals:**

- One formal name, "equipment", for the entity in config, code, specs, and docs.
- Tests that pin the four new framing sentences exactly, so a later wording
  change is a deliberate act.

**Non-Goals:**

- Any change to how the field of view is derived, how framing is scored, or
  when a framing sentence appears.
- Removing the informal word "rig" from comments, docstrings, and test prose.

## Decisions

### D1 — "Equipment" names the entity; "rig" may stay as an informal word

The class becomes `Equipment` and the field becomes `PierConfig.equipment`.
Every identifier that holds or names an instance follows the same name. For
example, `_rig_key` becomes `_equipment_key`, the `rig` parameter becomes
`equipment`, and `_WIDEFIELD_RIG` becomes `_WIDEFIELD_EQUIPMENT`.

Prose follows a looser rule. A comment such as "a widefield rig" may stay. A
comment or docstring changes only where "rig" names the config entity, such as
"the pier's optional rig".

*Alternative: remove every "rig".* Rejected. "Equipment" is a mass noun, so
phrases such as "two rigs" would become clumsy ("two sets of equipment") with no
gain in clarity.

### D2 — The framing sentences name the field of view

All four sentences end in "your field of view", for example "Top pick M31 frames
well in your field of view." The story suggested "frames well in your
equipment". That phrasing reads awkwardly, because "equipment" is a mass noun.
The field of view is also what the sentence is actually about.

*Alternative: "your equipment's field of view".* Rejected. It is longer and adds
nothing, because the user has only one set of equipment per pier.

### D3 — Tests pin each sentence exactly

The two wording tests switch from substring checks to exact matches on all four
sentences. The producer test also stops looking for "rig" and checks for the
exact framing sentence. These assertions are written first and fail against the
current wording (test-driven development).

### D4 — How the spec deltas carry the rename

- **pier-equipment:** the delta REMOVES both requirements and ADDS them back
  under new titles: "Equipment is optional on each pier" and "Field of view is
  derived offline from the equipment". This is the only way to rename their
  scenarios. The ADDED text also names the `equipment` key and states that a
  `rig` key is rejected.
- **target-ranking:** the delta MODIFIES "Targets are scored and ordered
  deterministically" and keeps its two scenario titles that say "rig". Removing
  and re-adding the core ranking requirement just to rename two titles would
  bury a wording change in a large delta.
- **In the archive commit:** after the archive syncs the deltas, the same commit
  edits the main specs directly. It renames those two target-ranking scenario
  titles, and it rewords the pier-equipment Purpose, which a delta cannot change.
  The archive commit stays the last commit on the branch, as the workflow
  requires.

*Alternative: RENAMED plus MODIFIED for pier-equipment.* Rejected. Validation
still compares the renamed requirement's scenario titles against the old ones,
so it fails.

## Risks / Trade-offs

- [A Home Assistant automation matches on the old reason wording] → Nobody uses
  PierPressure yet, and the README documents no automation that reads
  `reasons[]` text.
- [The archive sync leaves two "rig" scenario titles in the main specs] → The
  archive commit includes the direct edit, so no commit on the branch has them.
- [A missed identifier keeps the old name] → A final task searches the live tree
  for `\brigs?\b` and reviews each remaining hit against D1.

## Migration Plan

None is needed. The rename has no alias, and no deployed config exists. To roll
back, revert the PR.
