"""The conditions input to the core — one self-stamped group per source (design D1, D2).

The provider layer (outside the core) builds this immutable value from external
forecasts; the core only reads it. Keeping the seam a *plain data value* is what
keeps ``produce_verdict`` a pure, deterministic function: a data value cannot
fetch anything, so no I/O can creep back across the boundary and the offline
guarantee stays a hard wall rather than "deterministic if mocked correctly".

Shape (design D1): the conditions input is modelled as one self-stamped group per
source rather than a flat hourly grid with side-channel issue times. Each source
is the unit that fetches, fails, caches, and stamps an issue time, so the source
is the honest grouping boundary. "Base" and "secondary" name the source *role* —
the load-bearing cloud/wind spine versus the optional seeing/transparency polish —
never a vendor, so the core still never learns a source's scale or resolution.

Two levels of absence, both stamped per-source (design D1, D2):

- **A whole group is present iff its source returned rows.** ``Conditions(None,
  None)`` is the canonical empty value; a source that contributed nothing yields a
  ``None`` group, and per-source freshness travels on each present group's meta.
- **Each field within a present group is independently present-or-absent** — a
  value is absent when it is ``None`` — so a partial group is an ordinary, valid
  value rather than an error.

Field conventions the core relies on:

- ``cloud_cover`` — percent, 0 (clear) .. 100 (overcast). The clarity curve that
  turns this into usable-sky weight is a scoring policy and lives in the core.
- ``wind_gust`` — the forecast gust in the same unit as ``PierConfig.max_gust``
  (km/h), compared directly against that limit.
- ``seeing`` and ``transparency`` — normalized quality in ``[0, 1]`` where 1 is
  best. The provider layer maps each source's native scale onto this range so
  the core never learns a source or a resolution existed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class GroupMeta:
    """Provenance for one source's group: which source, and when it issued the data.

    ``issued_at`` is aware UTC and ``None`` only when unknown; a present group whose
    source returned rows carries the source's own issue time, so per-source
    staleness travels with the data instead of in a parallel side-channel.
    """

    source: str
    issued_at: datetime | None = None


@dataclass(frozen=True)
class BaseHour:
    """The base source's readings for one clock-hour slot beginning at ``time``.

    ``time`` is the aware-UTC top of hour. ``cloud_cover`` and ``wind_gust`` are
    each independently optional: ``None`` means that field is unavailable for this
    hour, the per-field availability stamp the verdict degrades against.
    """

    time: datetime
    cloud_cover: float | None = None
    wind_gust: float | None = None


@dataclass(frozen=True)
class SecondaryHour:
    """The secondary source's readings for one clock-hour slot beginning at ``time``.

    ``seeing`` and ``transparency`` are normalized quality in ``[0, 1]`` (1 best),
    each independently optional. Values are hourly-held from the source's coarser
    cadence in the provider layer (design D3), so this grid aligns hour-for-hour
    with the base group.
    """

    time: datetime
    seeing: float | None = None
    transparency: float | None = None


@dataclass(frozen=True)
class BaseGroup:
    """The base source's hourly cloud/wind readings, self-stamped with its meta.

    ``hours`` are kept uniquely keyed by top-of-hour; ``at`` resolves a slot in
    O(1) via a lookup built once, matching the flat grid's ``_by_time`` (design D6).
    A ``BaseGroup`` exists only when its source returned rows — build one through
    :meth:`of`, which returns ``None`` for an empty source (design D1).
    """

    meta: GroupMeta
    hours: tuple[BaseHour, ...] = ()
    _by_time: dict[datetime, BaseHour] = field(
        default_factory=dict, compare=False, repr=False, init=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_by_time", {hour.time: hour for hour in self.hours})

    def at(self, time: datetime) -> BaseHour | None:
        """The hour slot beginning at ``time``, or ``None`` if the group omits it."""
        return self._by_time.get(time)

    @classmethod
    def of(cls, meta: GroupMeta, hours: tuple[BaseHour, ...]) -> BaseGroup | None:
        """The group for a source that returned ``hours``, or ``None`` if it returned none.

        A source that returned rows but left every field empty still yields a
        present group (its hours carry ``None`` fields); only a source that
        contributed no rows at all yields ``None`` (design D1, D2).
        """
        return cls(meta=meta, hours=hours) if hours else None


@dataclass(frozen=True)
class SecondaryGroup:
    """The secondary source's hourly seeing/transparency readings, self-stamped.

    Uniform with :class:`BaseGroup` (design D1): same O(1) ``at`` lookup and the
    same present-iff-rows construction via :meth:`of`.
    """

    meta: GroupMeta
    hours: tuple[SecondaryHour, ...] = ()
    _by_time: dict[datetime, SecondaryHour] = field(
        default_factory=dict, compare=False, repr=False, init=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_by_time", {hour.time: hour for hour in self.hours})

    def at(self, time: datetime) -> SecondaryHour | None:
        """The hour slot beginning at ``time``, or ``None`` if the group omits it."""
        return self._by_time.get(time)

    @classmethod
    def of(cls, meta: GroupMeta, hours: tuple[SecondaryHour, ...]) -> SecondaryGroup | None:
        """The group for a source that returned ``hours``, or ``None`` if it returned none."""
        return cls(meta=meta, hours=hours) if hours else None


@dataclass(frozen=True)
class Conditions:
    """The observing-conditions input to the core: one optional group per source.

    A group is ``None`` exactly when its source contributed no rows (design D1), so
    ``Conditions(None, None)`` is the canonical empty value — the astronomy-only
    input the service's fallback supplies. The core reads each group through its
    ``at`` lookup, guarding the ``None`` group first, so an absent source degrades
    the verdict rather than raising (design D6).
    """

    base: BaseGroup | None = None
    secondary: SecondaryGroup | None = None
