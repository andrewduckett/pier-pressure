# ADR Review Manifest

- Status: completed
- Review date: 2026-10-06

## Review Summary

ADR review completed for this change. A decision gets an ADR when a later change
could reverse it without knowing why, and the reversal would be costly.

One decision meets that bar: how the add-on chooses between the config file and
the Supervisor for its broker's connection settings. Merging the two sources
field by field looks simpler, but it would send one broker's credentials to
another. So it gets a new ADR.

The other design decisions do not meet the bar. The wait length, the retry
interval, the TLS refusal and the log wording are cheap to change and readable
from the code. Detecting an add-on by `SUPERVISOR_TOKEN` is cheap to change.
Splitting config loading so the edge does the lookup applies ADR-0001 and
ADR-0005; it makes no new decision.

## In-Force ADRs Reviewed

- ADR-0001: the core is Home Assistant-agnostic and emits one JSON verdict
  document. This change keeps all Supervisor access outside the core.
- ADR-0002: gates, then a banded score. Not affected.
- ADR-0003: target windows are clamped to astronomical night. Not affected.
- ADR-0004: astronomy is deterministic and offline. Not affected; the core does no
  network access.
- ADR-0005: all network access stays at the edge, and the core receives data,
  not an interface that fetches. This change follows it: the entry point asks
  the Supervisor, and passes the broker settings into the core as plain data.
- ADR-0007: canonical horizon representation. Not affected.
- ADR-0008: vendored OpenNGC catalogue. Not affected.
- ADR-0009: targets fill the document additively. Not affected.
- ADR-0010: ranking renormalises over known factors. Not affected.
- ADR-0011: the narrative is a separate entity. Not affected.
- ADR-0012: threaded loop with a work queue. Not affected; the lookup runs once,
  before the loop starts.
- ADR-0013: CalVer versions from git tags. Not affected.
- ADR-0014: the add-on lives in this repository and runs the released image. Still
  in force. The add-on still runs the same image; ADR-0017 records that the image
  now has one behaviour that runs only inside an add-on.
- ADR-0015: provider health sits beside the verdict, in memory. Not affected.
- ADR-0016: Python 3.14. Not affected.

ADR-0006 is deprecated and was not treated as in force.

## New Durable ADRs Created

- [ADR-0017: Inside an add-on, the broker comes from the config file or the Supervisor, never a mix](../../../docs/decisions/0017-addon-broker-from-supervisor-as-one-source.md)
