"""The MET Norway provider: layered cloud, wind and weather from Locationforecast (#220)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pierpressure.core.config import PierConfig
from pierpressure.core.providers import MET_NORWAY, ProviderSpec

from .provider import SourceForecast


@dataclass
class MetNorwayProvider:
    """Fetches MET Norway's complete Locationforecast for a pier."""

    spec: ClassVar[ProviderSpec] = MET_NORWAY

    def fetch(self, pier: PierConfig) -> SourceForecast:
        raise NotImplementedError
