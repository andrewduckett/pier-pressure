## 1. The Supervisor's scan

- [x] 1.1 [easy] A test helper in `tests/test_ha_addon.py` applies the Supervisor's add-on scan rule to a list of repository paths: it keeps a path whose file name starts with `config.` and whose suffix is `.yaml`, `.yml` or `.json`, and drops it when any path part starts with `.` or is named `rootfs`. Its docstring cites home-assistant/supervisor@98a2322 `supervisor/store/data.py:158-164` (brainstorm D2). Checked on synthetic paths: `docs/examples/config.sample.yaml` matches, while `.github/config.yml`, `x/rootfs/config.json`, `a/config.txt` and `vite.config.ts` do not (verify: uv run pytest tests/test_ha_addon.py -k supervisor_scan) (✓ uv run pytest tests/test_ha_addon.py -k supervisor_scan passed)
- [x] 1.2 [easy] A test applies that rule to the output of `git ls-files` and asserts that the matches are exactly `ha-addon/config.yaml` and `openspec/config.yaml`. On failure its message names each extra path. Today it fails and names `docs/examples/config.explainer.yaml` (brainstorm D3, D7) (verify: uv run pytest tests/test_ha_addon.py -k supervisor_scan) (✓ uv run pytest tests/test_ha_addon.py -k supervisor_scan failed as planned, naming docs/examples/config.explainer.yaml)
- [ ] 1.3 [easy] The explainer sample config lives at `docs/examples/explainer-config.yaml` (moved with `git mv`), and `tests/test_explainer_docs.py` loads it from there, so the 1.2 test passes and the sample still enables the explainer (brainstorm D6) (verify: uv run pytest tests/test_ha_addon.py tests/test_explainer_docs.py)

## 2. The docs

- [ ] 2.1 [easy] `ha-addon/DOCS.md` has a section `## If the Supervisor log warns about openspec/config.yaml`, placed after the other "If …" sections. It quotes `Can't read …/openspec/config.yaml: Invalid app config!`, says that the Supervisor reads every `config.yaml` in the repository and that this file is the project's planning config, not an add-on, and says the warning is harmless and needs no action. A test checks that the section exists, quotes `openspec/config.yaml: Invalid app config!` and says `no action` (brainstorm D5, D8) (verify: uv run pytest tests/test_ha_addon.py -k supervisor_warning)
- [ ] 2.2 [easy] In the README's add-on install section, step 1, which adds the repository URL, has one sentence that links to that DOCS.md section by its anchor (`ha-addon/DOCS.md#if-the-supervisor-log-warns-about-openspecconfigyaml`). A test checks the link (brainstorm D8) (verify: uv run pytest tests/test_ha_addon.py -k supervisor_warning)

## 3. Integration

- [ ] 3.1 [easy] The whole change passes the CI gate (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
