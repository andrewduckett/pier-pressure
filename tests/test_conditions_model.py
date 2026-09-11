"""Tasks 2.1-2.2: the immutable per-source conditions group model in the pure core."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from pierpressure.core.conditions import (
    BaseGroup,
    BaseHour,
    Conditions,
    GroupMeta,
    SecondaryGroup,
    SecondaryHour,
)

# --------------------------------------------------------------------------- #
# 2.1 / 2.2 the per-source group model (design D1, D2)
# --------------------------------------------------------------------------- #


def _t(h: int) -> datetime:
    return datetime(2026, 9, 8, h, 0, tzinfo=UTC)


def _meta(issued: int = 12) -> GroupMeta:
    return GroupMeta(source="base", issued_at=_t(issued))


def test_group_meta_carries_source_and_issue_time() -> None:
    meta = GroupMeta(source="secondary", issued_at=_t(11))
    assert meta.source == "secondary"
    assert meta.issued_at == _t(11)


def test_group_meta_issue_time_defaults_to_none() -> None:
    assert GroupMeta(source="base").issued_at is None


def test_base_group_lookup_hits_and_misses_by_hour() -> None:
    h21 = BaseHour(time=_t(21), cloud_cover=10.0, wind_gust=15.0)
    group = BaseGroup(meta=_meta(), hours=(h21, BaseHour(time=_t(22), cloud_cover=20.0)))
    assert group.at(_t(21)) is h21
    assert group.at(_t(23)) is None


def test_secondary_group_lookup_hits_and_misses_by_hour() -> None:
    h21 = SecondaryHour(time=_t(21), seeing=0.8, transparency=0.7)
    group = SecondaryGroup(meta=GroupMeta(source="secondary"), hours=(h21,))
    assert group.at(_t(21)) is h21
    assert group.at(_t(22)) is None


def test_base_group_of_returns_none_when_the_source_returned_no_rows() -> None:
    # No rows -> absent group (mirrors today's empty readings -> no issue time).
    assert BaseGroup.of(_meta(), ()) is None


def test_secondary_group_of_returns_none_when_the_source_returned_no_rows() -> None:
    assert SecondaryGroup.of(GroupMeta(source="secondary"), ()) is None


def test_base_group_of_present_when_rows_have_all_none_fields() -> None:
    # Rows but every field empty -> a present group, not None (design D1, D2).
    group = BaseGroup.of(_meta(), (BaseHour(time=_t(21)),))
    assert group is not None
    hour = group.at(_t(21))
    assert hour is not None
    assert hour.cloud_cover is None and hour.wind_gust is None


def test_secondary_group_of_present_when_rows_have_all_none_fields() -> None:
    group = SecondaryGroup.of(GroupMeta(source="secondary"), (SecondaryHour(time=_t(21)),))
    assert group is not None
    assert group.at(_t(21)) is not None


def test_base_hour_stamps_each_field_independently() -> None:
    hour = BaseHour(time=_t(21), cloud_cover=40.0)
    assert hour.cloud_cover == 40.0
    assert hour.wind_gust is None  # availability is per field


def test_base_hour_carries_the_cloud_component_split() -> None:
    hour = BaseHour(time=_t(21), cloud_cover=40.0, cloud_low=10.0, cloud_mid=20.0, cloud_high=30.0)
    assert (hour.cloud_low, hour.cloud_mid, hour.cloud_high) == (10.0, 20.0, 30.0)


def test_base_hour_cloud_components_default_to_none() -> None:
    hour = BaseHour(time=_t(21), cloud_cover=40.0)
    assert hour.cloud_low is None
    assert hour.cloud_mid is None
    assert hour.cloud_high is None


def test_base_hour_cloud_components_are_independently_optional() -> None:
    # Only the high component reported: low and mid stay absent, total stays usable.
    hour = BaseHour(time=_t(21), cloud_cover=40.0, cloud_high=30.0)
    assert hour.cloud_high == 30.0
    assert hour.cloud_low is None
    assert hour.cloud_mid is None
    assert hour.cloud_cover == 40.0


def test_conditions_none_none_is_the_canonical_empty_value() -> None:
    empty = Conditions(None, None)
    assert empty.base is None
    assert empty.secondary is None
    # The defaults give the same empty value.
    assert Conditions() == empty


def test_conditions_holds_both_groups() -> None:
    base = BaseGroup.of(_meta(), (BaseHour(time=_t(21), cloud_cover=10.0),))
    secondary = SecondaryGroup.of(
        GroupMeta(source="secondary", issued_at=_t(11)),
        (SecondaryHour(time=_t(21), seeing=0.8),),
    )
    conditions = Conditions(base=base, secondary=secondary)
    assert conditions.base is base
    assert conditions.secondary is secondary
    assert conditions.base is not None and conditions.base.meta.issued_at == _t(12)
    assert conditions.secondary is not None and conditions.secondary.meta.issued_at == _t(11)


def test_base_hour_is_immutable() -> None:
    hour = BaseHour(time=_t(21), cloud_cover=10.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        hour.cloud_cover = 90.0  # type: ignore[misc]


def test_conditions_is_immutable() -> None:
    conditions = Conditions(None, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        conditions.base = BaseGroup.of(_meta(), (BaseHour(time=_t(21)),))  # type: ignore[misc]
