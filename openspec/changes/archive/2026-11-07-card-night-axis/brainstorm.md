## Story

#182 card-night-axis — dusk, dawn, the moon-up span and a now line cross the
card's strip.
https://github.com/andrewduckett/pier-pressure/issues/182

## Decisions

The user delegated this brainstorm (D1): the agent settled each question it had
a recommendation for, and recorded its reason here. The issue has no comments.

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Who settles the brainstorm's questions? | The agent, wherever it has a recommendation; it asks only when it has none | User |
| D2 | Which specs does the change touch? | Only `night-card`: added requirements for the Sun altitude row, the Moon up lane, the three lines, and their docs. `night-dashboard` is the reference, not changed | Assumption |
| D3 | Where does the Sun altitude row go? | At the top of the strip, above Cloud cover, labelled Sun altitude, as in the YAML strip; the Moon altitude row that sits between them in the YAML strip is a later story | Evidence: `docs/night-dashboard.md` row order |
| D4 | Which entity does the Sun altitude row read? | `sensor.pierpressure_<slug>_sun_altitude`'s `forecast`, with the same hour, clipping, blank-hour and missing-sensor rules as the cloud rows | Evidence: `docs/night-timeline.md`; `night-card` spec, cloud rows |
| D5 | How is a Sun altitude cell shaded? | In the same seven blues: above 0° step 0; above −6° step 1 (civil twilight); above −12° step 2 (nautical); above −18° step 3 (astronomical); −18° or lower step 6, the darkest | Evidence: `docs/night-dashboard.md` YAML Sun altitude band |
| D6 | What does hovering over a Sun altitude cell show? | `Sun altitude, the hour from 21:00: -14.235°`: the value as the forecast holds it, with `°` | Evidence: `docs/night-dashboard.md` YAML unit `°` |
| D7 | Where is the Moon up lane, and what does it read? | Below the four cloud rows, labelled Moon up; it reads `sensor.pierpressure_<slug>_moon_altitude`'s `forecast` | Evidence: `docs/night-dashboard.md` "Under the rows, the Moon up lane" |
| D8 | What makes a Moon up bar? | Each run of consecutive hours whose moon altitude is above 0° is one bar, from the first hour's start to the last hour's end, cut off at the axis ends; a null value, 0° or below, or a missing hour ends a run | Evidence: `docs/night-dashboard.md` YAML `pier_lanes` |
| D9 | What does a Moon up bar look like and show on hover? | Grey `#898781`, rounded, with no text inside, since the lane's label already says Moon up; hovering shows `Moon up from 21:00 to 03:00`, the run's own hours, even where the axis cuts it off; an end the forecast does not reach is left out (`Moon up until 03:00`, `Moon up from 21:00`), and a run of 24 hours or more shows `Moon up` | Assumption |
| D10 | What if the moon sensor is missing, unavailable or has no forecast? | The Moon up lane keeps its label and has no bars, and the card never throws, as for a cloud row | Evidence: #132 Shared decisions ("the card tolerates a missing sensor or attribute"); `night-card` spec, missing cloud sensor |
| D11 | When are the dusk and dawn lines drawn? | Only when the axis comes from the Verdict sensor's `dark_window`: a dashed grey `#898781` line at `start`, labelled dusk, and one at `end`, labelled dawn. On the fallback axis there are no dusk or dawn lines | Evidence: `docs/night-dashboard.md` YAML `shapes` |
| D12 | What does the now line look like, and when is it drawn? | A solid red `#e66767` line labelled now, at the browser's current time, drawn only while that time is on the axis | Evidence: `docs/night-dashboard.md` YAML `shapes`; Assumption for hiding it off the axis |
| D13 | How often does the now line move? | Every minute, on a timer the card starts when it is attached and stops when it is removed; the YAML strip's 5 minutes is a Plotly refresh limit the card does not have | Assumption |
| D14 | How far do the lines reach? | Across the Sun altitude row, the cloud rows and the Moon up lane; their labels sit above the strip's top row; the time labels stay below, uncrossed | Assumption |
| D15 | Do the lines say their time? | Yes: hovering over a line shows `Dusk, 20:30`, `Dawn, 03:25` or `Now, 14:05`, in Home Assistant's time zone, and the same text is its `aria-label`, because the time labels are 3 hours apart | Assumption |
| D16 | Does the fallback axis follow the now line? | Yes: the fallback axis is "6 hours before now to 18 hours after", so each tick recomputes it from the same clock | Evidence: `night-card` spec, "The strip spans the judged night" |
| D17 | Does the change need a glossary term? | No: the night strip's entry already says "with dusk, dawn and the moon on the same time axis", and Moon up lane is the docs' own name | Evidence: `openspec/glossary.md`, "Night strip" |
| D18 | What do the docs say? | `docs/night-card.md` describes the Sun altitude row and its twilight steps, that an altitude is for the start of the hour, the Moon up lane, the dusk, dawn and now lines, and that the now line moves every minute; its opening no longer says dusk, dawn and the moon come later | Evidence: #182 Scope; `docs/night-timeline.md` |
| D19 | How is it seen working before merge? | `mise run dashboard-check` shows the locally built card beside the YAML strip in a real Home Assistant, checked by eye | Evidence: `scripts/dashboard_check.py` |

## Changes from the story

None.

Confirmed by user: yes
