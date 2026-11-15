**Why:** The pier fields now explain themselves in sections, but the recompute interval, the Piers introduction and the broker section still use the older, thinner text, and `DOCS.md` does not walk through the form as it now looks.

## Story

#101 addon-form-text — every part of the Configuration tab explains itself.
<https://github.com/andrewduckett/pier-pressure/issues/101>

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is in scope? | The description of `interval_seconds`, `piers` and `mqtt`, the descriptions of the four broker fields, and the setup walkthrough in `ha-addon/DOCS.md`. The pier field text from `addon-pier-layout` stays as shipped. | Evidence: #101 packet |
| D2 | Do any names change? | No. "Recompute interval", "Piers", "MQTT broker", "Host", "Port", "Username" and "Password" stay. `DOCS.md` and the log already use them, and the broker block is a real section of the tab, so its fields need no section prefix. | Assumption |
| D3 | What is "the same voice as the pier settings"? | Each description says what the setting is, why it matters, its unit or that it has none, its default, and what an empty field means. An optional field says `Optional.`; a required one does not. | Evidence: `ha-addon/translations/en.yaml` pier fields |
| D4 | What does the interval's description add? | It names its unit, its default of 900 (15 minutes), and that each pier's Refresh button recomputes at once, between intervals. | Evidence: `openspec/specs/ha-delivery/spec.md`, "Refresh works independently of the interval" |
| D5 | What does the Piers introduction say? | What a pier is, that each pier gets its own device, and that a pier's dialog lists the Pier ID, then the Location, Horizon, Equipment and Verdict fields, each label starting with its section. Location is required; the other three are optional. It keeps the `config.yaml` pointer for settings the form lacks. | Evidence: archived `addon-pier-layout` D14, D15 |
| D6 | What do the broker section and fields say? | The section says when to fill it in: leave it empty to use the Mosquitto add-on, or the broker in `config.yaml`. Host says that setting it takes all four from the form. Port, Username and Password say they need a host. Every broker field, Host included, says `Optional.` | Evidence: `openspec/specs/ha-addon/spec.md`, "A broker host on the form sets all four connection settings" |
| D7 | How does `DOCS.md` walk through the form? | "Set up the add-on" gets one step per part of the tab, in the tab's order: Recompute interval, Piers, then MQTT broker. The Piers step walks the pier dialog in its order: Pier ID, Location, Horizon, Equipment, Verdict. Each step names the part by its label in bold, and links to the detailed section where one exists. | Assumption |
| D8 | Do the detailed sections of `DOCS.md` change? | Only where they are out of step with the form. "More settings" lists what the tab shows by its parts, in the tab's order. The horizon, equipment, verdict and broker sections already use the shipped labels. | Evidence: `ha-addon/DOCS.md`, `tests/test_ha_addon.py` (`test_docs_label_is_never_an_old_pier_label`) |
| D9 | How is it accepted? | Tests check: every optional field says `Optional.` and no required one does; the interval names 900 and the Refresh button; the Piers introduction names the four sections in order; the broker section names the Mosquitto add-on and `config.yaml`; and the `DOCS.md` setup walkthrough names the tab's parts and the pier sections in the tab's order. The schema and the service stay unchanged. | Assumption |
| D10 | Does the form's structure or any check change? | No. `ha-addon/config.yaml`, the service and every verdict stay as they are. | Evidence: #101 packet, Scope out |

## Changes from the story

- Added a rule that every optional field's description says `Optional.` (D3).
  Host is the one optional field whose text does not say so today.

Confirmed by user: yes
