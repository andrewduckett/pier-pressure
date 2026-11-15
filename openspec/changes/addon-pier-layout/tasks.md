## 1. Section-prefixed pier labels

- [x] 1.1 [easy] Each pier field's English label is the one the spec's section table gives it, the schema lists the pier fields in that table's order after `id`, and `id` is labelled `Pier ID` (verify: uv run pytest tests/test_ha_addon.py -k section_label) (✓ uv run pytest tests/test_ha_addon.py -k section_label passed)
- [x] 1.2 [easy] The descriptions of `latitude`, `min_altitude`, `equipment_focal_length_mm` and `go_threshold` open with `Location:`, `Horizon:`, `Equipment:` and `Verdict:` and one introducing sentence, and no other pier field's description opens with a section name and a colon (verify: uv run pytest tests/test_ha_addon.py -k section_intro) (✓ uv run pytest tests/test_ha_addon.py -k section_intro passed)
- [ ] 1.3 [easy] Every pier field's description is the labelled trial's text, and none names an old label such as `Focal length` or `Horizon points`, while each number still names its unit and the gate fields still name their defaults (verify: uv run pytest tests/test_ha_addon.py)
- [ ] 1.4 [easy] `ha-addon/DOCS.md` names each pier field by its new label in bold text, field tables and label-to-`config.yaml` tables, and keeps headings and prose that name a setting as an idea (verify: uv run pytest tests/test_ha_addon.py -k docs_label)
- [ ] 1.5 [easy] The whole project's checks pass with the new labels, and the schema, service and form-to-verdict tests are unchanged (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
