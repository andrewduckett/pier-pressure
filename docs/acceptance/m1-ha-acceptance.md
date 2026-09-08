# M1 — Manual Home Assistant Acceptance Checklist

This is the end-to-end proof the walking skeleton exists (design D11). A fake
MQTT client proves *what PierPressure publishes*; it cannot prove *how Home
Assistant reacts*. This checklist covers exactly the parts that genuinely require
Home Assistant. Run it once against the real HAOS install + broker.

## Setup

- [ ] `config.yaml` points at the real broker; `PIERPRESSURE_MQTT_PASSWORD` is
      set in the environment.
- [ ] The container is running: `docker run ... pierpressure` (or `just run`).

## Checks

- [ ] **Entities appear under one device.** In Home Assistant →
      *Settings → Devices & Services → MQTT*, a device **PierPressure `<pier>`**
      exists and groups exactly three entities: a **Verdict** sensor, a **Score**
      sensor, and a **Refresh** button.
- [ ] **Verdict, score, and confidence render.** The Verdict sensor shows
      `MAYBE` (the M1 stub); its attributes show the reasons, `confidence`
      (`{band: LOW, value: 0}`), night window, pier id, and generation timestamp;
      the Score sensor shows `50`.
- [ ] **The refresh button republishes.** Pressing the **Refresh** button updates
      the entities and the generation timestamp advances to (at or after) the
      moment of the press, without waiting for the interval.
- [ ] **A gated NO-GO shows the score as unavailable.** Publish (or otherwise
      produce) a verdict document with `verdict: NO-GO` and `score: null`; the
      Score sensor becomes **unavailable** rather than showing `0`, while the
      Verdict sensor shows `NO-GO`.
- [ ] **Killing the container flips entities to unavailable.** Stop the container
      (`docker stop ...`); within the broker's keepalive the Verdict, Score, and
      Refresh entities go **unavailable** (the retained Last-Will `offline`), and
      a Home Assistant restarted while the container is down still reads `offline`
      rather than a stale `online`.

## Result

- Date run:
- HA version / broker:
- Outcome (pass/fail + notes):
