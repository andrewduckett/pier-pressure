## Why

PierPressure names the telescope and camera on a pier in two ways. The
`pier-equipment` spec calls it "equipment", but the config key, the code, and the
verdict's reason sentences call it a "rig". The add-on form (#67) is about to add
field names for these settings. Renaming first means the form matches the config
file from day one, and no form field has to be renamed later.

Nobody uses PierPressure yet, so this is a plain rename with no migration.

Story: #68 "rename-rig-to-equipment — the config and verdict say 'equipment',
not 'rig'".

## What Changes

- **BREAKING** — The per-pier config key `rig:` becomes `equipment:`. There is no
  alias and no special error for the old key. A pier that still says `rig:` is
  skipped, with the same logged "extra inputs are not permitted" error as any
  unknown key. The other piers keep running. Startup fails only when no valid pier
  remains.
- The four framing sentences in the verdict's `reasons[]` stop naming the
  equipment and name the field of view instead:

  | Today | After |
  |---|---|
  | Top pick Andromeda Galaxy frames well in your rig. | Top pick Andromeda Galaxy frames well in your field of view. |
  | Top pick Andromeda Galaxy is larger than your rig's field of view. | Top pick Andromeda Galaxy is larger than your field of view. |
  | Top pick Andromeda Galaxy is small in your rig's field of view. | Top pick Andromeda Galaxy is small in your field of view. |
  | Top pick Andromeda Galaxy fills most of your rig's field of view. | Top pick Andromeda Galaxy fills most of your field of view. |

  This changes wording only. When each sentence appears, and what it means, stay
  the same.
- In the code, "Equipment" is the name of the entity. The `Rig` class becomes
  `Equipment`, and `PierConfig.rig` becomes `PierConfig.equipment`. Function
  parameters, the ranking cache key helper, and test helpers and constants
  follow the same name.
- The README, `openspec/prd.md`, `openspec/discovery.md`, and the
  `pier-equipment` and `target-ranking` specs use "equipment" wherever they name
  the entity.
- "Rig" is not banned. Code comments, docstrings, and test prose may still say
  "rig" as an informal word, such as "a widefield rig". They change only where
  the word names the entity.

Out of scope:

- Archived OpenSpec changes and accepted decision records keep their wording as a
  historical record.
- The golden verdicts need no change. None of the golden piers has equipment set
  up, so no golden verdict contains a framing sentence. The new wording is checked
  by the producer and ranking tests instead.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pier-equipment`: the requirements name the entity "equipment" and the config
  key `equipment`. Two requirement titles that say "rig" are renamed.
- `target-ranking`: the scoring requirement says "equipment" in place of "rig".
  A new requirement states the four framing sentences and when they appear. No
  spec stated them before.

## Impact

- **Config:** the per-pier key `rig:` becomes `equipment:`. This breaks any
  existing config file, but none exists in use.
- **Verdict document:** the wording of four `reasons[]` sentences changes. No
  field, topic, entity, or entity mapping changes.
- **Code:** `pierpressure/core/config.py`, `pierpressure/core/ranking.py`, and
  `pierpressure/core/producer.py`.
- **Tests:** `tests/test_equipment.py`, `tests/test_producer_targets.py`,
  `tests/test_ranking_pipeline.py`, `tests/test_ranking_suitability.py`, and
  `tests/test_validation_night.py`.
- **Docs:** `README.md`, `openspec/prd.md`, and `openspec/discovery.md`.
- **Add-on:** no change. `ha-addon/` does not mention the equipment yet; #67 adds
  it under the new name.
