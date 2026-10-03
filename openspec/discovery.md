# Discovery: PierPressure

> The living map behind the backlog: who the product serves and the journeys it supports.
> Product intent (scope, goals, non-goals) lives in `openspec/prd.md`.
> Stories are GitHub issues; each discovery run's scope and decisions live in its parent issue.

## Personas

### People who use PierPressure

#### Andrew — the home-pier astrophotographer

- **Who**: an amateur astrophotographer who runs long imaging sessions from a fixed
  pier at home, and whose house already runs on Home Assistant.
- **Goal**: know early in the evening whether tonight is worth a full imaging setup,
  and what to point at from this pier with this rig.
- **Pain today**: answering means checking several weather sites, a moon calendar, a
  planetarium app, and his own memory of which trees block which part of the sky.
  Good nights get missed, and poor nights waste an hour of setup.
- **Success looks like**: one glance at the dashboard, or one notification, answers
  both questions, and he trusts the answer enough to act on it.

#### A fellow Home Assistant astronomer — the adopter

- **Who**: another amateur astronomer, imaging or observing, who already runs Home
  Assistant and an MQTT broker and uses one or more fixed sites.
- **Goal**: get the same go/no-go answer and target list for their own site and gear,
  without reading the source.
- **Pain today**: the same scattered checking Andrew does. Every existing tool also
  expects them to open an app, instead of bringing the answer to them.
- **Success looks like**: they install it, describe their site, horizon, and rig in
  one file, and see a verdict in Home Assistant the same evening.

> **Implication**: Andrew and the adopter walk one journey. The adopter has extra
> stages at the start (find the project, get it running without cloning the repo).
> Build one setup path that works for a stranger. Don't split it into an author path
> and a user path.

### People who build PierPressure

#### Andrew — the maintainer

- **Who**: the same person, maintaining the code.
- **Goal**: add science and fix problems without breaking the frozen verdict contract
  or the deterministic core, and keep pinned data (ephemeris, star catalogue) and
  weather providers current.
- **Pain today**: astronomy code goes wrong quietly. A wrong twilight time or a
  changed weather API can look plausible for weeks.
- **Success looks like**: every change ships as a small, tested PR. A provider outage
  or a data update shows up as a failing check or a lower confidence, never as a
  confidently wrong verdict.

## Journey Map

## Backlog

Stories are GitHub issues: <https://github.com/andrewduckett/pier-pressure/issues>.
