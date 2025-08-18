"""DTM (Digital Terrain Model) API endpoints for Maps4FS."""

import maps4fs as mfs
from fastapi import APIRouter, HTTPException, Request

from maps4fsapi.components.models import (
    DEMSettingsPayload,
    DTMCodePayload,
    LatLonPayload,
)
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, get_session_name_from_payload, task_generation

dtm_router = APIRouter(dependencies=dependencies)


@dtm_router.post("/list")
def dtm_list(payload: LatLonPayload):
    """Get a list of available DTM providers based on latitude and longitude.

    Arguments:
        payload (LatLonPayload): The payload containing latitude and longitude.
    Returns:
        list: A list of available DTM providers for the given coordinates.
    """
    available_dtm = mfs.DTMProvider.get_valid_provider_descriptions((payload.lat, payload.lon))
    return available_dtm


@dtm_router.post("/info")
def dtm_info(payload: DTMCodePayload):
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
    settings = dtm.settings()().model_dump() if dtm.settings() else {}
    return {
        "valid": True,
        "provider": dtm.description(),
        "settings_required": dtm.settings_required(),
        "settings": settings,
    }


@dtm_router.post("/dem")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def dtm_dem(payload: DEMSettingsPayload, request: Request) -> dict[str, str | bool]:
    """Generate a DEM (Digital Elevation Model) based on the provided settings.

    Arguments:
        payload (DEMSettingsPayload): The settings payload containing parameters for DEM generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    task_id = get_session_name_from_payload(payload)

    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        ["Background"],
        ["dem"],
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
