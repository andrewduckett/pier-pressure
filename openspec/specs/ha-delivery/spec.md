# ha-delivery Specification

## Purpose

The ha-delivery capability publishes a produced verdict document into Home Assistant over MQTT discovery, so per-pier entities appear on a dashboard with no hand-written YAML, stay current from a persistent process, and can be refreshed on demand and used as automation triggers for push notifications. Delivery consumes an already-produced verdict document; it never computes one.

Scenarios below are written against the system's observable MQTT output (topics, retain flags, and payloads), because that is what PierPressure controls and can assert mechanically. Home Assistant's own reaction to a valid discovery payload (actually rendering an entity) is confirmed by a documented manual acceptance check, not asserted as if PierPressure produced it.

## Requirements

### Requirement: Delivery consumes a produced verdict document

The delivery adapter SHALL take an already-produced verdict document as its input and publish it. It SHALL NOT compute, alter, or reinterpret the verdict, score, confidence, or reasons. This keeps the decision core independent of, and testable without, the delivery path.

#### Scenario: Adapter publishes the document it is given

- **WHEN** the adapter is given a verdict document and asked to publish
- **THEN** the values published to the state and attributes topics match the input document's verdict, score, confidence, and reasons exactly

#### Scenario: Verdict production does not depend on delivery

- **WHEN** the delivery path is unavailable
- **THEN** a verdict document can still be produced by the core

### Requirement: Per-pier entity auto-discovery

On publishing, the system SHALL publish MQTT discovery configuration messages for at least a verdict entity, a score entity, and a refresh control for the pier, so Home Assistant auto-creates them without manual configuration. Each discovery payload SHALL conform to Home Assistant's MQTT discovery schema for its entity type (sensor, sensor, button), SHALL be published to the discovery topic derived from the pier identifier, and SHALL be published with the retain flag set. Each entity's unique identity SHALL derive from the pier identifier, so re-publishing for the same pier updates the existing entities rather than creating duplicates.

#### Scenario: Discovery configuration is published on first publish

- **WHEN** the adapter publishes for a pier
- **THEN** it publishes a retained discovery configuration message for a verdict sensor, a score sensor, and a refresh button, each on the discovery topic derived from the pier identifier
- **AND** each discovery payload validates against Home Assistant's MQTT discovery schema for its entity type

#### Scenario: Re-publishing targets the same identities, not duplicates

- **WHEN** the adapter publishes twice for the same pier identifier
- **THEN** both publishes use the same discovery topics and the same entity unique identities
- **AND** no additional verdict, score, or refresh discovery identity is introduced

### Requirement: Verdict state and attributes are exposed

The verdict entity's state SHALL be published as the verdict value (`GO`, `MAYBE`, or `NO-GO`). The reasons, the score, the confidence (band and value), the night window, the pier identifier, and the generation timestamp SHALL be published as a JSON attributes payload so a dashboard card can display them. The score entity's state SHALL be the numeric score. The score entity's discovery configuration SHALL declare availability such that the score is available only when the process is online AND the score is non-null; when the score is null the score entity SHALL resolve to unavailable rather than a numeric value such as `0`.

#### Scenario: Verdict state and attributes are published from the document

- **WHEN** a verdict document with verdict `MAYBE`, a confidence, and a set of reasons is published
- **THEN** `MAYBE` is published to the verdict state topic
- **AND** a JSON attributes payload is published containing the reasons, score, confidence, night window, pier identifier, and generation timestamp

#### Scenario: Null score is published as null, with availability requiring non-null

- **WHEN** a verdict document whose score is null is published
- **THEN** the published attributes payload contains the `score` key explicitly set to null (present, not omitted)
- **AND** the score entity's published discovery payload declares an availability that requires a non-null score, so Home Assistant renders it unavailable rather than as `0`

### Requirement: Persistent operation with periodic republish

The delivery process SHALL run persistently rather than as a one-shot. It SHALL publish a verdict on startup and republish on a configurable interval so the displayed state does not silently go stale as the day and forecast move. Discovery configuration, state, attributes, and availability SHALL be published with the retain flag set, so a Home Assistant restart re-reads the last known verdict and availability without waiting for the next recompute. The process SHALL NOT depend on Home Assistant being available in order to stay current.

#### Scenario: State is published on startup

- **WHEN** the delivery process starts with a valid configuration
- **THEN** it publishes a verdict for the configured pier without any external trigger

#### Scenario: State refreshes on the configured interval

- **WHEN** the configured interval elapses with no external trigger
- **THEN** the pier's entities reflect a newer verdict document with a later generation timestamp

#### Scenario: Discovery, state, and availability are published retained

- **WHEN** the adapter publishes for a pier
- **THEN** the discovery configuration, state, attributes, and availability messages are all published with the retain flag set
- **AND** the availability message reflects the process being online

### Requirement: Availability reflects process liveness via last-will

The system SHALL register a retained Last-Will-and-Testament that marks the pier's entities unavailable if the process disconnects unexpectedly, and SHALL publish a retained online availability while running. Because both the online message and the last-will are retained, a subscriber connecting after the process has died SHALL read the offline state rather than a stale online state.

#### Scenario: A retained offline last-will is registered on connect

- **WHEN** the process connects to the broker
- **THEN** it registers a last-will message on the availability topic with an offline payload and the retain flag set

#### Scenario: A retained online availability is published while running

- **WHEN** the process is running and connected
- **THEN** an online availability message has been published to the availability topic with the retain flag set

### Requirement: On-demand refresh via a show-me-now control

The system SHALL publish the refresh control as an actionable Home Assistant entity (a button) and SHALL subscribe to a command topic that the control publishes to. When a message arrives on that command topic, the system SHALL recompute and republish immediately for the pier, producing a verdict document with a current generation timestamp. This gives the user a "show me now" action from the dashboard without waiting for the interval.

#### Scenario: A command on the refresh topic triggers an immediate republish

- **WHEN** a message is received on the pier's refresh command topic
- **THEN** the system recomputes and republishes for the pier
- **AND** the republished document carries a generation timestamp at or after the moment the command was received

#### Scenario: Refresh works independently of the interval

- **WHEN** a refresh command is received before the configured interval has elapsed
- **THEN** the entities update immediately rather than waiting for the next interval tick

#### Scenario: A refresh arriving during a recompute is not lost

- **WHEN** a refresh command arrives while a recompute is already in progress
- **THEN** a further recompute and republish occurs after the in-progress one completes

### Requirement: Verdict is usable as a notification trigger

The published verdict entity SHALL expose the verdict as a discrete, watchable state that distinguishes `NO-GO` from a not-`NO-GO` result, so a Home Assistant automation can trigger a push notification when tonight is worth setting up. Because state is republished on startup, on interval, and on demand, an automation firing at a chosen time reads the current verdict.

#### Scenario: The published verdict state is a discrete value distinguishing no-go

- **WHEN** a verdict document is published
- **THEN** the value published to the verdict state topic is exactly one of `GO`, `MAYBE`, or `NO-GO`
- **AND** the `NO-GO` value is distinct from `GO` and `MAYBE`, so a Home Assistant automation can branch on it by equality

### Requirement: Delivery failures are reported, not swallowed

When the MQTT broker is unreachable or a publish fails, the system SHALL report the failure rather than reporting success. A delivery failure SHALL NOT corrupt or partially publish an entity's state such that a stale value is presented as current without indication.

#### Scenario: Unreachable broker is reported as a failure

- **WHEN** the adapter attempts to publish and the broker cannot be reached
- **THEN** the run reports a delivery failure
- **AND** does not report the publish as successful
