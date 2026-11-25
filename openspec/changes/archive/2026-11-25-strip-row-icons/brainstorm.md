<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#332 strip-row-icons — a narrow card labels the night strip's rows with icons and a legend, leaving more width for the hours. https://github.com/andrewduckett/pier-pressure/issues/332

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Where does the Temperature chart's °C scale go on a card 450 px or wider? | Into the plot on every card: the °C labels are drawn inside the chart's left edge, over the lines, in both layouts. | Assumption |
| D2 | Does the legend explain a target lane's rank number in icon-only mode? | Yes: a last entry pairs a rank number with `Target rank`, shown only when the strip has at least one target lane. | Assumption |
| D3 | Does the legend list every icon, or only what the strip draws? | Only the rows, lanes and key entries the strip draws now, in the strip's top-to-bottom order. | Assumption |
| D4 | In icon-only mode, where does a Temperature chart line's message (`Not found`, `Unavailable`, `No forecast`) go? | Beside the line's icon in the key, as today; the label column widens only while a sensor has a problem. | Assumption |
| D5 | What in the label column can a tap open? | Every icon, in both layouts, opens a box with its row's name; in icon-only mode each rank number opens `Target <n>`; a tap on a label's text still closes the box. | Assumption |
| D6 | Do "icon-only mode" and "legend" become glossary terms? | No: the spec says "a card narrower than 450 px" and "the strip's legend"; "key" stays the Temperature chart's key only. | Assumption |
| D7 | How is the layout switch accepted, given happy-dom lays nothing out? | Tests check the markup, each icon's `title` and `aria-label`, the legend and the container query rule; the build also checks both layouts by hand in a browser, below and above 450 px, and records it in the pull request. | Assumption |
| D8 | What labels a target lane on a card 450 px or wider? | `Target <n>` as text, with no icon, as today. | Evidence: #332 scope item 4 |

## Changes from the story

- **Cut:** the option to keep the °C scale in the label column on a wide card (scope item 4, "may stay"). D1 moves it into the plot on every card, so the chart has one layout.
- **Added:** a `Target rank` legend entry (D2), so a bare rank number is explained.
- **Added:** rank numbers as tap items in icon-only mode (D5). The tap-box requirement changes: a tap on an icon or rank number opens a box; a tap on a label's text still closes it.
- **Added:** a manual browser check of both layouts, recorded in the pull request (D7), because the automated tests cannot see which layout shows.

Confirmed by user: yes
