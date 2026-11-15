## ADDED Requirements

### Requirement: A pier that names a METAR station has a METAR health sensor

For each pier that names a METAR station, the system SHALL publish one more
health sensor, "METAR health", keyed `metar`, beside its provider health
sensors. It SHALL follow every rule a provider's health sensor follows: its
discovery, state, attributes, startup reset and availability. A pier with no
station SHALL have no METAR health sensor.

#### Scenario: A pier with a station has METAR health

- **WHEN** the system publishes health for a pier whose `metar_station` is `KBOS` and whose configured providers are `open_meteo` and `seven_timer`
- **THEN** it publishes health sensors named "Open-Meteo health", "7Timer! health" and "METAR health"
- **AND** the METAR health sensor's discovery topic and unique identity derive from the pier identifier and `metar`

#### Scenario: A pier with no station has no METAR health

- **WHEN** the system publishes health for a pier with no `metar_station`
- **THEN** it publishes no health sensor named "METAR health"

#### Scenario: Startup resets METAR health before going online

- **WHEN** the process starts with a pier whose `metar_station` is `KBOS`
- **THEN** it publishes METAR health for that pier with no history before it publishes its online availability

### Requirement: METAR health lists no variables and gives the observation time

The METAR health sensor's `variables` attribute SHALL be the empty list, since an
observation fills no variable. Its issue time SHALL be the observation time of
the report from the last successful fetch. A fetch that returns a report SHALL
be a success even when the report is too old for the verdict to use.

#### Scenario: A successful METAR fetch gives the observation time

- **WHEN** the METAR fetch for a pier succeeds at `2026-11-14T21:30:05Z` with a report measured at `2026-11-14T20:54:00Z`, and the system publishes
- **THEN** the METAR health sensor's state is `2026-11-14T21:30:05Z`
- **AND** its attributes give status `ok`, `variables` equal to `[]` and the issue time `2026-11-14T20:54:00Z`

#### Scenario: An old report is still a successful fetch

- **WHEN** the METAR fetch for a pier at `2026-11-14T23:30:00Z` returns a report measured at `2026-11-14T20:54:00Z`, and the system publishes
- **THEN** the METAR health sensor's attributes give status `ok` and the issue time `2026-11-14T20:54:00Z`
- **AND** the verdict's `observation` is null

#### Scenario: An empty response is a failed fetch

- **WHEN** the METAR fetch for a pier returns no report, and the system publishes
- **THEN** the METAR health sensor's attributes give status `failed` and the error `no report returned`
