# The night timeline: chart the hours in Home Assistant

The verdict tells you whether tonight is worth setting up for. The timeline
shows you why, hour by hour. This page explains what the timeline holds, how the
timeline sensors deliver it to Home Assistant, and how to chart it.

## What the timeline is

The verdict document has a `timeline` field: a list with one entry per clock
hour. It covers every hour the weather sources returned, usually two to three
days, including hours that have already passed. Entries are in time order.

Each entry has the same keys, always present:

| Key | Meaning |
|---|---|
| `time` | The start of the hour, in UTC, ending in `Z`. |
| `sun_altitude`, `moon_altitude` | The height of the sun's and the moon's centre above the horizon, in degrees, to three decimal places. Negative means below the horizon. Computed offline by PierPressure. |
| `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high` | Total cloud and its low, middle and high layers, in percent, from Open-Meteo. |
| `wind_gust` | The forecast gust in km/h, from Open-Meteo. |
| `seeing`, `transparency` | Quality from 0 to 1, where 1 is best, from 7Timer!. Two decimal places. |

A weather value is `null` when its source has no data for that hour. The sun and
moon altitudes are always present.

The timeline is evidence, not a decision. The verdict still judges one night,
the one `dark_window` names. Clear hours on a later night do not change
tonight's verdict, and the timeline makes no verdict about that later night.

## The timeline sensors

Each pier's device has one sensor per timeline value. Its entity id ends in the
value's key. For a pier called `backyard`, the Cloud cover sensor is
`sensor.pierpressure_backyard_cloud_cover`.

| Entity id | Unit | State |
|---|---|---|
| `sensor.pierpressure_<pier>_cloud_cover` | % | Total cloud cover |
| `sensor.pierpressure_<pier>_cloud_low` | % | Low cloud cover |
| `sensor.pierpressure_<pier>_cloud_mid` | % | Middle cloud cover |
| `sensor.pierpressure_<pier>_cloud_high` | % | High cloud cover |
| `sensor.pierpressure_<pier>_wind_gust` | km/h | The forecast gust |
| `sensor.pierpressure_<pier>_seeing` | none | Seeing, from 0 to 1, where 1 is best |
| `sensor.pierpressure_<pier>_transparency` | none | Transparency, from 0 to 1, where 1 is best |
| `sensor.pierpressure_<pier>_sun_altitude` | ° | The sun's altitude at the start of the current hour |
| `sensor.pierpressure_<pier>_moon_altitude` | ° | The moon's altitude at the start of the current hour |

Every timeline sensor works the same way:

- **State:** the value for the current hour, as the timeline holds it.
- **`forecast` attribute:** one point per timeline hour, in order. Each point is
  `{ "datetime": "<time>", "value": <value> }`. An hour with no value stays in
  the list with `value: null`, so every sensor's points line up with the
  timeline hour for hour.
- **`hour` attribute:** the start of the hour the state belongs to, or `null`.
  Each sensor judges its own value, so Seeing can be unknown while Cloud low has
  a value in the same hour.

When the current hour has no value for a sensor, or the timeline is empty, its
state is `unknown`. It never shows `0` or an older value instead. The sensor stays
available, so `forecast` is still there for a chart. It is unavailable only when
PierPressure is offline, and then Home Assistant hides all its attributes.

Every timeline sensor shows `unknown` when no weather source returned the
current hour: the altitudes too. A timeline entry, and the altitudes in it, is
always present for each hour a source returned, but there is no entry for an
hour no source returned. To tell whether it is dark, use the Verdict sensor's
`dark_window` instead.

### An altitude is for the start of the hour

The Sun altitude and Moon altitude states are the altitude at the start of the
current hour, as the timeline holds it, not the live sky. Together with the
recompute interval, a state can trail the live sky by up to one hour plus one
recompute interval. Do not use them for an automation that needs the sun's or
moon's position to the minute.

### The state can be up to one recompute old

PierPressure recomputes on the interval you set in `recompute.interval_seconds`.
The "current hour" is the hour that contains the verdict's `generated_at`. With a
three-hour interval, for example, the state can be for an hour that started up
to three hours ago. Read the `hour` attribute to see which hour the state is for. Press
the **Refresh** button to recompute now.

## Why the Verdict sensor leaves the timeline out

Home Assistant does not store state attributes larger than 16 KiB. A timeline of
around 120 hours with ten values each would push the Verdict sensor past that
limit. So the Verdict sensor's attributes hold every field of the verdict
document except `timeline`. Each timeline value reaches Home Assistant on its own
sensor instead: Cloud cover, Cloud low, Cloud mid, Cloud high, Wind gust,
Seeing, Transparency, Sun altitude and Moon altitude.

## Chart the forecast

This example uses [apexcharts-card](https://github.com/RomRider/apexcharts-card),
a custom card you install through HACS. It draws the `forecast` attribute as
columns, with a line marking now.

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Cloud cover
graph_span: 48h
span:
  start: day
now:
  show: true
yaxis:
  - min: 0
    max: 100
series:
  - entity: sensor.pierpressure_backyard_cloud_cover
    name: Cloud cover
    type: column
    unit: "%"
    data_generator: |
      return (entity.attributes.forecast ?? []).map((point) => [
        new Date(point.datetime).getTime(),
        point.value,
      ]);
```

Replace `backyard` with your pier's id. The `?? []` keeps the card working while
PierPressure is offline, when Home Assistant hides the sensor's attributes.

## Keep the forecast out of the recorder

PierPressure rewrites the forecast on every recompute. Home Assistant's recorder
saves each new copy, which adds to your database over time, and the history of a
forecast is rarely useful. To stop recording the timeline sensors, add them to
the recorder's exclusions in `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
      - sensor.pierpressure_backyard_cloud_cover
      - sensor.pierpressure_backyard_cloud_low
      - sensor.pierpressure_backyard_cloud_mid
      - sensor.pierpressure_backyard_cloud_high
      - sensor.pierpressure_backyard_wind_gust
      - sensor.pierpressure_backyard_seeing
      - sensor.pierpressure_backyard_transparency
      - sensor.pierpressure_backyard_sun_altitude
      - sensor.pierpressure_backyard_moon_altitude
```

Each pier has its own nine sensors. For a second pier, add its nine entity ids
too.

The card above reads the live attributes, so it keeps working.

## Related

- [ADR-0025: the hourly timeline is evidence beside the verdict](decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md)
- The verdict document table in the [README](../README.md#the-verdict-document)
