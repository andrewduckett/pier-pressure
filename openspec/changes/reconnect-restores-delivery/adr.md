# ADR Review Manifest

- Status: completed
- Review date: 2026-10-08

## Review Summary

The author completed the ADR review for this change. The change introduces no
new durable architectural decision, so it creates no new ADR file. It amends
ADR-0018, which the change extends.

Each design decision extends an existing ADR or can be recovered from the code:

- **D1, D2, D6 and D7** extend ADR-0018's single retry mechanism to every reconnect,
  as that ADR expected ("work on reconnect behaviour extends the same callbacks").
- **D3** adds one item type to ADR-0012's work queue. The main thread stays the
  only publisher.
- **D4** chooses to replay the last retained messages rather than recompute. That
  is cheap to reverse, and the design records why.
- **D5** moves the login advice into the adapter. That is a local refactor.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0005, and ADR-0007 to ADR-0018 (all accepted). ADR-0006 is
  deprecated. No ADR has a Supersedes field.
- **ADR-0012** (threaded MQTT loop with a main-thread work queue) bears on D2 and
  D3. The network thread now subscribes again inside `on_connect`. Subscribing
  publishes nothing, so the rule that only the main thread publishes still holds.
  All recompute and replay still run on the main thread.
- **ADR-0018** (the MQTT library retries every connection) bears on D1, D2 and
  D5. Its Decision says the callbacks "only record the outcome for the main
  thread". After this change, a reconnect callback also subscribes again and logs
  a rejected login. D7 also keeps watching paho's thread after startup. None of
  these publish. This change adds a dated amendment to ADR-0018 that records all
  three, so the ADR matches the code.
- ADR-0015 (provider health beside the verdict, in memory) is unaffected. The
  replay republishes the health messages last sent, and keeps no new state in the
  verdict document.

## New Durable ADRs Created

- None. No major durable architectural decisions were introduced.

## ADRs Amended

- [ADR-0018: The MQTT library retries every connection to the broker](../../../docs/decisions/0018-mqtt-library-owns-broker-retries.md):
  an amendment for this change.
