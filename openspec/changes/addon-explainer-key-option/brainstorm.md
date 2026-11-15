**Why:** An add-on user who wants the explainer must type its API key in plain text into `config.yaml`, a file the Supervisor backs up. The add-on cannot pass the key in from the environment. The form now reads in one voice (#101), so the key can get a hidden field there.

## Story

#150 addon-explainer-key-option — the add-on form takes the explainer key as a password field.
<https://github.com/andrewduckett/pier-pressure/issues/150>

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | One optional field on the form for `explainer.api_key` that hides its value; how the service combines it with `config.yaml`; its label and description; and the add-on's `DOCS.md`. Other explainer settings stay in `config.yaml` (#88). The FIRMS key stays out. | Evidence: #150 packet |
| D2 | What is the field's name and shape? | An `explainer` block with one field, `api_key`, of type `password?`, and `explainer: {}` in `options`, not a flat `explainer_api_key`. The name matches `config.yaml`, as the `mqtt` block does, and nesting works on the form. | Assumption |
| D3 | Where does it sit on the tab? | Last, after MQTT broker, as its own section. It is the least-used part, and the tab's order up to the broker stays as #101 left it. | Assumption |
| D4 | Does a key on the form turn the explainer on? | No. It sets only `explainer.api_key`. `explainer.enabled` and `explainer.model` stay in `config.yaml`, and a key with the explainer off does nothing, as it does in a file. | Evidence: #150 Scope; `ExplainerConfig` in `pierpressure/core/config.py` |
| D5 | How does the form's key combine with `config.yaml`? | The key joins the file's `explainer` block key by key, as the form's `mqtt` block joins the file's. A key in both stops the add-on with an error that names `explainer.api_key` and never its value. A file `explainer` that is not a mapping is a combine error whatever the form holds, as `mqtt` is. | Evidence: ADR 0021; `_check_broker` in `pierpressure/addon_settings.py` |
| D6 | What does an empty key field mean? | Not set. A missing, null, empty or blank key gives the core no `explainer` block from the form, so the file's key, or none, applies. | Evidence: `openspec/specs/ha-addon/spec.md`, "An empty or blank form field counts as not set" |
| D7 | Can the key leak? | No startup log line, combine error or configuration error contains the form's key, as for the broker password. What a failed provider call logs is #92's, for a key from either place. | Evidence: `openspec/specs/ha-addon/spec.md`, "No log line or error reveals the form's broker password"; #92 |
| D8 | What do the label and description say? | The section, **Explainer**, says `Optional.`, what the explainer writes, and that `explainer.enabled` in `config.yaml` turns it on. The field, **API key**, says `Optional.`, whose key it is, that the form hides it as you type, and to set it here, not in `config.yaml`. | Evidence: archived `addon-form-text` D3, D6 |
| D9 | What changes in `DOCS.md`? | The setup steps gain an **Explainer** step after **MQTT broker**. A new "Turn on the explainer" section puts the key on the tab, and `enabled` and `model` in `config.yaml`. "More settings" names four parts. The `config.yaml` sections name the key as a tab setting. | Assumption |
| D10 | Does `docs/llm-explainer.md` change? | One sentence: in the add-on, put the key on the Configuration tab, as the add-on's `DOCS.md` says. Its environment-variable advice does not work there. | Assumption |
| D11 | How is it accepted? | Tests check the schema, `options`, labels and `Optional.` rule. They check the setup steps and "More settings" in the tab's order. They check the translation, the combine and its conflict, and that a form key reaches the explainer but no startup error. | Assumption |

## Changes from the story

- Renamed the field from `explainer_api_key` to `explainer.api_key`, a block
  with one field (D2), so its name matches `config.yaml`, as the broker's does.
- Added `docs/llm-explainer.md` (D10), so its advice to use an environment
  variable does not mislead an add-on user.
- Left what a failed provider call logs to #92 (D7). It applies to a key from
  the form or the file alike.

Confirmed by user: yes
