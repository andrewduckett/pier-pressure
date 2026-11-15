## ADDED Requirements

### Requirement: Every pier has a FIRMS health sensor while the FIRMS key is set

While the service has a FIRMS key, the system SHALL publish one more health
sensor for every pier, "FIRMS health", keyed `firms`, beside its provider
health sensors. It SHALL follow every rule a provider's health sensor follows:
its discovery, state, attributes, startup reset and availability. With no key,
no pier SHALL have a FIRMS health sensor.

#### Scenario: A pier has FIRMS health while the key is set

- **WHEN** the configuration sets a FIRMS key and the system publishes health for a pier whose configured providers are `open_meteo` and `seven_timer`
- **THEN** it publishes health sensors named "Open-Meteo health", "7Timer! health" and "FIRMS health"
- **AND** the FIRMS health sensor's discovery topic and unique identity derive from the pier identifier and `firms`

#### Scenario: No key, no FIRMS health

- **WHEN** the configuration has no FIRMS key and the system publishes health for a pier
- **THEN** it publishes no health sensor named "FIRMS health"

#### Scenario: Startup resets FIRMS health before going online

- **WHEN** the process starts with a FIRMS key
- **THEN** it publishes FIRMS health for each pier with no history before it publishes its online availability

### Requirement: FIRMS health lists no variables and gives the latest detection time

The FIRMS health sensor's `variables` attribute SHALL be the empty list, since a
fire detection fills no variable. Its issue time SHALL be the latest time among
the fire detections from the last successful fetch, whether or not they count
for the verdict, or null when that fetch returned none. A fetch that returns
only a header row SHALL be a success.

#### Scenario: A fetch with detections gives the latest time

- **WHEN** the FIRMS fetch for a pier succeeds at `2026-11-14T21:30:05Z` with detections at `2026-11-13T05:54:00Z` and `2026-11-13T07:35:00Z`, and the system publishes
- **THEN** the FIRMS health sensor's state is `2026-11-14T21:30:05Z`
- **AND** its attributes give status `ok`, `variables` equal to `[]` and the issue time `2026-11-13T07:35:00Z`

#### Scenario: A fetch with no detections is a success with no issue time

- **WHEN** the FIRMS fetch for a pier at `2026-11-14T21:30:05Z` returns only a header row, and the system publishes
- **THEN** the FIRMS health sensor's state is `2026-11-14T21:30:05Z`
- **AND** its attributes give status `ok` and a null issue time

#### Scenario: A rejected key is a failed fetch

- **WHEN** the FIRMS fetch for a pier answers 400, and the system publishes
- **THEN** the FIRMS health sensor's attributes give status `failed` and the error `HTTPStatusError: 400 Bad Request`
