**Why:** When a form pier fills in both **Horizon: floor** and **Horizon: points**, the add-on skips it and logs an error that names `points` and `min_altitude`. Neither name is on the tab or in a label table, so the user cannot tell which fields to fix. This is the last loose end of epic #99's form work.

## Story

#288 addon-horizon-error-labels — a form pier with both horizon fields gets an error that uses their labels.
<https://github.com/andrewduckett/pier-pressure/issues/288>

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How are other form-pier errors worded today? | All of them name `config.yaml` keys, such as `equipment.sensor_height_mm`, `horizon.points`, `latitude` and `max_gust`, and the add-on's `DOCS.md` maps labels to keys in tables. No error uses a label, so there is no form-terms pattern to copy. | Evidence: startup probe through `load_app_config`; `ha-addon/DOCS.md`; ADR-0022, Consequences |
| D2 | Fix this error only, or every form-pier error? | This error only. Rewording every error changes the documented log format of every form-pier error. It needs a label for every field and an origin rule for each setting group. It also rewrites the equipment and verdict label tables in `DOCS.md`. That is bigger. | Assumption |
| D3 | How does the add-on recognise this error without parsing text? | The core raises its "more than one horizon source" error as its own `ValueError` subclass that carries the source names it found, by their `config.yaml` names. Pydantic keeps that exception in the error's context. The core's message is unchanged. | Evidence: `pierpressure/core/config.py` (`_resolve_horizon`); pydantic `ctx["error"]` |
| D4 | How does the reworded error reach the log? | `validate_piers` takes an optional function that writes a skipped pier's error, and logs `SKIP_PIER_MESSAGE` with its result. `build_config` takes the function as a keyword argument and passes it on; `load_app_config` passes the add-on's function. The default writes the error as today. `ConfigFile` does not change. The core learns no form name. | Evidence: plan review round 2 |
| D5 | What does the add-on's function change? | It writes the form's message in place of the core's error when the pier's horizon came from the form and the error is the horizon-source error. The core checks the horizon only once every field is valid, so that error never comes with another. Every other error stays as the core wrote it. The function checks nothing, so ADR-0022 holds. | Evidence: pydantic runs `PierConfig`'s after-validator only when its fields pass; plan review round 1 |
| D6 | When did a pier's horizon come from the form? | When any form pier with that text id sets both `min_altitude` and `horizon_points`. The combine stops the add-on when the form and `config.yaml` both set a horizon for one id, so the file cannot be the source then. A pier without a text id fails on `id` before the horizon check runs. A pier whose horizon came from `config.yaml` keeps the file's wording. | Evidence: `pierpressure/addon_settings.py:128`, `pierpressure/core/config.py:268` |
| D7 | What does the reworded message say? | The log line reads `Skipping invalid pier 'backyard': Horizon: floor and Horizon: points are both filled in on the Configuration tab. Fill in one of them at most.` It leaves out pydantic's header and its excerpt of the input, which can show `min_altitude`. | Evidence: plan review round 1 |
| D8 | Where do the labels live in code? | In `pierpressure/addon_options.py`, beside `HORIZON_FIELDS`, keyed by the horizon block's `config.yaml` keys. A test checks they match `ha-addon/translations/en.yaml`, so they cannot drift. | Assumption |
| D9 | Does the error for a `config.yaml` pier change? | No. A Docker pier, or a form pier whose horizon came from `config.yaml`, keeps today's message. | Evidence: #288 Scope |
| D10 | Which spec changes? | `ha-addon`: the requirement "A form pier's horizon that breaks the horizon rules skips the pier" says the both-fields error names the two labels, and that a field error comes first. A new requirement says a horizon from `config.yaml` keeps the file's names, and another covers `DOCS.md`. `horizon-mask` is unchanged. | Evidence: `openspec/specs/ha-addon/spec.md`; plan review round 2 |
| D11 | What changes in `DOCS.md`? | "Set a pier's horizon" says the error for both fields names **Horizon: floor** and **Horizon: points**. The line that maps `horizon.points` stays, for points that cannot be read. | Evidence: `ha-addon/DOCS.md` |
| D12 | How is it accepted? | Tests check each of these. The core's error type carries its sources. `validate_piers` logs what the function writes. A form pier with both fields logs the two labels and neither key. A horizon from `config.yaml` with both keys logs the core's wording. Any other error is unchanged. The labels match the translation file. `DOCS.md` names both labels. | Assumption |
| D13 | Where does the `discovery.md` revision go? | On this branch, as its own `docs:` commit before the archive commit. At that commit, the author checks stage 4 against the code again, once the fix is in. | User |

## Changes from the story

- The general case, every form-pier error in labels, stays out (D2). It is
  bigger than this fix. Not filed: Andrew can ask for it as its own story.
- Added the `discovery.md` revision for epic #99 to this branch (D13).

Confirmed by user: yes
