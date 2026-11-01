## ADDED Requirements

### Requirement: Cells and lane bars have rounded corners
Each hour cell in the strip's condition rows and each bar in the Moon up and target lanes SHALL be drawn with rounded corners: a radius of 2 px for a cell and 4 px for a lane bar. Rounding SHALL not change what the cells show: a null hour stays a gap, and hovering over a cell still shows the hour and the value.

#### Scenario: The YAML rounds cells and lane bars
- **WHEN** the strip's traces are read from the dashboard YAML
- **THEN** the trace that draws the condition rows sets a corner radius of 2 px
- **AND** the trace that draws the lanes sets a corner radius of 4 px

#### Scenario: A null hour stays a gap after rounding
- **WHEN** the Seeing forecast holds `{"datetime": "2026-10-31T16:00:00Z", "value": null}`
- **THEN** the Seeing row draws no cell for 16:00 UTC, and hovering there shows nothing

#### Scenario: The check shows rounded corners
- **WHEN** the documented check renders the dashboard in a real Home Assistant
- **THEN** every cell and every lane bar has visibly rounded corners, and the screenshot on the page shows them
