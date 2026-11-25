<!-- Plain language: Lead with the problem and resulting behavior. Give a reader enough context to decide whether the scope solves that problem. Keep the required headings. -->

## Why

On a phone in portrait, the night strip's label column takes about 140 px of a card about 340 px wide, so each hour's cell is too narrow to read or tap easily. The column is as wide as its widest entry: the Temperature chart's key beside its °C scale. These widths are estimates from the card's styles, not measurements.

## What Changes

- Each of the fourteen rows, the Moon up lane, and the Temperature and Dew point entries of the Temperature chart's key get a 16 px icon. The icon carries its row's name as `title` and `aria-label`.
- The card picks one of two layouts from its own width, through a CSS container query at 450 px:
  - **450 px or wider:** each icon sits beside the text label the row has today. A target lane reads `Target <n>`, with no icon (D8). There is no legend.
  - **Narrower than 450 px:** the text labels are hidden and only the icons show. A target lane's label is its rank number alone. A legend under the strip pairs each icon with its row's name.
- The legend lists only the rows, lanes and key entries the strip draws, in the strip's top-to-bottom order (D3). Its last entry pairs a rank number with `Target rank`, shown only when the strip has a target lane (D2).
- The Temperature chart's °C labels move from the label column into the plot, at the chart's left edge, on every card (D1). They still stay put while the strip pans.
- A Temperature chart line's message (`Not found`, `Unavailable`, `No forecast`) stays beside its key entry, so the label column widens only while a sensor has a problem (D4).
- A tap on an icon opens a box with its row's name. On a card narrower than 450 px, a tap on a rank number opens `Target <n>`. A tap on a label's text still closes the box (D5).
- `docs/night-card.md` describes the icons, both layouts, the legend and where the °C scale is drawn.
- No change to the core, the verdict document, the delivery, or the rows' names, order or shades. No card option forces a layout.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-card`: the strip's labels gain icons and a narrow layout with a legend; the Temperature chart's °C labels move into the plot; icons and rank numbers become tap items; the docs describe all of this. The changed requirements include `The Temperature chart labels each 5 °C step`, `Everything on the strip pans together`, `A tap elsewhere or on the same item closes the box`, `An item is the same after a redraw when it has the same place in the strip`, `The docs describe the Temperature chart` and `The docs say a tap shows what hovering shows`.

## Impact

- **Card code:** `card/src/strip.ts` (rows, lanes and chart lines), `card/src/pierpressure-card.ts` (strip markup and styles, a new legend), `card/src/chart.ts` (key entries, °C labels), `card/src/tap.ts` (tap keys and texts for icons and rank numbers), and a new module for the icon set.
- **Card tests:** `card/test/rows.test.ts`, `card/test/targets.test.ts`, `card/test/chart.test.ts` and `card/test/tap.test.ts` read labels, the scale and tap boxes, and change with them.
- **Docs and spec:** `docs/night-card.md` and `openspec/specs/night-card/spec.md`.
- **Acceptance:** happy-dom lays nothing out, so the automated tests check the markup and the container query rule. Both layouts are also checked by hand in a browser, below and above 450 px, and the result is recorded in the pull request (D7).
- No new dependency. No change to the Python core, MQTT delivery or the Home Assistant add-on.
