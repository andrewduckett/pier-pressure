## Why

Every condition in the timeline now reaches Home Assistant as a sensor (#133, #134), but nothing shows them together. To decide on a night, Andrew still opens the Astrospheric app. A dashboard that anyone can paste in, showing the night strip, makes Home Assistant the one place to look.

## What Changes

- A new docs page, `docs/night-dashboard.md` (D10), with one complete dashboard in YAML. It uses Home Assistant core cards plus plotly-graph-card from HACS, and no JavaScript of its own.
  - A tonight card: verdict, score, confidence, dark window and reasons (D12).
  - The night strip: a plotly-graph-card heatmap with one row per timeline sensor, in the packet's order. A null hour is a gap, and the shading follows the reference rendering (D8). The axis spans tonight with margins, read from `dark_window`, with a fallback when there is no dark window (D2). It uses Home Assistant's local time (D9).
  - On the same axis: dusk and dawn lines, a "Moon up" lane (D3), one lane per ranked target (D4), and a "now" line at the browser's current time (D7).
  - A moon card, a target table and health chips for the two weather sources (D12).
  - Install steps for plotly-graph-card, with the pier id `backyard` to replace (D11).
- A screenshot of the dashboard in `docs/images/`, taken from the check below (D6).
- A check of the YAML against a real Home Assistant, run in a throwaway Docker setup with mosquitto and PierPressure (D1).
- A pytest test that reads the YAML from the docs page and fails when it reads an entity id or attribute the MQTT adapter does not publish (D5).
- Links to the new page from the README's entity section and from `docs/night-timeline.md` (D10).

The published entities, topics and verdict document do not change.

## Capabilities

### New Capabilities

- `night-dashboard`: the documented Home Assistant dashboard for a pier. It covers what the strip and its cards show, where each value comes from among the published entities, and the guard that keeps the YAML in step with the MQTT adapter.

### Modified Capabilities

None. `ha-delivery` is read for context only: the dashboard consumes the entities it publishes and changes none of them.

## Impact

- **Docs:** new `docs/night-dashboard.md` and `docs/images/` (the first image on `main`); links added to `README.md` and `docs/night-timeline.md`. The apexcharts-card example in `docs/night-timeline.md` stays as it is.
- **Tests:** a new docs guard test. It reads names from `pierpressure/delivery/mqtt.py` but changes nothing there.
- **Dependencies:** none for the package. Readers install plotly-graph-card through HACS. The Docker check uses the official Home Assistant image and the existing `compose.yaml` services, and may add a dev-only compose profile or script.
- **Code:** no change to `pierpressure/core/` or the delivery adapter.
