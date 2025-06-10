from pydantic import BaseModel


class LatLonPayload(BaseModel):
    lat: float
    lon: float


class DTMCodePayload(BaseModel):
    code: str
