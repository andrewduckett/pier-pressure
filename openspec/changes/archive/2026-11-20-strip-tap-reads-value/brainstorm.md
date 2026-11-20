<!-- Plain language: Write questions and answers so a reader without the conversation can understand each decision and its source. Keep the confirmation marker exactly as written. -->

## Story

#254 strip-tap-reads-value — on a phone, tapping the night strip shows what
hovering shows.
https://github.com/andrewduckett/pier-pressure/issues/254

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | What does a tap show, and on what? | A tap on a cell, a Cloud range band, a Moon up or target bar, a dusk, dawn or now line, or the moon drawing shows that item's hover text on the card. | Evidence: #254 packet, Scope |
| D2 | Does a tap on the Temperature chart show its values? | Yes. A tap on one of the chart's hour areas shows its hover text, such as `The hour from 21:00: Temperature 4.2 °C, Dew point 1.0 °C`. | Evidence: #253 design (`openspec/changes/archive/2026-11-19-card-temp-dew-chart/`) and `card/src/chart.ts` (`renderHour`) |
| D3 | Does a tap on a row's message (`Not found`, `Unavailable` or `No forecast` on a row, the Moon up lane or the Temperature chart's key) show its hover text, which names the sensor? | Yes. On a phone it is the only way to learn which sensor is missing. | Assumption |
| D4 | Where does the tapped text appear? | In a small box just above the tapped item, kept inside the card, with long text wrapped. Nothing else on the card moves. | Assumption |
| D5 | Which pointers can tap? | Any pointer: touch, pen or mouse. On a desktop the box shows as well as the browser's own hover tooltip. | Assumption |
| D6 | What closes the box? | A tap elsewhere on the card, or a second tap on the same item. | Evidence: #254 packet, Scope |
| D7 | With the box open, what does a tap on another item or a pan do? | A tap on another item shows that item's text instead. Any pan closes the box: a drag, a wheel or trackpad swipe, an arrow key, or Back to tonight. | Assumption |
| D8 | What does a gesture that is not a tap show? | Nothing. A drag that pans the strip shows no box, and neither does a swipe the browser takes to scroll the page. | Evidence: #254 packet, Scope (drag); Assumption (page scroll) |
| D9 | Does any hover text change? | No. The hover text and the browser's hover tooltip stay as they are. | Evidence: #254 packet, Scope (out) |
| D10 | Is there a keyboard path to the values? | No. That is out of scope. | Evidence: #254 packet, Scope (out) |
| D11 | Which documents change? | The night-card spec (`openspec/specs/night-card/spec.md`) and `docs/night-card.md`. | Evidence: #254 packet, Scope |
| D12 | Home Assistant redraws the card on every state change, and the now line moves every minute. What happens to an open box when the card redraws? | The box stays on the same item, follows it if it moves, and shows that item's latest text. It closes only when the item is no longer on the card, for example when its hour has left the strip or the verdict has gone. | Assumption |

## Changes from the story

- Added: the Temperature chart's hour areas can be tapped (D2). #253 put the
  temperature and dew point values there after the story was written.
- Added: a row's message can be tapped (D3), on a row, the Moon up lane and
  the Temperature chart's key. The story listed only cells, bands, bars, lines
  and the moon drawing.

Confirmed by user: yes
