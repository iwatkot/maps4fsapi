"""Maps4FS API Models used to validate and structure data for various endpoints."""

from typing import Literal

import maps4fs as mfs
from pydantic import BaseModel


class LatLonPayload(BaseModel):
    """Payload model for latitude and longitude coordinates."""

    lat: float
    lon: float


class DTMCodePayload(BaseModel):
    """Payload model for DTM code."""

    code: str


class TaskIdPayload(BaseModel):
    """Payload model for task ID."""

    task_id: str


class MainSettingsPayload(BaseModel):
    """Main settings payload for generating maps with Maps4FS."""

    game_code: Literal["fs22", "fs25"]
    dtm_code: str
    lat: float
    lon: float
    size: int
    rotation: int = 0


class DEMSettingsPayload(MainSettingsPayload):
    """Payload model for DEM settings, extending MainSettingsPayload."""

    dem_settings: mfs.settings.DEMSettings | None = mfs.settings.DEMSettings()
