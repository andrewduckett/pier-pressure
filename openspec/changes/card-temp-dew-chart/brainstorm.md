<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#253 card-temp-dew-chart — temperature and dew point are drawn as two lines
under the night strip.
https://github.com/andrewduckett/pier-pressure/issues/253

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What replaces the Temperature and Dew point rows? | An SVG chart with a Temperature line and a Dew point line, read from `sensor.pierpressure_<slug>_temperature` and `_dew_point`, on the strip's time axis and moving with every pan. Hovering shows the hour and both values. | Evidence: #253 packet, Scope |
| D2 | What is removed? | The Temperature and Dew point rows, `temperatureShade`, the requirement "Warmer is darker in Temperature and Dew point", and the docs' and spec's naming of those rows as the one exception to "darker is better". | Evidence: #253 packet, Scope; #252 `docs/night-card.md` and `openspec/specs/night-card/spec.md` |
| D3 | What is out of scope? | A Dew risk row, any new sensor, and any change to the core or the delivery. | Evidence: #253 packet, Scope |
| D4 | What is the chart called, and is it part of the night strip? | The Temperature chart, with lines named Temperature and Dew point. It is part of the night strip; the glossary's Night strip entry now names it. | Assumption |
| D5 | Where does the chart sit? | Inside the strip, under the last target lane and above the time labels. The strip's time labels serve it, the dusk, dawn and now lines cross it, and a drag or swipe on it pans the strip. | Assumption |
| D6 | Where is each hour's point drawn on the time axis? | At the middle of the hour that starts at the point's `datetime`, so it lines up with that hour's cells and hover area. | Assumption |
| D7 | How does a line show an hour with no value (null, or no point)? | The line breaks at that hour. An hour with no value on either side shows as a dot. No value is invented. | Assumption |
| D8 | How is the °C scale chosen and labelled? | Fit both lines' values across the whole pan reach, widened to whole 5 °C steps, with a gridline and a label at each step in the label column. The scale stays put while the user pans. | Assumption |
| D9 | What colours are the lines, and how does the reader tell them apart? | Temperature orange, Dew point green, both clear on light and dark themes, with a key in the label column naming each line beside a sample of its colour. | Assumption |
| D10 | What does hovering show? | One hover area per hour, the full height of the chart, showing `The hour from 21:00: Temperature 4.2 °C, Dew point 1.0 °C` in Home Assistant's time zone. A value the hour lacks is left out of the text. An hour with neither value has no hover area. | Assumption |
| D11 | What does the chart show when a line's sensor is missing, unavailable or has no forecast on the strip? | The chart keeps its place. Each line that cannot draw shows the row message (`Not found`, `Unavailable` or `No forecast`) beside its key entry, and hovering over the message names the sensor. When both sensors fail, the chart shows two messages and no lines. | Assumption |
| D12 | Do the temperature and dew point forecasts still count toward how far the strip can pan? | Yes. Both sensors stay in the reach, so a forecast that only they cover can still be panned to. | Assumption |

## Changes from the story

None. The story stands as written.

Confirmed by user: yes
