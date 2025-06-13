from typing import Literal

import maps4fs as mfs
from pydantic import BaseModel


class LatLonPayload(BaseModel):
    lat: float
    lon: float


class DTMCodePayload(BaseModel):
    code: str


class TaskIdPayload(BaseModel):
    task_id: str


class MainSettingsPayload(BaseModel):
    game_code: Literal["fs22", "fs25"]
    dtm_code: str
    lat: float
    lon: float
    size: int
    rotation: int = 0
    dem_settings: mfs.settings.DEMSettings | None = mfs.settings.DEMSettings()
