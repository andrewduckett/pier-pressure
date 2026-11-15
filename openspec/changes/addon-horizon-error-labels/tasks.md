## 1. Form labels in the both-horizon-fields error

- [x] 1.1 [easy] The core's error for a horizon with more than one source is its own `ValueError` subclass, which carries the source names it found by their `config.yaml` names, and its message is unchanged (verify: uv run pytest tests/test_horizon_config.py -k horizon_sources_error) (✓ uv run pytest tests/test_horizon_config.py -k horizon_sources_error passed)
- [x] 1.2 [easy] `validate_piers` logs a skipped pier's error as an optional error-writing function writes it, and as the core writes it today when no function is given (verify: uv run pytest tests/test_config.py -k pier_error_writer) (✓ uv run pytest tests/test_config.py -k pier_error_writer passed)
- [x] 1.3 [easy] `build_config` passes an error-writing function given as a keyword argument to the per-pier check, and without one it logs today's line (verify: uv run pytest tests/test_config.py -k build_config_error_writer) (✓ uv run pytest tests/test_config.py -k build_config_error_writer passed)
- [x] 1.4 [easy] The add-on's label for each horizon key, `min_altitude` and `points`, matches the label of its form field in `ha-addon/translations/en.yaml` (verify: uv run pytest tests/test_ha_addon.py -k horizon_error_labels) (✓ uv run pytest tests/test_ha_addon.py -k horizon_error_labels passed)
- [x] 1.5 [medium] For a form pier that sets both horizon fields, the add-on's error-writing function writes `Horizon: floor and Horizon: points are both filled in on the Configuration tab. Fill in one of them at most.` in place of the core's horizon-source error (verify: uv run pytest tests/test_addon_settings.py -k horizon_error_in_labels) (✓ uv run pytest tests/test_addon_settings.py -k horizon_error_in_labels passed)
- [x] 1.6 [easy] The add-on's error-writing function writes the core's error unchanged for a pier whose horizon came from `config.yaml`, and for any error that is not the horizon-source error (verify: uv run pytest tests/test_addon_settings.py -k horizon_error_keeps_file_names) (✓ uv run pytest tests/test_addon_settings.py -k horizon_error_keeps_file_names passed)
- [ ] 1.7 [medium] At startup, a form pier that sets both horizon fields is skipped with an error that names `Horizon: floor` and `Horizon: points` and not `min_altitude`, and the other pier publishes (verify: uv run pytest tests/test_main.py -k both_horizon_fields_name_labels)
- [ ] 1.8 [easy] At startup, a form pier that sets both horizon fields and a latitude of 95 is skipped with an error that names `latitude` and no form label (verify: uv run pytest tests/test_main.py -k field_error_before_horizon_error)
- [ ] 1.9 [easy] At startup, a form pier whose `config.yaml` entry gives a `horizon` block with `points` and `min_altitude` is skipped with an error that names both keys and no form label (verify: uv run pytest tests/test_main.py -k file_horizon_sources_keep_names)
- [ ] 1.10 [easy] The "Set a pier's horizon" section of `ha-addon/DOCS.md` says the error for both horizon fields names **Horizon: floor** and **Horizon: points** (verify: uv run pytest tests/test_ha_addon.py -k horizon_docs_name_error_labels)
- [ ] 1.11 [easy] Stage 4 of `openspec/discovery.md` says `supported` and links no issue, once a check of the code shows the fix is in (verify: test -z "$(grep -n 'issues/288' openspec/discovery.md)")
- [ ] 1.12 [easy] The whole project's checks pass (verify: mise run check)

## Deviations Ledger

- 2026-11-15, task 1.6: both tests passed at once, because task 1.5's function
  already returns the core's error when it does not reword. A mutation that
  ignored where the horizon came from failed the `config.yaml` test. A mutation
  that ignored what the error was failed the field-error test. So each test
  guards its behavior.
