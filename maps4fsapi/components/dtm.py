"""DTM (Digital Terrain Model) API endpoints for Maps4FS."""

import maps4fs as mfs
from fastapi import APIRouter, HTTPException

from maps4fsapi.components.models import DTMCodePayload, LatLonPayload
from maps4fsapi.limits import dependencies

dtm_router = APIRouter(dependencies=dependencies)


@dtm_router.post("/get_list")
def get_dtm_list(payload: LatLonPayload):
    """Get a list of available DTM providers based on latitude and longitude.

    Arguments:
        payload (LatLonPayload): The payload containing latitude and longitude.
    Returns:
        list: A list of available DTM providers for the given coordinates.
    """
    available_dtm = mfs.DTMProvider.get_valid_provider_descriptions((payload.lat, payload.lon))
    return available_dtm


@dtm_router.post("/get_info")
def get_dtm_info(payload: DTMCodePayload):
    """Get information about a DTM provider based on its code.
    If the code is correct, returns the description of the DTM provider. If not, raises a 404 error.

    Arguments:
        payload (DTMCodePayload): The payload containing the DTM code to check.
    Returns:
        dict: A dictionary indicating whether the DTM code is valid and providing the
            description of the provider.
    """
    dtm = mfs.DTMProvider.get_provider_by_code(payload.code)
    if not dtm:
        raise HTTPException(status_code=404, detail="DTM provider with this code not found")
    return {"valid": True, "provider": dtm.description()}
