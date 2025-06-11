import maps4fs as mfs
from fastapi import APIRouter, Depends, HTTPException

from maps4fsapi.components.models import DTMCodePayload, LatLonPayload
from maps4fsapi.config import api_key_auth, is_public

dtm_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])


@dtm_router.post("/get_list")
def get_dtm(payload: LatLonPayload):
    """Get a list of available DTM providers based on latitude and longitude.

    Arguments:
        payload (LatLonPayload): The payload containing latitude and longitude.
    Returns:
        list: A list of available DTM providers for the given coordinates.
    Payload example:
        {
            "lat": 47.3768866,
            "lon": 8.541694
        }
    Usage example:
        curl -X POST "http://localhost:8000/dtm/get_list" -H "Content-Type:application/json" -d '{"lat": 47.3768866, "lon": 8.541694}'
    """
    available_dtm = mfs.DTMProvider.get_valid_provider_descriptions((payload.lat, payload.lon))
    return available_dtm


@dtm_router.post("/is_valid")
def is_dtm_code_valid(payload: DTMCodePayload):
    """Check if the provided DTM code is valid.
    If correct, returns the description of the DTM provider. If not, raises a 404 error.

    Arguments:
        payload (DTMCodePayload): The payload containing the DTM code to check.
    Returns:
        dict: A dictionary indicating whether the DTM code is valid and providing the
            description of the provider.

    Payload example:
        {
            "code": "some_dtm_code"
        }
    Usage example:
        curl -X POST "http://localhost:8000/dtm/is_valid" -H "Content-Type:application/json" -d '{"code": "some_dtm_code"}'
    """
    dtm = mfs.DTMProvider.get_provider_by_code(payload.code)
    if not dtm:
        raise HTTPException(status_code=404, detail="DTM provider with this code not found")
    return {"valid": True, "provider": dtm.description()}
