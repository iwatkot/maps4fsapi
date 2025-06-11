from typing import Literal

from pydantic import BaseModel


class LatLonPayload(BaseModel):
    lat: float
    lon: float


class DTMCodePayload(BaseModel):
    code: str


class MainSettingsPayload(BaseModel):
    game_code: Literal["fs22", "fs25"]
    dtm_code: str
    lat: float
    lon: float
    size: int
    rotation: int = 0
