**Why:** Two dashboards, the YAML night dashboard and the PierPressure card, keep getting mixed up when features are designed, and the card has replaced the YAML in every recent story, so the YAML goes now and only the card is left.

## Story

#227 remove-yaml-night-dashboard — the PierPressure card is the only Home Assistant dashboard PierPressure documents
<https://github.com/andrewduckett/pier-pressure/issues/227>

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What is removed? | The YAML night dashboard: `docs/night-dashboard.md`, `docs/images/night-dashboard.png`, the `night-dashboard` spec and `tests/test_night_dashboard_doc.py` | User |
| D2 | What is left at the old page's path? | Nothing: no stub and no migration note, because the maintainer is the only user | User |
| D3 | What happens to `mise run dashboard-check`? | It stays, card only: no plotly-graph-card download, no YAML dashboard, and its tests follow | User |
| D4 | Does the night-card spec gain a requirement for the real Home Assistant check? | No: `dashboard-check` stays unspecified dev tooling | User |
| D5 | What replaces the README's two dashboard paragraphs? | One paragraph that points to `docs/night-card.md` and says the card shows the verdict, the moon, the night strip and the target lanes | User |
| D6 | How is the decision recorded? | A new ADR-0035 supersedes ADR-0034's sentence that the YAML dashboard stays; ADR-0026's status and banner become fully superseded | Evidence: #227, `docs/decisions/0026-*.md`, `docs/decisions/0034-*.md` |
| D7 | Which other references go? | The YAML mentions in `docs/night-card.md` (opening and the shades note), `docs/night-timeline.md` (Related), `card/src/strip.ts` (span comment), `mise.toml` (`dashboard-check` description) and `compose.yaml` (dashboard profile comment) | Evidence: `grep -rn night-dashboard` |
| D8 | Do archived changes and the core change? | No: archived changes under `openspec/changes/archive/` are history and keep their links; the core, the published entities and the glossary are untouched | Assumption |

## Changes from the story

None. #173 (scrollable-night-strip) was closed as superseded while #227 was shaped.

Confirmed by user: yes
