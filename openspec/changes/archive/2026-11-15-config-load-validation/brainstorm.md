## Story

#81 config-load-validation — a padded horizon azimuth reads as written, and a
repeated pier id is refused.
https://github.com/andrewduckett/pier-pressure/issues/81

The change also closes #86, duplicate-pier-ids — two piers can no longer share an id.
https://github.com/andrewduckett/pier-pressure/issues/86

Neither issue has comments.

## Decisions

The user delegated this brainstorm: the brief said to take the recommended
answer to each question, record the alternatives, and go on without asking. So
each row the brief did not settle is an `Assumption`, and the rejected
alternatives follow the answer.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | One change for #81 and #86, or two? | One change. Both are errors the core makes while it loads the piers, in `pierpressure/core/config.py`, and each fix is small. | User (brief) |
| D2 | What does a zero-padded integer such as `045` mean? | The decimal number 45, with or without a sign: `-045` is -45. Rejected: refuse it as not a plain number (stricter, but the intent is clear and padded tables are common). | Assumption |
| D3 | What does a base-60 value such as `1:30` or `1:30.5` mean? | It is text, not a number. A horizon point that holds one is rejected, and the pier is skipped with an error that names the pier and `horizon.points`. Rejected: read `1:30` as 1.5 degrees (a guess at degrees and minutes that YAML never meant). | Assumption |
| D4 | Where does the number rule apply? | To every value in `config.yaml`, in every install type, and to the form's **Horizon points** text. The file is read in one pass, so a rule for horizon points alone cannot be told apart from the rest of the file. Rejected: horizon points only (the file and the form would then differ). | Evidence: `pierpressure/core/config.py` (`read_config_mapping`, `HorizonConfig._parse_points_text`) |
| D5 | Do other YAML 1.1 forms change too? | No. Only the two surprises in #81 change: leading-zero octal and base-60 numbers. `0x1A`, `0b11`, `1_000`, and `yes` and `no` as true and false stay as they are. Rejected: adopt the whole YAML 1.2 core schema (wider change, more to test, not asked for). | Assumption |
| D6 | Does a text setting that looks like a padded number, such as `id: 08`, change? | No. Only values that YAML 1.1 reads as octal change, and they become decimal numbers. `id: 08` stays text, as today, and `id: 045` stays invalid, as today, because it was already a number. | Evidence: `yaml.safe_load` reads `08` as text and `045` as 37 |
| D7 | Is a repeated pier id one pier's error, or the whole configuration's? | The whole configuration's: startup fails with an error that names the id. Neither pier is wrong alone, so skipping one cannot be right. The add-on's repeated-id rule for its `config.yaml` and the repeated-provider rule already stop startup. Rejected: skip every pier that shares the id; keep the first and skip the rest. | Evidence: `openspec/specs/ha-addon/spec.md` (A pier id repeated in config.yaml stops the add-on), `openspec/specs/conditions/spec.md` |
| D8 | Which entries count when looking for a repeat? | Every entry in the piers list whose `id` is text, compared exactly, before any pier is checked. An entry that will be skipped for another reason still counts. Rejected: count only the piers that pass their checks (fixing one pier could then reveal a clash later). | Assumption |
| D9 | Do ids that differ only in letter case clash? | No, they stay distinct. Topics and entity ids use the id as written. | Evidence: `pierpressure/delivery/mqtt.py` (topic builders) |
| D10 | Where does the add-on get the rule? | From the core: a form that lists an id twice reaches the core, which rejects it. The add-on's own check for an id repeated in its `config.yaml` stays, and runs first. | Evidence: `pierpressure/addon_settings.py` (`_file_piers`), `pierpressure/addon_options.py` (`translate_form` keeps every pier) |
| D11 | What may the repeated-id error show? | The repeated id, kept on one line, and no other configuration value. | Evidence: `openspec/specs/ha-addon/spec.md` (An id or key name in a combine error stays on one line) |
| D12 | Do the user docs change? | Yes. The README's configuration table says that a pier id must be unique, and that a zero-padded number is read as a decimal number. | Assumption |

## Changes from the story

- The packet left open whether `045` is read as 45 or refused. D2 picks 45.
- The packet's scope already holds ids that differ only in letter case out of
  scope. D9 records why.
- D6 records that a text setting such as `id: 08` keeps working.

The brief's instruction to proceed on recommendations stands in for the user's
confirmation of this ledger.

Confirmed by user: yes
