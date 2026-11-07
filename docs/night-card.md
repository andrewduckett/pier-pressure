# The PierPressure card: tonight's verdict on your dashboard

The PierPressure card is a Home Assistant dashboard card. It shows tonight's
verdict, score and confidence for one pier, and tonight's moon beside them.
Under them, a night strip shows every forecast condition hour by hour, and when
each of the ranked targets can be seen. Lines for dusk, dawn and now cross the
strip.

The card only shows what PierPressure already publishes. It never computes a
verdict and never fetches data. If you would rather not install a card, the
[night dashboard](night-dashboard.md) shows the same entities with YAML.

## What the card shows

| Line | What it shows |
|---|---|
| **Verdict** | `GO`, `MAYBE` or `NO-GO`, from the **Verdict** sensor |
| **Score** | The score from 0 to 100. A dash when a gate gives `NO-GO` and there is no score. |
| **Confidence** | The confidence band and value, such as `HIGH · 82` |

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
Hover over the drawing to see its phase and illumination, such as
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
| **Temperature** | `sensor.pierpressure_<pier>_temperature` | °C |
| **Dew point** | `sensor.pierpressure_<pier>_dew_point` | °C |
| **Humidity** | `sensor.pierpressure_<pier>_humidity` | % |
| **Wind speed** | `sensor.pierpressure_<pier>_wind_speed` | km/h |
| **Wind direction** | `sensor.pierpressure_<pier>_wind_direction` | ° |
| **Rain chance** | `sensor.pierpressure_<pier>_precipitation_probability` | % |

Under the rows is the **Moon up** lane, which also reads
`sensor.pierpressure_<pier>_moon_altitude`. Under that is one lane for each
[ranked target](target-ranking.md) tonight.

The strip runs from 4 hours before dusk to 5 hours after dawn, the dark window
on the Verdict sensor. Some nights have no astronomical darkness, such as a
summer night far from the equator. Then the card shows
"No astronomical darkness tonight" under the confidence, and the strip runs
from 6 hours before now to 18 hours after.

#### How to read the rows

Each cell is one hour, shaded in one of seven blues. Darker means more of what
the row names. Seeing and Transparency are the exception: for those two rows,
darker means worse.

| Row | Lightest | Darkest |
|---|---|---|
| Sun altitude | Sun above the horizon | Astronomical night. See the steps below. |
| Moon altitude | Moon on or below the horizon | Moon 30° high or more. One step darker for every 6°. |
| Cloud cover, Cloud low, Cloud mid, Cloud high | Clear | Overcast. One step darker for every 15%. |
| Wind gust, Wind speed | Calm | 42 km/h or more. One step darker for every 7 km/h. |
| Seeing, Transparency | Excellent, 1 | Poor, 0. |
| Temperature, Dew point | Below −5 °C | 20 °C or more. One step darker for every 5 °C. |
| Humidity, Rain chance | 0% | 90% or more. One step darker for every 15%. |

The rows the [night dashboard](night-dashboard.md#how-to-read-the-night-strip)
also has use its shades. It has no Temperature, Dew point, Humidity, Wind
speed, Wind direction or Rain chance row.

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

Temperature and Dew point use the same scale, so you can compare the two rows
by eye. Dew is more likely the closer the dew point comes to the temperature.
Matching shades only mean that both values are in the same 5 °C step, so hover
to see the values.

A **Wind direction** cell has no shade. It holds an arrow that points the way
the wind blows to, as on a weather map. A wind from the south-west has an arrow
pointing north-east.

A **Rain chance** value is the chance of rain or snow in the hour before its
time. So its cell fills the hour before that time: the chance at 22:00 fills
the cell from 21:00 to 22:00.

The **Cloud range** row shows how far the weather forecasts agree on cloud
cover. Each hour has a light blue column. Its height runs from 0% at the bottom
to 100% at the top. A dark blue bar in the column runs from the lowest to the
highest cloud cover any forecast gives for the hour. A tall bar means the
forecasts disagree; a short bar means they agree, and where it sits says how
cloudy they expect it to be. When the forecasts give the same value, the bar is
a thin line. An hour with fewer than two forecasts is blank. The row is twice as
tall as the others, so you can read the bar's ends.

A blank hour in a row means the weather source has no value for that hour.

A row with no cells at all says why, with **Not found**, **Unavailable** or
**No forecast**. Hover over the message to see the sensor's entity id, such as
"sensor.pierpressure_backyard_seeing is unavailable". The **Moon up** lane
reads the Moon altitude sensor, so it shows the same message as the Moon
altitude row. A lane with no bar and no message means the moon stays down.

The **Cloud range** row reads two sensors. It says **Not found** or
**Unavailable** for the first of the two that is missing or unavailable. When
both are there, it says **Needs two forecasts** instead of **No forecast**.
Hover over that message to see
"No hour on the strip has cloud cover from two or more forecasts". With the
default providers, only Open-Meteo gives cloud cover, so the row shows this
message. See
[If something looks wrong](#if-something-looks-wrong) for how to fill it.

| Message | What it means |
|---|---|
| **Not found** | Home Assistant has no entity with the sensor's id. |
| **Unavailable** | The sensor is unavailable. Its forecast is hidden or out of date. |
| **No forecast** | The sensor has no value for any hour on the strip. |
| **Needs two forecasts** | Cloud range only. No hour on the strip has cloud cover from two or more weather forecasts. |

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

Under the Moon up lane, each ranked target tonight has a lane, in rank order.
The lane **Target 1** reads `sensor.pierpressure_<pier>_target_1`, and so on to
**Target 10**, which reads `sensor.pierpressure_<pier>_target_10`.

Each lane has a violet bar over the target's observable window: the time when
the target is above your horizon mask and the sky is astronomically dark. The
bar holds the target's name. A name too long for its bar
ends in "…".

Hover over a bar to see the target's name and its window, such as
"Andromeda Galaxy from 21:00 to 02:00". The times are the window's own, even
where the strip cuts the bar off. A window of 24 hours or more, as on a polar
night, shows only the name.

A rank with no target tonight leaves no lane, so the lanes that are there
follow each other with no gap. On a night with no targets at all, the strip
ends at the Moon up lane.

#### The lines

Three lines cross the strip, through every row, the Moon up lane and the target
lanes:

- A dashed grey line labelled **dusk** at the start of the dark window, and
  one labelled **dawn** at its end. On a night with no astronomical darkness,
  there are no dusk and dawn lines.
- A red line labelled **now** at your browser's current time. The line moves
  every minute, and shows only while now is on the strip.

Hover over a line to see its time, such as "Dusk, 20:30".

#### Times

All times are in your Home Assistant time zone, on a 24-hour clock, whatever
time zone your browser or user profile uses. The axis has a time label every 3
hours, or every 6 hours on a night longer than 15 hours.

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
2. Search for **PierPressure** and select it, or choose **Manual** and paste the
   YAML below.
3. Replace `backyard` with your pier's id: the `id` in PierPressure's `piers`
   setting.
4. Select **Save**.

In a sections view, the card takes the full width of its section. For more room
for the strip, make the section wider.

```yaml
type: custom:pierpressure-card
pier: backyard
```

The card needs `pier`. Without it, Home Assistant shows the error
"pier is required" in place of the card.

## Find your pier's entity id

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
  for the hours on the strip. There are two causes:
  - None of the providers in your pier's `providers` setting supplies that
    condition, or a short-range model does not reach tonight. Add a provider
    that does, under `conditions` in the
    [configuration](../README.md#%EF%B8%8F-configuration).
  - Every weather source failed, so every row says "No forecast", Sun altitude
    and Moon altitude too. The verdict still shows. Check the pier's weather
    source health sensors, such as **Open-Meteo health**. See
    [Watching provider health](../README.md#watching-provider-health).

  Before PierPressure's first verdict, every row says "No forecast" too, except
  Cloud range, which says "Needs two forecasts". The rows fill in when it
  publishes.
- **The Cloud range row says "Needs two forecasts".** Fewer than two weather
  forecasts gave cloud cover for the hours on the strip. There are two causes:
  - Only one provider in the `providers` list under `conditions` gives cloud
    cover. With the default list, only Open-Meteo does. Add a second provider
    that gives cloud cover, such as an Open-Meteo model like `open_meteo_icon`,
    in the [configuration](../README.md#%EF%B8%8F-configuration). The add-on's
    Configuration tab has no `conditions` setting, so for the add-on, set it in
    the `config.yaml` in the add-on's config folder.
  - A listed cloud provider failed. Check that provider's health sensor, such as
    **Open-Meteo ICON health**. See
    [Watching provider health](../README.md#watching-provider-health).
- **"No astronomical darkness tonight".** The sun stays less than 18° below
  the horizon all night, as in summer far from the equator. Nothing is wrong.
  The strip shows the day around now, with no dusk or dawn line.
- **The card shows an older version's layout.** The browser has the old file
  cached. Reload the page while bypassing the cache, for example with
  Ctrl+Shift+R.

To see which version you have, open the browser's developer console. The card
writes a line such as `PIERPRESSURE-CARD 2026.11.0` when it loads.
