# Home Assistant acceptance checklist

Use this checklist to prove a change against a real Home Assistant before you
merge it. It covers every entity PierPressure publishes today.

The test suite uses a fake MQTT client. It proves *what PierPressure publishes*,
but not *how Home Assistant reacts* to it. This checklist covers only what needs a
real Home Assistant.

When a change adds or changes an entity, update this checklist in the same pull
request.

## Before you start

You need:

- a Home Assistant install with the MQTT integration, connected to a broker;
- `mosquitto_sub` and `mosquitto_pub` on a machine that can reach that broker;
- a `config.yaml` with one pier. The examples below use a pier called `backyard`.

PierPressure reads its config only when it starts. After each config change below,
restart the container (`docker restart <container>`) or the `just run` process.

- [ ] `config.yaml` points at the real broker, and `PIERPRESSURE_MQTT_PASSWORD` is
      set in the environment.
- [ ] PierPressure is running from the image or branch under test (`docker run ...`
      or `just run`). Its first log line shows the version.

## 1. Entities and device

- [ ] **The entities appear under one device.** In Home Assistant, open
      *Settings → Devices & services → MQTT*. A device called
      **PierPressure backyard** exists. With the explainer off, it has exactly
      four entities:

      | Entity | Type | Entity id |
      |---|---|---|
      | Verdict | sensor | `sensor.pierpressure_backyard_verdict` |
      | Score | sensor | `sensor.pierpressure_backyard_score` |
      | Top target | sensor | `sensor.pierpressure_backyard_top_target` |
      | Refresh | button | `button.pierpressure_backyard_refresh` |

      There is no Narrative entity.

## 2. A normal night

Use your normal pier settings for this section.

- [ ] **Verdict.** The state is `GO`, `MAYBE`, or `NO-GO`. Its attributes include
      `pier`, `generated_at`, `verdict`, `score`, `confidence` (a `band` of `LOW`,
      `MEDIUM`, or `HIGH` and a `value` from 0 to 100), a non-empty `reasons` list,
      `targets`, `dark_window`, and `moon`.
- [ ] **Score.** When the verdict is `GO` or `MAYBE`, the state is a whole number
      from 0 to 100 and matches the Verdict's `score` attribute.
- [ ] **Top target.** The state is the name of the first target in the Verdict's
      `targets` list, or its catalogue id (for example `NGC0224`) when it has no
      common name. Its attributes hold `count`, `top` (that first target), and
      `targets` (the whole ranked list, in the same order as the Verdict's).

## 3. Refresh

- [ ] **The Refresh button republishes.** Note the Verdict's `generated_at`. Press
      **Refresh**. Within a few seconds, without waiting for the recompute
      interval, `generated_at` changes to a time at or after the press.

## 4. A gated NO-GO

A failed hard gate must show the score as unavailable, not as `0`. Force the wind
gate to fail: under the pier in `config.yaml`, set

```yaml
    max_gust: 0.1   # km/h; almost any forecast gust is over this
```

and restart PierPressure.

- [ ] **Verdict** shows `NO-GO`, and its `reasons` say
      `Wind gust over the 0.1 km/h limit during the dark window.`
- [ ] **Score** shows **unavailable**, not `0`.
- [ ] **Verdict, Top target, and Refresh** stay available.

If the verdict is not `NO-GO`, check the `reasons`: the forecast may have no wind
data for tonight. Try again later.

Remove `max_gust` (or restore your own value) and restart.

## 5. No rankable targets

When nothing can be ranked, Top target must show as unavailable, not as a blank or
placeholder value. Block the whole sky: under the pier in `config.yaml`, set

```yaml
    horizon:
      min_altitude: 90   # nothing rises above a 90-degree horizon
```

and restart PierPressure.

- [ ] **Top target** shows **unavailable**.
- [ ] **Verdict** has an empty `targets` attribute and stays available.

Restore your own `horizon` setting (or remove it) and restart.

## 6. Narrative (explainer on)

Turn on the explainer as described in [the explainer guide](../llm-explainer.md),
using a real API key, and restart PierPressure.

- [ ] **A Narrative entity appears** on the same device:
      `sensor.pierpressure_backyard_narrative`. The device now has five entities.
- [ ] **Narrative** shows `ready`. Its `narrative` attribute holds a paragraph of
      text, and its `available` attribute is `true`.
- [ ] **The prose matches the verdict.** Do the
      [manual acceptance check](../llm-explainer.md#manual-acceptance-check) from the
      explainer guide.

Now make the explainer fail. Change `api_key` to a variable that is not set, such
as `${UNSET_API_KEY}`, and restart.

- [ ] **Narrative** shows **unavailable**, not empty text or the earlier paragraph.
- [ ] **Verdict, Score, Top target, and Refresh** still update as normal.

## 7. Narrative (explainer off again)

Turn the explainer off (`enabled: false`, or remove the `explainer` block) and
restart.

- [ ] **No new narrative is published.** PierPressure leaves the retained
      Narrative entity in place, so it still exists in Home Assistant. Remove it
      with the step in
      [Removing the entity after disabling](../llm-explainer.md#removing-the-entity-after-disabling).
      The device goes back to four entities.

## 8. Last will

The commands below assume the default `base_topic` of `pierpressure`.

- [ ] **Stopping PierPressure marks every entity unavailable.** Stop the container
      (`docker stop <container>`). Within the broker's keepalive time, Verdict,
      Score, Top target, Refresh, and Narrative (if it exists) all show
      **unavailable**.
- [ ] **The offline status survives a Home Assistant restart.** Check the
      retained status:

      ```bash
      mosquitto_sub -h <broker> -u <user> -P <password> -t pierpressure/status -C 1
      ```

      It prints `offline`. Restart Home Assistant while PierPressure is still
      stopped. The entities stay **unavailable**.
- [ ] **Starting again restores them.** Start PierPressure. `pierpressure/status`
      is `online`, and every entity is available again.

## Result

- Date run:
- PierPressure version or branch:
- Home Assistant version and broker:
- Outcome (pass or fail, with notes):
