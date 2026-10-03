"""PierPressure: deterministic per-pier night verdict, delivered to Home Assistant.

The package is split into a pure decision ``core`` (no Home Assistant or MQTT
imports) and a ``delivery`` adapter. ``core`` MUST NOT import from ``delivery``;
see design D1. That boundary is what makes the verdict document producible and
testable off Home Assistant.
"""

import importlib.metadata

# The git tag is the only source of the version (ADR-0013); the build stamps it
# into the package metadata.
__version__ = importlib.metadata.version("pierpressure")
