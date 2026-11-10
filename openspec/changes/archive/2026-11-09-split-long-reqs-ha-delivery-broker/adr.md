# ADR Review Manifest

- Status: completed
- Review date: 2026-11-09

## Review Summary

ADR review completed for this change. It changes the text of one spec only. No record in force covers how specs are written, and none constrains this change.

## In-Force ADRs Reviewed

- [ADR-0001](../../../docs/decisions/0001-core-ha-agnostic-json-verdict-contract.md) to [ADR-0035](../../../docs/decisions/0035-the-pierpressure-card-is-the-only-documented-dashboard.md) in `docs/decisions/`, except the superseded ADR-0006 and ADR-0026. None is about spec structure. Four set rules that the split requirements specify, and the split keeps each one:
  - [ADR-0012](../../../docs/decisions/0012-threaded-loop-work-queue.md): a threaded MQTT loop with a main-thread work queue ("The process publishes a verdict at startup and on an interval", "A failed publish does not stop the process").
  - [ADR-0018](../../../docs/decisions/0018-mqtt-library-owns-broker-retries.md): the MQTT library retries every connection, and a rejected login stops the process at startup ("The process keeps trying to connect to the broker at startup", "The pauses between connection attempts grow from 1 to 120 seconds", "A rejected login at startup stops the process", "The process keeps trying to reconnect while it runs").
  - [ADR-0019](../../../docs/decisions/0019-replay-repairs-outage-publishes.md): the replay after a reconnect repairs what an outage missed, not the MQTT client's queue ("After a reconnect, the process subscribes again and republishes its last state", "The MQTT client may send a message again after a reconnect", "While disconnected, the process holds its publishes for the replay").
  - [ADR-0022](../../../docs/decisions/0022-core-is-the-only-place-that-validates-settings.md): the core alone validates settings ("An error about the mqtt block shows none of its values", "An error about the mqtt block says what is wrong").

## New Durable ADRs Created

- None - no major durable architectural decisions were introduced. The design's decisions are about spec text. New headings are forced by OpenSpec (epic #230 decision 5), the added scenario restates a rule its requirement keeps, and the one new SHALL NOT restates what its scenario already asserts, so none is a costly fork.
