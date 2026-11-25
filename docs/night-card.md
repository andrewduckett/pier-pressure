# The PierPressure card: tonight's verdict on your dashboard

The PierPressure card is a Home Assistant dashboard card. It shows tonight's
verdict, score and confidence for one pier, and tonight's moon beside them.
Under them, a night strip shows every forecast condition hour by hour, and when
each of the ranked targets can be seen. Lines for dusk, dawn and now cross the
strip.

The card only shows what PierPressure already publishes. It never computes a
verdict and never fetches data.

## What the card shows

| Line | What it shows |
|---|---|
| **Verdict** | `GO`, `MAYBE` or `NO-GO`, from the **Verdict** sensor |
| **Score** | The score from 0 to 100. A dash when a gate gives `NO-GO` and there is no score. |
| **Confidence** | The confidence band and value, such as `HIGH · 82` |
| **Reasons** | The reasons for the verdict, in order, from the Verdict sensor's `reasons`. A `NO-GO` from a gate names the gate that failed, such as a wind gust over your limit. Times in a reason show in your Home Assistant time zone. When your equipment is set, notes about the top target come after the scoring reasons. |

The card shows a message instead when:

- PierPressure is offline: "PierPressure is offline".
- It cannot find the Verdict sensor: "No PierPressure verdict found", with the
  entity id it looked for. See [Find your pier's entity id](#find-your-piers-entity-id).

A dash in every line means PierPressure has not published its first verdict
since it started. The lines fill in when it does.

### The Moon section

Beside the verdict lines, the **Moon** section shows tonight's moon. It reads
the Verdict sensor's `moon` attribute. On a narrow card, it moves under the
verdict lines.

| Line | What it shows |
|---|---|
| **Phase** | One of eight phases, from New through Waxing crescent, First quarter and Waxing gibbous to Full, then Waning gibbous, Last quarter and Waning crescent |
| **Illumination** | How much of the moon's face is lit, as a whole percent, such as `78%` |
| **Moonrise** | When the moon rises, if it rises during the dark window |
| **Moonset** | When the moon sets, if it sets during the dark window |

Phase and Illumination are for the time PierPressure last computed the verdict,
not for a time during the night. Both change slowly, so they differ little from
the moon you see after dusk. Near the boundary between two phases, the phase
can change before the night starts.

The dark window runs from dusk to dawn: the time the sun is at least 18° below
the horizon. A dash for Moonrise or Moonset means the moon does not rise or set
during the dark window. It may be up all night, down all night, or rise or set
in daylight or twilight. The **Moon up** lane on the strip shows when it is up.
On a night with no dark window, when the card says
"No astronomical darkness tonight", Moonrise and Moonset always show a dash.
A dash in every Moon line means PierPressure has not published its first
verdict yet.

#### How to read the moon drawing

The drawing shows the moon's face, with the lit part in pale grey. The lit
part's share of the disc is the illumination: at 25%, a quarter of the disc's
width is lit. A waxing moon, growing towards full, is lit on the right. A
waning moon, shrinking towards new, is lit on the left. That is how the moon
looks from the northern hemisphere. When Home Assistant's location is south of
the equator, the drawing mirrors both, as the moon looks from there.

The card takes the hemisphere from Home Assistant's location, not the pier's,
because the verdict carries no location. So the drawing for a pier in the other
hemisphere from Home Assistant is mirrored. The phase and the illumination are
still right.

A new moon is drawn unlit and a full moon fully lit, even when the illumination
is a few percent off. The phase does not say which side such a sliver is on.
Hover over or tap the drawing to see its phase and illumination, such as
"Moon: waxing gibbous, 78% lit". The drawing is left out when the phase or the
illumination is missing.

### The night strip

Under the verdict, the strip shows the night hour by hour, one row per
condition, from top to bottom:

| Row | Sensor | Unit |
|---|---|---|
| **Sun altitude** | `sensor.pierpressure_<pier>_sun_altitude` | ° |
| **Moon altitude** | `sensor.pierpressure_<pier>_moon_altitude` | ° |
| **Cloud cover** | `sensor.pierpressure_<pier>_cloud_cover` | % |
| **Cloud range** | `sensor.pierpressure_<pier>_cloud_cover_min` and `sensor.pierpressure_<pier>_cloud_cover_max` | % |
| **Cloud low** | `sensor.pierpressure_<pier>_cloud_low` | % |
| **Cloud mid** | `sensor.pierpressure_<pier>_cloud_mid` | % |
| **Cloud high** | `sensor.pierpressure_<pier>_cloud_high` | % |
| **Wind gust** | `sensor.pierpressure_<pier>_wind_gust` | km/h |
| **Seeing** | `sensor.pierpressure_<pier>_seeing` | none: 0 to 1, where 1 is best |
| **Transparency** | `sensor.pierpressure_<pier>_transparency` | none: 0 to 1, where 1 is best |
| **Humidity** | `sensor.pierpressure_<pier>_humidity` | % |
| **Wind speed** | `sensor.pierpressure_<pier>_wind_speed` | km/h |
| **Wind direction** | `sensor.pierpressure_<pier>_wind_direction` | ° |
| **Rain chance** | `sensor.pierpressure_<pier>_precipitation_probability` | % |

Under the rows is the **Moon up** lane, which also reads
`sensor.pierpressure_<pier>_moon_altitude`. Under that is one lane for each
rank with a [ranked target](target-ranking.md) on any night. Under the lanes, the Temperature
chart draws the temperature and the dew point as two lines. See
[The Temperature chart](#the-temperature-chart).

The strip opens from 4 hours before dusk to 5 hours after dawn, the dark window
on the Verdict sensor. Once the night has started, the strip opens
4 hours before now instead, so it never opens on hours long gone. It
keeps its length and moves on with the clock every minute, so late in the
night it shows more of the morning. Some nights have no astronomical darkness, such as a
summer night far from the equator. Then the card shows
"No astronomical darkness tonight" under the confidence, and the strip opens
from 6 hours before now to 18 hours after. You can pan the strip to the other
hours of the forecast. See [Panning the strip](#panning-the-strip).

#### The labels and the legend

Each row's label, the Moon up lane's label and each entry in the Temperature
chart's key has a small icon. A target lane has no icon: its label is
**Target 1**, **Target 2** and so on.

The layout follows the card's width, not the screen's, so a narrow card on a
wide screen still gets the narrow layout. The cut-off is 450 px:

- A card 450 px or wider shows each icon beside its label, such as the Seeing
  icon and then **Seeing**. It has no legend.
- A card narrower than 450 px shows only the icons and the rank numbers, so
  the hours get more of the card's width. A target lane's label is its rank
  number, `1` to `10`. A key entry keeps its colour sample, and its message
  when it has one. A legend under the strip names each icon the strip draws,
  in the strip's order. When the strip has a target lane, the legend ends with
  a rank number and `Target rank`.

Hover over or tap an icon or a rank number to see its name.

#### How to read the rows

Each cell is one hour, shaded in one of seven blues. On every shaded row,
darker means better for observing: a darker sky, less cloud, less wind, better
seeing.

| Row | Darkest | Lightest |
|---|---|---|
| Sun altitude | Astronomical night. See the steps below. | Sun above the horizon |
| Moon altitude | Moon on or below the horizon | Moon 30° high or more. One step lighter for every 6°. The shade ignores the moon's phase, so a crescent and a full moon at the same height match. |
| Cloud cover, Cloud low, Cloud mid, Cloud high | Clear | Overcast. One step lighter for every 15%. |
| Wind gust, Wind speed | Calm | 42 km/h or more. One step lighter for every 7 km/h. |
| Seeing, Transparency | Excellent, 1 | Poor, 0. |
| Humidity, Rain chance | 0% | 90% or more. One step lighter for every 15%. |

In the **Sun altitude** row, the blue darkens as the sun goes down:

| Shade | The sun's altitude |
|---|---|
| Lightest | Above the horizon |
| Light | Civil twilight, down to −6° |
| Middle | Nautical twilight, down to −12° |
| Dark | Astronomical twilight, down to −18° |
| Darkest | Astronomical night, −18° or lower |

The sun's and the moon's altitude are for the start of the hour. So the dusk
line can fall inside an hour still shaded as twilight.

A **Wind direction** cell has no shade. It holds an arrow that points the way
the wind blows to, as on a weather map. A wind from the south-west has an arrow
pointing north-east.

A **Rain chance** value is the chance of rain or snow in the hour before its
time. So its cell fills the hour before that time: the chance at 22:00 fills
the cell from 21:00 to 22:00.

The **Cloud range** row shows how far the weather forecasts agree on cloud
cover. Its bar is grey and its column grey or amber, because the row shows
agreement, not whether an hour is good or bad for observing. Each hour has a
column. Its height runs from 0% at the bottom to 100% at the top. A darker grey
bar in the column runs from the lowest to the highest cloud cover any forecast
gives for the hour. Where the bar sits says how cloudy the forecasts expect it
to be. Its length says how far they disagree: a short bar means they agree, a
long bar that they disagree. When the forecasts give the same value, the bar is
a thin line. An hour with fewer than two forecasts is blank. The row is twice as
tall as the others, so you can read the bar's ends.

An amber column marks an hour where the forecasts disagree by more than 35
points, so its cloud forecast is not to be trusted. It is the same 35-point
edge PierPressure uses when it lowers its confidence because the forecasts
disagree. Hover over such an hour to see, for example,
"Cloud range, the hour from 21:00: 20% to 70%, the forecasts disagree".

A blank hour in a row means the weather source has no value for that hour.

A row with no cells at all says why, with **Not found**, **Unavailable** or
**No forecast**. Hover over the message to see the sensor's entity id, such as
"sensor.pierpressure_backyard_seeing is unavailable". The **Moon up** lane
reads the Moon altitude sensor, so it shows the same message as the Moon
altitude row. A lane with no bar and no message means the moon stays down.

The **Cloud range** row reads two sensors. It says **Not found** or
**Unavailable** for the first of the two that is missing or unavailable. When
both are there but no hour of the whole forecast has cloud cover from two or
more weather forecasts, the card leaves the row out. With the default
providers, only Open-Meteo gives cloud cover, so the strip has no Cloud range
row. When two forecasts give cloud cover but not for the hours on the strip,
as when you pan past the shorter one, the row says **No forecast**. Hover over
it to see "No hour on the strip has cloud cover from two or more forecasts".
See [If something looks wrong](#if-something-looks-wrong) for how to bring
the row back.

| Message | What it means |
|---|---|
| **Not found** | Home Assistant has no entity with the sensor's id. |
| **Unavailable** | The sensor is unavailable. Its forecast is hidden or out of date. |
| **No forecast** | The sensor has no value for any hour on the strip. |

The other rows draw as usual. See [If something looks wrong](#if-something-looks-wrong)
for what to do.

Hover over a cell to see its row, the hour it starts and its value with its
unit, such as "Cloud cover, the hour from 21:00: 40%",
"Wind gust, the hour from 21:00: 12.5 km/h" or
"Sun altitude, the hour from 21:00: -14.235°". Seeing and Transparency have no
unit. A Wind direction cell also names the compass point the wind blows from,
such as "Wind direction, the hour from 21:00: 225° from SW". A Cloud range
hour shows both ends of its bar, such as
"Cloud range, the hour from 21:00: 40% to 70%".

The **Moon up** lane has a grey bar for each run of hours
when the moon is above the horizon. Like the sun's, each moon altitude is for
the start of its hour, so a bar can start up to an hour before moonrise and end
up to an hour after moonset. Hover over a bar to see when the moon rises and
sets, such as "Moon up from 21:00 to 03:00". The text names a rise or set only
when the forecast holds the hour before or after it. A bar at the start of the
forecast reads "Moon up until 03:00", one at its end "Moon up from 21:00", and
a run of a day or more just "Moon up".

#### The target lanes

Under the Moon up lane, each rank with a target on any night has a lane, in
rank order. Tonight, the lane **Target 1** reads
`sensor.pierpressure_<pier>_target_1`, and so on to **Target 10**, which reads
`sensor.pierpressure_<pier>_target_10`. A later night's bars read the
`targets` attribute of its Night sensor, from Night 2 to Night 4.

A lane can hold a bar for each night: tonight's, and one for each later night
the forecast reaches. Each bar is named for its own night's target at that
rank. Each night is ranked on its own moon, so a bright moon later in the week
can put different targets in the same lane.

Each bar is violet, over its target's observable window: the time when the
target is above your horizon mask and the sky is astronomically dark. The bar
holds the target's name and its catalog id, such as
"Andromeda Galaxy (M31)": the id is what you type into your mount or planetarium
app. A target the catalog gives no name shows its id alone, such as "IC2184".
A bar too short for both shortens the name, ending it in "…", and keeps the
catalog id whole.

Hover over a bar to see the target's name, catalog id and window, such as
"Andromeda Galaxy (M31) from 21:00 to 02:00". The times are the window's own,
even where the strip cuts the bar off. A window of 24 hours or more, as on a
polar night, shows only the name and id.

A rank with no target on any night leaves no lane, so the lanes that are there
follow each other with no gap. When no night has a target at all, the
Temperature chart follows the Moon up lane.

#### The Temperature chart

Under the last target lane, the **Temperature chart** draws two lines on the
strip's time axis. Dew is more likely the closer the two lines come: when the
temperature falls to the dew point, dew forms on your optics.

| Line | Colour | Sensor |
|---|---|---|
| **Temperature** | Orange | `sensor.pierpressure_<pier>_temperature` |
| **Dew point** | Green | `sensor.pierpressure_<pier>_dew_point` |

The key in the label column names each line, with its icon, beside a sample
of its colour. The
dew point line is normally the lower one. It can cross above the temperature
line when the two values come from different weather sources.

Each point sits at the middle of the hour it is for, so it lines up with that
hour's cells in the rows above. A line has a break where an hour has no value.
A value with no value on either side of it shows as a dot.

The scale is in °C, with a gridline and a label every 5 °C. The labels sit
inside the chart's left edge, over the lines, on a backing in the card's
colour. A hover or a tap where a label sits still reaches the hour under it.
The scale fits both
lines' values over the whole forecast, not only the hours on the strip, so it
stays put while you pan. The chart is 16 px tall for every 5 °C, and covers at
least 10 °C.

Hover over an hour to see both values, such as
"The hour from 21:00: Temperature 4.2 °C, Dew point 1.5 °C". An hour with a
value on only one line shows that one value.

A line with no value for any hour on the strip draws nothing, and shows
**Not found**, **Unavailable** or **No forecast** beside its key entry. These
mean what they mean on a row. Hover over the message to see the sensor's
entity id. The other line still draws.

#### The lines

Three lines cross the strip, through every row, the Moon up lane, the target
lanes and the Temperature chart:

- A dashed grey line labelled **dusk** at the start of the dark window, and
  one labelled **dawn** at its end. On a night with no astronomical darkness,
  there are no dusk and dawn lines.
- A red line labelled **now** at your browser's current time. The line moves
  every minute, and shows only while now is on the strip.

Hover over a line to see its time, such as "Dusk, 20:30".

#### Reading a value on a phone

A phone has no pointer to hover with, so tap instead. Tap a cell, a Cloud
range column, a Moon up or target bar, a line, a Temperature chart hour, a
message, an icon, a rank number or the moon drawing, and a small box shows the
same text that hovering shows. The box sits just above the item, or just below it near the top of the
card, and moves nothing else on the card.

A tap works with any pointer: a finger, a pen or a mouse click. On a computer,
the box shows beside the browser's own hover text. A press that moves more
than a few pixels is not a tap, so a drag or a swipe opens no box.

One box shows at a time. A tap on another item shows that item's text
instead. A tap elsewhere on the card closes the box, such as on the text of a
row's label, the legend or the verdict. A second tap on the same item closes the box too. Any pan of
the strip closes the box: a drag, a swipe, the arrow keys or
**Back to tonight**. While the box shows, it keeps up with new forecasts, and
it closes when its item leaves the strip.

#### Panning the strip

The strip opens on the judged night. To see the hours before or after it, pan
the strip sideways:

- With a mouse, drag the strip left or right.
- On a phone or tablet, swipe the strip left or right with one finger. An up
  or down swipe scrolls the page, as it does elsewhere.
- On a laptop, swipe sideways with two fingers on the trackpad.
- With a keyboard, press Tab until the strip has focus, then use the Left and
  Right arrow keys. Each press moves the strip one hour.

Drag to the left to see later hours, as if you were moving the strip itself.
Every row and lane moves together, and so do the Temperature chart's lines,
the lines across the strip, the time labels and the day labels. The row
labels, and the Temperature chart's key and scale, stay where they are. The
strip keeps its length: it shows as many hours as when it opened.

The strip stops at the first and last forecast hour. How far ahead that is
depends on your weather sources. Each forecasts its own distance ahead:
Open-Meteo, for example, about three days.

Up to three later nights have a dusk line and a dawn line too, as far as the
forecast reaches. Each later night also has its own target bars. The card reads
them from the Night 2 to Night 4 sensors, `sensor.pierpressure_<pier>_night_2` to
`sensor.pierpressure_<pier>_night_4`. A later night with no astronomical
darkness has neither line and no target bars, and its **Sun altitude** row
still shows how dark it gets.

PierPressure judges one night, so only that night has a verdict and a score. A
later night's target bars show what is worth pointing at that night, not
whether the night is worth setting up for.

Once you have panned, the strip stays on the same hours when PierPressure
publishes a new verdict. The exception is a pan to later hours: once the
strip's opening hours catch up with it, as the clock moves on or with a new
verdict, the strip follows now again. While the strip is off the judged night, a
**Back to tonight** button shows above it. Select it to go back. Reloading the
page also opens the strip on the judged night.

#### Times

All times are in your Home Assistant time zone, on a 24-hour clock, whatever
time zone your browser or user profile uses. The axis has a time label every 3
hours, or every 6 hours on a night longer than 15 hours.

Under the time labels, a row of day labels names each day on the strip, such
as `Thu 26 Nov`. A day starts at midnight in your Home Assistant time zone, and
a thin divider marks that start across the time labels and the day labels. On
the rare day whose clock skips midnight, the day starts at the first time the
clock shows, such as 01:00. Each day's label sits just right of its divider.
The label of the day in progress at the strip's left edge stays at that edge as
you pan the strip, so you can always tell which day you are looking at. A label
with no room before the next day starts or the strip ends is hidden, not cut
off, and its divider still shows.

## Before you start

You need Home Assistant with PierPressure's entities in it. See the
[README](../README.md#-home-assistant-entities).

The card's version is the same as PierPressure's. Install the card from the
same release as the PierPressure you run, and update both together.

## Install the card

Choose one of these two ways.

### With HACS

[HACS](https://hacs.xyz) is the Home Assistant Community Store. It installs
the card from this repository's releases and offers you each update. This
works from the first release that carries `pierpressure-card.js`; earlier
releases have no card.

1. In Home Assistant, open **HACS**.
2. Open the three-dot menu and select **Custom repositories**.
3. Enter `https://github.com/andrewduckett/pier-pressure` as the repository,
   choose **Dashboard** as the type, and select **Add**.
4. Search for **PierPressure**, open it, and select **Download**.
5. Reload the browser page when HACS asks you to.

HACS adds the card as a dashboard resource for you.

### By hand

1. Download `pierpressure-card.js` from the
   [latest release](https://github.com/andrewduckett/pier-pressure/releases/latest).
2. Copy it to `/config/www` on your Home Assistant. Home Assistant serves that
   folder at `/local/`.
3. Go to **Settings** > **Dashboards**, open the three-dot menu, and select
   **Resources**. If you do not see **Resources**, turn on **Advanced mode** in
   your user profile first.
4. Select **Add resource**. Enter `/local/pierpressure-card.js` as the URL,
   choose **JavaScript module** as the type, and select **Create**.
5. Reload the browser page.

To update the card, download the new file, copy it over the old one, and
reload the page.

## Add the card to a dashboard

1. Open a dashboard, select the pencil to edit it, then select **Add card**.
2. In the card picker, search for **PierPressure** and select it. The picker
   shows a preview of the card for the first pier it finds.
3. In the card's editor, pick your pier from the **Pier** list. The list holds
   each pier whose Verdict sensor Home Assistant has. If your pier is not in
   the list, type its id: the `id` in PierPressure's `piers` setting.
4. Select **Save**.

If the editor says "No PierPressure piers found", Home Assistant has no
PierPressure Verdict sensor yet. Check that PierPressure is running, or type
your pier's id.

The list shows each pier by its id. Once you pick a pier, the field shows the
value the card stores. For most piers that is the id. For a pier id the card
cannot turn into an entity id, such as one in another alphabet, it is the part
of the entity id between `pierpressure_` and `_verdict`.

In a sections view, the card takes the full width of its section. For more room
for the strip, make the section wider.

### With YAML

Instead of the editor, you can choose **Manual** in the card picker and paste
this YAML. Replace `backyard` with your pier's id.

```yaml
type: custom:pierpressure-card
pier: backyard
```

The card needs `pier`. Without it, Home Assistant shows the error
"pier is required" in place of the card.

## Find your pier's entity id

The **Pier** list in the card's editor already uses the real entity id. You
need this section only when you write the card's YAML yourself.

The card reads `sensor.pierpressure_<pier>_verdict`. It writes your pier's id
the way Home Assistant writes an entity id: in lower case, without accents,
with each run of other characters as one `_`. A pier with the id `Back-Yard`
has `sensor.pierpressure_back_yard_verdict`.

Home Assistant also spells out some letters that the card cannot, such as `ß`
or letters from other alphabets. For such a pier id, or if you renamed the
entity, the card says "No PierPressure verdict found". To check the real id,
find your **Verdict** sensor under **Settings** > **Entities**. Then use, as
`pier`, the part between `pierpressure_` and `_verdict`.

## If something looks wrong

- **"Custom element doesn't exist: pierpressure-card".** The card is not
  installed, or the browser has not loaded it yet. Install it as above, then
  reload the page.
- **"PierPressure is offline".** Home Assistant has lost PierPressure: it has
  stopped, or it cannot reach your MQTT broker. Check that PierPressure is
  running. The card fills in again when it comes back.
- **"No PierPressure verdict found".** The card cannot find the Verdict sensor
  it names. Check your `pier` key, as
  [Find your pier's entity id](#find-your-piers-entity-id) says. On a new
  install, wait for PierPressure's first verdict.
- **A row says "Not found".** Home Assistant has no sensor with the id the
  message's hover shows. The card looks for it the same way as the Verdict
  sensor. Check the id under **Settings** > **Entities**. If you disabled the
  sensor, enable it. If your PierPressure is older than the card, update both
  from the same release.
- **A row says "Unavailable".** That one sensor is unavailable, though the
  Verdict sensor is not. PierPressure makes all its sensors unavailable
  together when it stops, so this usually lasts only while Home Assistant
  catches up. If it stays, restart PierPressure, so it publishes every sensor
  again.
- **A row says "No forecast".** No weather source gave that condition a value
  for the hours on the strip. There are three causes:
  - None of the providers in your pier's `providers` setting supplies that
    condition, or a short-range model does not reach tonight. Add a provider
    that does, under `conditions` in the
    [configuration](../README.md#%EF%B8%8F-configuration).
  - You panned the strip to a later night, past the last hour that condition's
    weather source forecasts. Weather sources forecast different distances
    ahead, so some rows stop before others. Select **Back to tonight**.
  - Every weather source failed, so every row says "No forecast", Sun altitude
    and Moon altitude too. The verdict still shows. Check the pier's weather
    source health sensors, such as **Open-Meteo health**. See
    [Watching provider health](../README.md#watching-provider-health).

  Before PierPressure's first verdict, every row says "No forecast" too, and
  so do both lines of the Temperature chart. The strip has no Cloud range
  row. The rows fill in when it publishes.
- **The strip has no Cloud range row.** No hour of the forecast has cloud
  cover from two or more weather forecasts, so the card leaves the row out.
  There are two causes:
  - Only one provider in the `providers` list under `conditions` gives cloud
    cover. With the default list, only Open-Meteo does. Add a second provider
    that gives cloud cover, such as an Open-Meteo model like `open_meteo_ecmwf`,
    in the [configuration](../README.md#%EF%B8%8F-configuration). The add-on's
    Configuration tab has no `conditions` setting, so for the add-on, set it in
    the `config.yaml` in the add-on's config folder.
  - A listed cloud provider failed for a whole fetch. Check that provider's
    health sensor, such as **Open-Meteo ECMWF health**. See
    [Watching provider health](../README.md#watching-provider-health).
- **"No astronomical darkness tonight".** The sun stays less than 18° below
  the horizon all night, as in summer far from the equator. Nothing is wrong.
  The strip shows the day around now, with no dusk or dawn line.
- **The card shows an older version's layout.** The browser has the old file
  cached. Reload the page while bypassing the cache, for example with
  Ctrl+Shift+R.

To see which version you have, open the browser's developer console. The card
writes a line such as `PIERPRESSURE-CARD 2026.11.0` when it loads.
