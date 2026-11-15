**Why:** Home Assistant's Supervisor reads every `config.*` file in this repository as an add-on config, so each store reload logs a warning for two files that are not add-ons, and every user who adds the repository sees them; one of the two is ours to rename, and the other needs a documented explanation.

## Story

#35 addon-store-scan-warnings — the add-on store logs no warning for files this
project controls.
https://github.com/andrewduckett/pier-pressure/issues/35

The issue has no comments.

## Decisions

The user delegated this brainstorm. The brief said to settle the warning from the
Supervisor's source code instead of a real Home Assistant OS, take the
recommended answer to each question, record the alternatives, and go on without
asking. So each row that code or a document did not settle is an `Assumption`,
and the rejected alternatives follow the answer. Supervisor sources are at
home-assistant/supervisor@98a2322 (2026-11-12).

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | How is the warning confirmed without a real Home Assistant OS? | From the Supervisor's store code, which this ledger cites line by line, and a copy of its file filter run on a clean export of the tree (`git archive HEAD`). | User (the brief) |
| D2 | Does the Supervisor log a warning for a non-add-on `config.yaml`? | Yes. It globs `**/config.*`, skips only paths with a part that starts with `.` or is named `rootfs`, and keeps the suffixes `.yaml`, `.yml` and `.json`. A file with no `name` field fails with `Invalid app config!`, and the store logs `Can't read <path>: Invalid app config!. Got {…}` at WARNING level for every user, where `{…}` is the start of the file's contents (reproduced with voluptuous's `humanize_error`). Only the schema's own advisories go quiet for add-ons that are not installed. It runs at startup, every 3 hours and on a manual refresh. | Evidence: `supervisor/store/data.py:158-164,233-238`, `supervisor/apps/validate.py:314-319,572-580`, `supervisor/const.py:52`, `supervisor/misc/tasks.py:38,79` |
| D3 | Which tracked files match? | Three: `ha-addon/config.yaml` (the add-on), `openspec/config.yaml` and `docs/examples/config.explainer.yaml`. The issue missed the third: the glob `config.*` matches any name that starts with `config.`. | Evidence: the filter from D2 run on `git archive HEAD` |
| D4 | Can `openspec/config.yaml` move or take another name? | No. OpenSpec 1.16.1 reads only `openspec/config.yaml`, or `openspec/config.yml` when that is missing. It has no flag or environment variable for another path, and both names match the glob. lets-spec owns the file too. | Evidence: `@fission-ai/openspec` 1.16.1 `dist/core/project-config.js` (`resolveConfigFilePath`), `dist/core/openspec-root.js` (`OPENSPEC_CONFIG_YAML`, `OPENSPEC_CONFIG_YML`) |
| D5 | What happens to the `openspec/config.yaml` warning? | It stays, and the docs explain it: one warning line per store reload that is safe to ignore. Rejected: move the add-on to its own repository (ADR-0014's rejected Alternative 1, and every user would have to add a new URL); serve the add-on from a branch with a `<url>#<branch>` repository URL, which the Supervisor accepts (it still changes the URL ADR-0014 keeps stable, and a release would also have to update that branch); make `openspec/config.yaml` valid as an add-on (the store would list a fake add-on); ask OpenSpec upstream for another config path (outside this repository, and lets-spec would need it too). | Assumption |
| D6 | What is the explainer example's new name? | `docs/examples/explainer-config.yaml`, which does not start with `config.`. Its one reader, `tests/test_explainer_docs.py`, follows it. No document links to the file by name. Rejected: `.yml` or `.json` suffixes (they still match); a hidden folder (it hides an example from readers). | Evidence: search of the tree for `config.explainer.yaml`; Assumption (the name) |
| D7 | How does a test stop a new matching file? | A test in `tests/test_ha_addon.py` lists the tracked files with `git ls-files`, applies the D2 rule, and expects exactly `ha-addon/config.yaml` and `openspec/config.yaml`. It reads tracked files because the Supervisor clones the repository: untracked folders such as `card/node_modules` never reach it. Its docstring cites the Supervisor lines from D2. Rejected: walk the working tree (it would also see untracked and ignored files). | Evidence: `supervisor/store/git.py` (clones the repository); Assumption (the test's place) |
| D8 | Where do the docs explain the warning? | A new section in `ha-addon/DOCS.md`, next to the other "If …" sections, that quotes the line, says why it appears, and says it is harmless. The README's install step 1, where the user adds the repository, gets one sentence that links to it. Rejected: the README only (DOCS.md is the add-on's own Documentation tab, where add-on users look). | Assumption |
| D9 | Which spec changes? | `ha-addon` gains one requirement: the only files the Supervisor reads as add-on configs are `ha-addon/config.yaml` and `openspec/config.yaml`, and the add-on docs name the one remaining warning. "The repository is an add-on repository" stays as it is. | Evidence: `openspec/specs/ha-addon/spec.md` |
| D10 | Is a follow-up issue filed for the OpenSpec warning? | No. Each fix left needs a decision this change does not make: a new add-on URL that would replace ADR-0014, or a change to OpenSpec upstream. The final report names both. | Assumption |

## Changes from the story

- The issue's first step, confirming the warning on a real Home Assistant OS, is
  replaced by the evidence in D1 and D2, as the brief asked.
- Added: `docs/examples/config.explainer.yaml`, a second file that matches the
  Supervisor's scan (D3). The packet, shaped in this run, already lists it.
- The `openspec/config.yaml` warning is documented, not removed (D4, D5).

The brief's instruction to proceed on recommendations stands in for the user's
confirmation of this ledger.

Confirmed by user: yes
