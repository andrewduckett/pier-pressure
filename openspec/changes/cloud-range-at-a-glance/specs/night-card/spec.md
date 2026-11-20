<!-- Plain language: Name the actor, condition and observable result. Explain necessary domain terms using the agreed glossary. Keep requirement and scenario headings and WHEN/THEN syntax exactly as required. -->

## ADDED Requirements

### Requirement: An hour where the forecasts disagree has an amber Cloud range column
An hour where the forecasts disagree is one whose cloud cover max value minus its min value is more than 35 points, with each value first drawn at 0 when below 0 and at 100 when above 100, as its range bar is. The card SHALL shade the Cloud range column of such an hour amber `#b58900` instead of grey, and keep its range bar the grey `#404040`. This holds for every Cloud range column the strip draws, panned or not. The 35-point edge SHALL be fixed: no card option changes it.

#### Scenario: Forecasts 50 points apart
- **WHEN** the min and max forecasts hold 20 and 70 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#b58900` and its range bar `#404040`

#### Scenario: Forecasts exactly 35 points apart
- **WHEN** the min and max forecasts hold 20 and 55 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#8c8c8c`

#### Scenario: Forecasts just over 35 points apart
- **WHEN** the min and max forecasts hold 20 and 55.5 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#b58900`

#### Scenario: Values outside 0 to 100
- **WHEN** the min and max forecasts hold -5 and 31 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#8c8c8c`, because its bar runs from 0 to 31

#### Scenario: An hour reached by panning
- **WHEN** the min and max forecasts hold 10 and 90 at an hour past the opening axis's end, and the user pans the strip until that hour is on the axis
- **THEN** that hour's column is shaded `#b58900`

### Requirement: The docs say what an amber Cloud range column means
Where `docs/night-card.md` describes the Cloud range row, it SHALL say that an amber column marks an hour where the forecasts disagree by more than 35 points, so its cloud forecast is not to be trusted. It SHALL say that this is the same 35-point edge PierPressure uses when it lowers confidence because the forecasts disagree. It SHALL show the hover text of such an hour.

#### Scenario: The Cloud range text explains amber
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** its Cloud range text names the words amber, 35 and confidence
- **AND** it holds an example hover text that ends `, the forecasts disagree`

## MODIFIED Requirements

### Requirement: The Cloud range row has its own shades and height
The Cloud range row SHALL be twice as tall as a shaded row. Each hour column SHALL be the grey `#8c8c8c`, unless its hour is one where the forecasts disagree, and each range bar the darker grey `#404040`, not blue, because the row shows how far the forecasts agree rather than good or bad. A range bar SHALL stay inside its column.

#### Scenario: The shades
- **WHEN** the min and max forecasts hold 40 and 70 at 2026-10-31T21:00:00Z
- **THEN** that hour's column is shaded `#8c8c8c` and its range bar `#404040`

### Requirement: The Cloud range greys stand out on the default themes
Each Cloud range bar SHALL have a contrast ratio of at least 3:1 against its column, grey or amber. Each column, grey or amber, SHALL have a contrast ratio of at least 3:1 against Home Assistant's default card background in the light theme, `#ffffff`, and in the dark theme, `#1c1c1c`. Contrast ratios are as WCAG 2.2 defines them.

#### Scenario: The bar against its column
- **WHEN** the contrast ratio of the range bar's grey against the column's grey is computed
- **THEN** it is at least 3:1

#### Scenario: The column against the light and dark card
- **WHEN** the contrast ratio of the column's grey is computed against `#ffffff` and against `#1c1c1c`
- **THEN** both are at least 3:1

#### Scenario: The bar against an amber column
- **WHEN** the contrast ratio of the range bar's grey against the amber column's colour is computed
- **THEN** it is at least 3:1

#### Scenario: The amber column against the light and dark card
- **WHEN** the contrast ratio of the amber column's colour is computed against `#ffffff` and against `#1c1c1c`
- **THEN** both are at least 3:1

### Requirement: Hovering over a Cloud range column shows both values
Hovering over a Cloud range column SHALL show `Cloud range, the hour from <HH:MM>: <min>% to <max>%`, with the values as the forecasts hold them. For an hour where the forecasts disagree, the text SHALL end `, the forecasts disagree`. A screen reader SHALL read the same text.

#### Scenario: Forecasts that disagree
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 40 and 70.5 at 2026-10-31T21:00:00Z
- **THEN** hovering over that column shows `Cloud range, the hour from 21:00: 40% to 70.5%`

#### Scenario: Forecasts more than 35 points apart
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 20 and 70 at 2026-10-31T21:00:00Z
- **THEN** hovering over that column shows `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`
- **AND** a screen reader reads the column as `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`
- **AND** a tap on that column shows a box that reads `Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree`

#### Scenario: Forecasts exactly 35 points apart
- **WHEN** Home Assistant's time zone is `UTC` and the min and max forecasts hold 20 and 55 at 2026-10-31T21:00:00Z
- **THEN** hovering over that column shows `Cloud range, the hour from 21:00: 20% to 55%`

### Requirement: The docs say the Cloud range row is grey
Where `docs/night-card.md` describes the Cloud range row, it SHALL say that its bar is grey and its column grey or amber, because the row shows how far the forecasts agree, not whether an hour is good or bad.

#### Scenario: The Cloud range text names its greys
- **WHEN** the part of `docs/night-card.md` before its "If something looks wrong" section is read
- **THEN** its Cloud range text names the words grey, amber and agree
- **AND** it no longer calls the Cloud range column or bar blue
