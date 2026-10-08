# ADR Review Manifest

- Status: completed
- Review date: 2026-10-07

## Review Summary

ADR review completed for this change. Design decision D1, letting paho retry
every broker connection, is a real fork: an engineer could replace it with a
hand-written retry loop without knowing why. That decision gets a new ADR. D2 to
D6 are recoverable from the code and do not need one.

## In-Force ADRs Reviewed

- ADR-0001 to ADR-0005, and ADR-0007 to ADR-0017 (all accepted). ADR-0006 is
  deprecated. No ADR has a Supersedes field.
- ADR-0012 (threaded MQTT loop with a main-thread work queue) bears on this change
  directly. The new connection callbacks only record an outcome, and the main
  thread still does all publishing.
- ADR-0017 (the add-on's broker comes from the file or the Supervisor) is
  unaffected. It decides which broker to use. This change decides how to reach it.

## New Durable ADRs Created

- [ADR-0018: The MQTT library owns every broker connection retry](../../../docs/decisions/0018-mqtt-library-owns-broker-retries.md)
