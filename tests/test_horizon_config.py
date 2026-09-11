"""Tasks 4.x: PierConfig.horizon — mutual exclusivity, isolation, path resolution."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pierpressure.core.config import ConfigError, PierConfig, load_config, validate_piers

_NINA_FIXTURE = Path(__file__).parent / "fixtures" / "nina_horizon.hrz"


def _write(tmp_path: Path, text: str, name: str = "config.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


_BASE_CONFIG = """
mqtt:
  host: 192.168.1.10
recompute:
  interval_seconds: 900
piers:
{piers}
"""


def _config_with_pier(pier_block: str) -> str:
    return _BASE_CONFIG.format(piers=pier_block)


# --------------------------------------------------------------------------- #
# 4.1 / 4.2 — the horizon block, its sources, and per-pier isolation
# --------------------------------------------------------------------------- #


def test_absent_horizon_resolves_to_flat_open_sky(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: backyard
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.piers[0].horizon_mask.alt_at(123) == 0.0


def test_inline_points_horizon_resolves_and_queries(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: backyard
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      points:
        - [90, 30]
        - [0, 10]
"""
    )
    config = load_config(_write(tmp_path, text))
    assert config.piers[0].horizon_mask.alt_at(90) == 30.0


def test_min_altitude_floor_resolves_to_a_flat_horizon(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: backyard
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      min_altitude: 25
"""
    )
    config = load_config(_write(tmp_path, text))
    for az in (0, 90, 200):
        assert config.piers[0].horizon_mask.alt_at(az) == 25.0


def test_two_horizon_sources_invalidate_only_their_own_pier(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: good
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
  - id: two_sources
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      min_altitude: 25
      points:
        - [0, 10]
"""
    )
    config = load_config(_write(tmp_path, text))
    assert [pier.id for pier in config.piers] == ["good"]


def test_out_of_range_inline_point_invalidates_only_its_pier(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: good
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
  - id: bad_horizon
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      points:
        - [10, 200]
"""
    )
    config = load_config(_write(tmp_path, text))
    assert [pier.id for pier in config.piers] == ["good"]


def test_unsupported_format_invalidates_its_pier(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: bad_horizon
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      file: horizon.dat
      format: stellarium
"""
    )
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_missing_horizon_file_invalidates_its_pier(tmp_path: Path) -> None:
    text = _config_with_pier(
        """  - id: bad_horizon
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      file: nonexistent.hrz
      format: nina
"""
    )
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_validate_piers_without_context_still_isolates_entries() -> None:
    # Backwards-compatible call (no base_dir): non-file horizons still validate.
    raw = [
        {"id": "good", "latitude": 51.5, "longitude": -0.12, "elevation_m": 30},
        {
            "id": "bad",
            "latitude": 51.5,
            "longitude": -0.12,
            "elevation_m": 30,
            "horizon": {"min_altitude": 25, "points": [[0, 10]]},
        },
    ]
    valid = validate_piers(raw)
    assert [pier.id for pier in valid] == ["good"]


def test_pier_constructed_without_horizon_defaults_to_open_sky() -> None:
    pier = PierConfig(id="p", latitude=51.5, longitude=-0.12, elevation_m=30.0)
    assert pier.horizon_mask.alt_at(180) == 0.0


# --------------------------------------------------------------------------- #
# 4.3 — a relative file path resolves against the config file's directory
# --------------------------------------------------------------------------- #


def test_relative_horizon_file_resolves_against_config_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "site"
    config_dir.mkdir()
    (config_dir / "horizon.hrz").write_text(
        _NINA_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    text = _config_with_pier(
        """  - id: backyard
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      file: horizon.hrz
      format: nina
"""
    )
    config_path = _write(config_dir, text)

    # Launch from an unrelated working directory: the file must still be found
    # relative to the config file's own directory, not the process cwd.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    config = load_config(config_path)
    assert config.piers[0].id == "backyard"
    assert config.piers[0].horizon_mask.alt_at(135) == 30.0


def test_relative_horizon_file_is_not_found_via_process_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Placing the file only in the cwd (not beside the config) must NOT satisfy the
    # reference — resolution ignores the process working directory.
    config_dir = tmp_path / "site"
    config_dir.mkdir()
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    (cwd / "horizon.hrz").write_text(_NINA_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    text = _config_with_pier(
        """  - id: backyard
    latitude: 51.5
    longitude: -0.12
    elevation_m: 30
    horizon:
      file: horizon.hrz
      format: nina
"""
    )
    config_path = _write(config_dir, text)
    monkeypatch.chdir(cwd)
    assert os.path.exists("horizon.hrz")

    with pytest.raises(ConfigError):
        load_config(config_path)
