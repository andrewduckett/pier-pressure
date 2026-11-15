# Plan review: addon-horizon-error-labels

- **Round:** 2
- **Reviewed commit:** 38ca44c
- **Reviewer:** gemini/gemini-3.8-flash
- **Reviewer context:** fresh context, other family
- **Verdict:** APPROVE_WITH_CHANGES
- **Round 1** (commit 823a8c5, same reviewer): REVISE. Two Critical findings were
  confirmed. Pydantic runs the horizon check only once every field is valid, so
  a field error and the horizon error never come together. The error's excerpt
  of the input could show `min_altitude`. The plan now writes the whole message
  for that one error (D5, D7), and the spec's scenario says a field error comes
  first.

The route `lets-minimal` has no review artifact. This review ran on the
finished plan before apply.

## Findings

| # | Label | Finding | Check | Outcome |
|---|---|---|---|---|
| 1 | Critical | Finding the form pier by text id fails for a repeated id or a pier without a text id. | REFUTED | Rebutted, below |
| 2 | Critical | The spec delta adds requirements beside the existing horizon requirement instead of modifying it. | CONFIRMED | Fixed |
| 3 | Moderate | `ConfigFile` carries the error-writing function, which mixes wording into a data object. | CONFIRMED | Fixed |
| 4 | Moderate | Task 1.7 covers two scenarios. | CONFIRMED | Fixed |
| 5 | Moderate | One error in labels leaves the other form-pier errors in `config.yaml` names. | CONFIRMED, by design | Rebutted, below |
| 6 | Suggestion | The Why line and D13 use the passive voice. | CONFIRMED | Fixed |

## Required changes applied

- Finding 2: the delta now modifies "A form pier's horizon that breaks the
  horizon rules skips the pier". The both-fields case names the labels, and a
  new scenario says a field error comes first. Two requirements stay ADDED:
  a horizon from `config.yaml` keeps the file's names, and the `DOCS.md`
  sentence. D10 says so.
- Finding 3: `build_config` takes the function as a keyword argument, and
  `load_app_config` passes the add-on's. `ConfigFile` does not change (D4, task
  1.3).
- Finding 4: task 1.7 is split into 1.7 (both fields name the labels) and 1.8 (a
  field error comes first).
- Finding 6: the Why line, D13 and task 1.11 name who acts.

## Rebuttals

- **Finding 1 (Critical).** D6 asks whether *any* form pier with that text id
  sets both horizon fields, so a repeated id is matched by set membership, not
  by the first pier. If the form sets a horizon for an id, `config.yaml` cannot
  also set one: the combine stops the add-on (`pierpressure/addon_settings.py:128`).
  A pier without a text id fails on `id: str` (`pierpressure/core/config.py:268`),
  so the horizon check never runs for it, and no horizon error can need
  rewording. D6 now states both facts.
- **Finding 5 (Moderate).** #288 asks for this error in the form's labels, and
  D2 keeps the other errors out because rewording all of them changes the
  documented log format for every form-pier error. The other errors stay mapped
  by the label tables in `ha-addon/DOCS.md`. A follow-up story can cover them.
