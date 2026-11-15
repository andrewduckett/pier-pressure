## 1. Form help text and setup steps

- [x] 1.1 [easy] Each optional form field's description says `Optional.`, the broker's `host` included, and no required field's description says it (verify: uv run pytest tests/test_ha_addon.py -k optional) (✓ uv run pytest tests/test_ha_addon.py -k optional passed)
- [x] 1.2 [easy] The description of `interval_seconds` names seconds, its default of 900, and that a pier's Refresh button recomputes at once (verify: uv run pytest tests/test_ha_addon.py -k interval) (✓ uv run pytest tests/test_ha_addon.py -k interval passed)
- [x] 1.3 [easy] The description of `piers` names the Location, Horizon, Equipment and Verdict sections in order, and says each field's label starts with its section (verify: uv run pytest tests/test_ha_addon.py -k piers_intro) (✓ uv run pytest tests/test_ha_addon.py -k piers_intro passed)
- [ ] 1.4 [easy] The description of `mqtt` names `config.yaml` and the Mosquitto add-on as where the broker comes from with no host (verify: uv run pytest tests/test_ha_addon.py -k broker_section)
- [ ] 1.5 [easy] The descriptions of the broker's `port`, `username` and `password` each say the field is set only with a host (verify: uv run pytest tests/test_ha_addon.py -k needs_a_host)
- [ ] 1.6 [medium] The "Set up the add-on" section of `ha-addon/DOCS.md` names in bold the Recompute interval, Piers, Pier ID, Location, Horizon, Equipment, Verdict and MQTT broker, in the tab's order, and the order check fails on a section that names a part too early (verify: uv run pytest tests/test_ha_addon.py -k setup_steps)
- [ ] 1.7 [easy] The "More settings" section of `ha-addon/DOCS.md` lists what the tab shows by its parts, in the tab's order (verify: uv run pytest tests/test_ha_addon.py -k more_settings)
- [ ] 1.8 [easy] The whole project's checks pass, and the schema, service and form-to-verdict tests are unchanged (verify: mise run check)
