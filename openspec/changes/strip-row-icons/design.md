<!-- Plain language: Help the next implementer find the approach, understand the choices and act on the plan. Explain necessary technical terms. Put each risk beside its mitigation and each open question beside the decision it affects. -->

## Context

The night strip is one CSS grid, `.strip`, with `grid-template-columns: max-content 1fr` (`card/src/pierpressure-card.ts`). Each row is `display: contents`, so its `.label` sits in column 1 and its `.track` in column 2. Column 1 is as wide as its widest entry. Today that is the Temperature chart's `.chart-label` (`card/src/chart.ts`): a two-column grid that holds the key and a `.scale` column at least 40 px wide, where each `.step` label is placed absolutely at its gridline's height.

Other facts that shape the approach:

- `strip.rows` already leaves out the Cloud range row when the card does not draw it. `strip.targets` holds only the lanes the strip draws. Each has a `label`.
- A tap is resolved by `target.closest("[data-tip]")` in the card's `tap` handler. The box stays open only while `tipText()` in `card/src/tap.ts` still returns text for the open key, and it is placed over `querySelector('[data-tip="<key>"]')`.
- The card's tests run in happy-dom, which does no layout. Style rules are checked as text through `cardStyles()` in `card/test/harness.ts`, as `card/test/range.test.ts` and `card/test/messages.test.ts` already do.
- `mise run dashboard-check` starts a throwaway Home Assistant with the built card, for checking it by eye.
- The draft icons are in issue #332 and in `.workspace/icon-mockup.html`: 24 × 24 view box, stroked in `currentColor`.

## Goals / Non-Goals

**Goals:**

- One markup for both layouts, so the render code has no width state and the tests can assert everything but the layout switch.
- The label column narrows to about 32 px on a card narrower than 450 px.
- Every new tap item follows the existing tap rules: a `data-tip` key, a text in `tipTexts`, and a box that closes when its item goes.

**Non-Goals:**

- No change to `buildStrip`'s rows, lanes, order or hover texts, other than what the label markup reads.
- No JavaScript measurement of the card's width.
- No change to `getCardSize()` (see Decisions).

## Test Seams

- **Primary test seam:** the mounted card, through `mountCard()` in `card/test/harness.ts`: query its shadow DOM for labels, icons, the legend and the °C labels, and drive taps with `tap()`. Style rules, including the container query, are read as text with `cardStyles()`.
- **Existing seams reused:** `card/test/rows.test.ts`, `card/test/targets.test.ts`, `card/test/chart.test.ts`, `card/test/tap.test.ts` and `card/test/range.test.ts`. A new `card/test/icons.test.ts` holds the icon and legend tests.
- **Outside the automated seam:** which layout shows at a given width, and how the °C labels read over the lines. The build checks both in a browser through `mise run dashboard-check`, at 340 px and at 600 px, and records the result in the pull request (D7).

## Scrutiny Tier & Blast Radius

- **Tier:** medium
- **Blast radius:** the dashboard card only: `card/src/` and `card/test/`, plus `docs/night-card.md` and the night-card spec. No change to the Python core, the verdict document, MQTT delivery or the add-on.

## Decisions

### 1. A CSS container query on `ha-card` picks the layout

`ha-card` gets `container: pierpressure / inline-size`. Rules under `@container pierpressure (width < 450px)` hide each label's name, show its rank number and show the legend. `ha-card` has no padding of its own, so the query measures the card's full width, which is the width the spec names.

- **Alternative: a `ResizeObserver` that sets an attribute.** It would let happy-dom tests see the layout, but it adds width state, a redraw on every resize and a first frame in the wrong layout. The issue chose a container query.
- **Alternative: a viewport media query.** Rejected by the issue: a card can be narrow on a wide screen.
- **Alternative: the container on `.card-content`.** Its 16 px padding would shift the cut-off to a 482 px card.

### 2. Both layouts are in the markup; CSS shows one

Each label always holds its icon and its name; a target lane's label holds its rank number and its name. The legend is always rendered after `.strip`, inside `.card-content`. Outside the container query, `.rank` and `.legend` are `display: none`. Inside it, `.label .name` and `.chart-label .name` are `display: none`, and `.rank` and `.legend` show.

- **Why:** the render stays a pure function of the strip, and the tests can assert every element and attribute.
- **Alternative: render one layout from a width property.** Needs Decision 1's rejected `ResizeObserver`.

### 3. The icon markup carries the name once for a screen reader

A row's label is:

```html
<span class="label">
  <span class="icon" role="img" title="Seeing" aria-label="Seeing" data-tip="label:seeing"><svg aria-hidden="true">…</svg></span>
  <span class="name" aria-hidden="true">Seeing</span>
</span>
```

The icon names the row in both layouts, so the visible name is `aria-hidden`. A target lane's label is `<span class="rank" title="Target 1" aria-label="Target 1" data-tip="label:target_1">1</span><span class="name">Target 1</span>`. Here the name is not `aria-hidden`: on a wide card the rank is `display: none`, so the name is all a screen reader has; on a narrow card the name is `display: none` and the rank's `aria-label` speaks. `display: none` removes an element from the accessibility tree, so each layout reads the name once.

The `title` and `aria-label` are attributes on the wrapper, not an SVG `<title>`: a `<title>` element adds to `textContent`, and the existing tests read a label's text.

### 4. The icons live in a new `card/src/icons.ts`

It exports a map from icon key to an SVG template (Lit `svg`), keyed by the row keys in `ROWS`, `cloud_range`, `moon_up`, `temperature` and `dew_point`, and a `renderIcon(key, name, tip?)` helper. Each icon is inline paths in a 24 × 24 view box, drawn at 16 px with `fill: none; stroke: currentColor; stroke-width: 2`. The shared small-cloud path in the draft is inlined into each of Cloud low, Cloud mid and Cloud high.

- **Alternative: `<symbol>` definitions and `<use href="#…">`.** Works only while the symbols sit in the same shadow root, adds a hidden SVG to every render, and saves little: the full set is a few kilobytes.
- Polishing the drafts, and keeping Cloud low, mid and high distinct at 16 px, is build work (issue #332, notes).

### 5. The legend is a list built from the strip

`renderLegend(strip)` returns `<ul class="legend">` with one `<li>` per drawn row (`strip.rows`), then `Moon up`, then each `strip.chart.lines` entry, then a `Target rank` entry when `strip.targets` is not empty (D2, D3). An entry is `<li>`, its icon, then `<span class="name">` with its name. The `Target rank` entry has no icon: it is `<li><span class="rank" aria-hidden="true"><n></span><span class="name">Target rank</span></li>`, where `<n>` is the rank of the strip's first target lane. Each entry's icon is `aria-hidden`, with no `title` and no `data-tip`, so a tap on the legend closes the box. The legend sits outside `.strip`, so dragging it pans nothing. On a narrow card it is a grid of `repeat(auto-fill, minmax(130px, 1fr))` columns in the secondary text colour.

### 6. The °C labels move into the chart's track

`.scale` moves from `.chart-label` into the chart's `.track`, after the hour areas, as an overlay at `left: 0` with `pointer-events: none` and `color: var(--secondary-text-color)`, the colour the labels had from `.label`. Each `.step` keeps its `data-celsius`, its `top` and its end-label shift, and changes `right: 0` to `left: 2px`. Its text gets a backing in the card's colour, `background-color: var(--card-background-color)`, with a small padding and radius, so a line does not run through the text. `.chart-label` stops being a two-column grid and holds only the key (D1).

- **Why `pointer-events: none`:** the hour areas fill the chart's full height. With the labels transparent to the pointer, a hover or a tap where a label sits reaches the hour under it, and `title` still shows the hour's text.
- **Panning:** the track never moves; only its contents are redrawn per axis. A label at `left` of the track stays put by construction.
- **Alternative: an SVG `<text>` in `.plot` with a `paint-order: stroke` halo.** It reads well, but `.plot` uses percent coordinates and has `overflow: hidden`, and the existing tests find the labels by `.scale [data-celsius]`.

### 7. Each key entry gets an icon; its message stays in the key

`renderKeyEntry` draws the swatch, the icon (`data-tip="label:chart:<key>"`), the name (`.name`, `aria-hidden`) and the existing message. The message keeps its markup and stays visible in both layouts, so on a narrow card the label column widens only while a sensor has a problem (D4).

### 8. Tap keys and texts for icons and rank numbers

`tipKey.label(place)` returns `label:<place>`, where `<place>` is a row key, `moon_up`, `chart:<line key>` or `target_<n>`. `tipTexts` adds one text per drawn label: the row's `label`, `Moon up`, each chart line's `label`, and each lane's `Target <n>`. When a lane goes, its key goes, so the box closes by the existing rule. A tap on a label's `.name` text finds no `data-tip` and closes the box, as today (D5).

### 9. `getCardSize()` does not change

The legend makes a narrow card taller. But `getCardSize()` runs before layout and cannot know the card's width, and a phone's masonry view has one column, where the size does not matter. The sections view sizes rows from the content. The card size requirement stays as it is.

## Risks / Trade-offs

- **[Risk] `container-type: inline-size` stops `ha-card` from taking its width from its content.** A parent that sizes the card to its content, such as an unusual custom stack, could squeeze it. → Every built-in Home Assistant view and stack gives the card a width. The manual check covers a masonry view and a sections view.
- **[Risk] A box opened on a rank number on a narrow card has no box to sit above if the card then widens, for example when a phone rotates.** The rank is `display: none`, so its rectangle is empty and the box sits at the card's corner. → Accept: the next tap or pan closes it. Note it in the build if the manual check shows it is worse than that.
- **[Risk] The °C labels cover the first few pixels of the lines at the plot's left edge.** → The backing is only as wide as the text. The check by eye confirms the lines stay readable at 340 px.
- **[Risk] happy-dom cannot show which layout is on screen.** → Assert the container query and its rules as text; check both layouts by hand and record it in the pull request (D7).
- **[Trade-off] Every icon is rendered twice on a narrow card,** once in its label and once in the legend. → The cost is a few kilobytes of DOM; the alternative is Decision 4's rejected `<use>`.

## Migration & Rollback

N/A. The card is one file, built and released as before. Rolling back is installing the previous card version; no data or configuration changes shape.
