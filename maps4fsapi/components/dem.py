"""Generate DEM data for the given payload."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from maps4fsapi.components.models import DEMSettingsPayload
from maps4fsapi.config import api_key_auth, is_public
from maps4fsapi.tasks import TasksQueue, task_generation

dem_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])


@dem_router.post("/get_dem")
def get_dem(payload: DEMSettingsPayload) -> dict[str, str | bool] | HTTPException:
    """Generate a DEM (Digital Elevation Model) based on the provided settings.

    Arguments:
        payload (DEMSettingsPayload): The settings payload containing parameters for DEM generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    task_id = str(uuid.uuid4())

    if not payload.dem_settings:
        return HTTPException(
            status_code=400,
            detail="DEM settings are required. Please provide valid DEM settings.",
        )
    payload.dem_settings.water_depth = 20

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
