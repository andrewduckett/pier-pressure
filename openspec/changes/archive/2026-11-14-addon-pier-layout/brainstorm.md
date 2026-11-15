## Story

#100 addon-pier-layout — a pier's settings are laid out the way you chose after
trying both. <https://github.com/andrewduckett/pier-pressure/issues/100>

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | Build a flat and a grouped pier layout, try both in real Home Assistant, and ship only the chosen one. The interval, Piers and broker text and the `DOCS.md` walkthrough stay with #101; the horizon-type dropdown stays with #102. | Evidence: #100 packet |
| D2 | When is the trial? | During planning, before the proposal, so the spec, design and tasks describe only the layout that ships. | Assumption |
| D3 | How are the two layouts loaded? | As two throwaway local add-ons, `pierpressure_flat_trial` and `pierpressure_grouped_trial`, in `.workspace/addon-trial/`. They run the released image and differ only in `config.yaml` and `translations/en.yaml`. Neither is committed. | Evidence: frontend `supervisor-app-config.ts` draws the form from the schema and translations alone |
| D4 | What does the flat layout change? | Only the help text. Field names and order stay, because today's order already runs Location, Horizon, Equipment, Gates. Saved settings keep working. | Evidence: `ha-addon/config.yaml` |
| D5 | Where does the pier ID sit in the grouped trial? | At the pier's top level, before the four groups, not inside Location. It names the pier, matches `piers[].id` in `config.yaml`, and leads the pier's row label. | Assumption |
| D6 | What are the fields called inside the grouped trial's groups? | The `config.yaml` names: `horizon.min_altitude`, `horizon.points`, `equipment.focal_length_mm` and so on. `location` and `gates` are form-only groups, and their fields keep the file's pier-level names. | Assumption |
| D7 | What label does the grouped trial's gates group show? | "Verdict rules", with the key `gates`, because "gates" is the project's own word, not the user's. | Assumption |
| D8 | Does the help text differ between the two layouts? | No. Each field has the same text in both, so the trial compares layout, not wording. Only the grouped layout has group introductions. | Assumption |
| D9 | What must every label do? | Every field and group has a name and a description, and each number's description names its unit or says it has none. | Evidence: `openspec/specs/ha-addon/spec.md` |
| D10 | What is the grouped layout's known risk? | The Supervisor requires every nested group to be present on save, because a group cannot be marked optional. The trial checks whether a new pier saves with a group left unopened. | Evidence: Supervisor `supervisor/apps/options.py` (`_check_missing_options`) |
| D11 | Do old saved settings keep working? | Not required. Andrew re-enters what no longer fits. | Evidence: epic #99 shared decisions |
| D12 | Does this story touch `DOCS.md`? | Only where the chosen layout makes it wrong. The section-by-section walkthrough is #101. | Assumption |
| D13 | Can the flat layout show dividers or section headings? | No. A pier's dialog is a plain list of fields, and the add-on schema has no heading type. Real sections exist only at the top level of the tab, and piers is a list. | Evidence: frontend `ha-selector-object.ts`, `supervisor-app-config.ts` |
| D14 | Which layout ships, and why? | The labelled flat layout: today's fields, each label prefixed with its section. The grouped layout's first view, a row per group that opens another dialog, read worse, and the plain flat list gave no sense of sections. | User |
| D15 | How does a label name its section? | `<Section>: <field>`, with four sections: Location (latitude, longitude, elevation), Horizon (floor, points), Equipment (focal length, sensor width, sensor height, reducer or barlow) and Verdict (GO threshold, wind-gust limit). The Pier ID stays unprefixed, first. | User |
| D16 | Where does a section's introduction go? | At the start of the help text of the section's first field, in one sentence. | User |
| D17 | Does the schema change? | No. Field names, order, types and save checks stay, so the service and saved settings are unchanged. Only `translations/en.yaml` changes. | Evidence: `ha-addon/config.yaml` |
| D18 | What happens to the "a form cannot nest" reason in the `ha-addon` spec and ADR 0020? | The spec drops it, because nesting has worked since Supervisor PR #6171. Flat names are now a choice made after this trial. A new decision record says so; ADR 0020 stays as written. | Assumption |
| D19 | How is the shipped layout accepted? | Its labels pass the add-on tests, including the section prefix and one section introduction per section. The schema, the service and the existing form-to-verdict scenarios stay unchanged. | Assumption |

## Changes from the story

- The grouped trial kept the pier ID outside the Location group (D5), where the
  packet put it inside. The grouped layout does not ship, so this changes nothing
  that ships.
- Added a third trial, the labelled flat layout (D15, D16), after Andrew asked
  for sections in the flat layout. It ships instead of the plain flat layout.
- Not filed: one pier on the form as real top-level sections, with more piers
  in `config.yaml`. Andrew did not take it up.

Confirmed by user: yes
