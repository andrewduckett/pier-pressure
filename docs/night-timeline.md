# The night timeline: chart the hours in Home Assistant

The verdict tells you whether tonight is worth setting up for. The timeline
shows you why, hour by hour. This page explains what the timeline holds, how the
Cloud cover sensor delivers it to Home Assistant, and how to chart it.

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

## The Cloud cover sensor

Each pier's device has a **Cloud cover** sensor, entity id
`sensor.pierpressure_<pier>_cloud_cover`. For a pier called `backyard`, that is
`sensor.pierpressure_backyard_cloud_cover`.

- **State:** the cloud cover, in percent, for the current hour.
- **`forecast` attribute:** one point per timeline hour, in order. Each point is
  `{ "datetime": "<time>", "value": <cloud_cover> }`. An hour with no value stays
  in the list with `value: null`, so the points line up with the timeline hour
  for hour.
- **`hour` attribute:** the start of the hour the state belongs to, or `null`.

When the current hour has no cloud cover value, or the timeline is empty, the
state is `unknown`. It never shows `0` or an older value instead. The sensor stays
available, so `forecast` is still there for a chart. It is unavailable only when
PierPressure is offline, and then Home Assistant hides all its attributes.

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
sensor instead, starting with Cloud cover.

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
forecast is rarely useful. To stop recording the sensor, add it to the recorder's
exclusions in `configuration.yaml`:

```yaml
recorder:
  exclude:
    entities:
      - sensor.pierpressure_backyard_cloud_cover
```

The card above reads the live attributes, so it keeps working.

## Related

- [ADR-0025: the hourly timeline is evidence beside the verdict](decisions/0025-hourly-timeline-is-evidence-beside-the-verdict.md)
- The verdict document table in the [README](../README.md#the-verdict-document)
