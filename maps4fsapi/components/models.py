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
    output_size: int | None = None
    # dtm_settings: mfs.DTMProviderSettings | None = None # ! Import to maps4fs from pygmdl.


class DEMSettingsPayload(MainSettingsPayload):
    """Payload model for DEM settings, extending MainSettingsPayload."""

    dem_settings: mfs.settings.DEMSettings = mfs.settings.DEMSettings()


class BackgroundSettingsPayload(DEMSettingsPayload):
    """Payload model for Background settings, extending DEMSettingsPayload."""

    background_settings: mfs.settings.BackgroundSettings = mfs.settings.BackgroundSettings()


class GRLESettingsPayload(MainSettingsPayload):
    """Payload model for GRLE settings, extending MainSettingsPayload."""

    grle_settings: mfs.settings.GRLESettings = mfs.settings.GRLESettings()


class I3DSettingsPayload(BackgroundSettingsPayload):
    """Payload model for I3D settings, extending BackgroundSettingsPayload."""

    i3d_settings: mfs.settings.I3DSettings = mfs.settings.I3DSettings()
    texture_settings: mfs.settings.TextureSettings = mfs.settings.TextureSettings()


class TextureSettingsPayload(MainSettingsPayload):
    """Payload model for Texture settings, extending MainSettingsPayload."""

    texture_settings: mfs.settings.TextureSettings = mfs.settings.TextureSettings()
    layer_names: list[str] = []


class SatelliteSettingsPayload(MainSettingsPayload):
    """Payload model for Satellite settings, extending MainSettingsPayload."""

    satellite_settings: mfs.settings.SatelliteSettings = mfs.settings.SatelliteSettings()


class MapGenerationPayload(MainSettingsPayload):
    """Payload model for Map generation settings, extending MainSettingsPayload."""

    dem_settings: mfs.settings.DEMSettings = mfs.settings.DEMSettings()
    background_settings: mfs.settings.BackgroundSettings = mfs.settings.BackgroundSettings()
    grle_settings: mfs.settings.GRLESettings = mfs.settings.GRLESettings()
    i3d_settings: mfs.settings.I3DSettings = mfs.settings.I3DSettings()
    texture_settings: mfs.settings.TextureSettings = mfs.settings.TextureSettings()
    satellite_settings: mfs.settings.SatelliteSettings = mfs.settings.SatelliteSettings()
