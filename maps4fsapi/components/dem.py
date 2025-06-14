"""Generate DEM data for the given payload."""

import uuid

from fastapi import APIRouter, Request

from maps4fsapi.components.models import DEMSettingsPayload
from maps4fsapi.limits import dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, task_generation

dem_router = APIRouter(dependencies=dependencies)


@dem_router.post("/get_dem")
@public_limiter("1/hour")
def get_dem(payload: DEMSettingsPayload, request: Request) -> dict[str, str | bool]:
    """Generate a DEM (Digital Elevation Model) based on the provided settings.

    Arguments:
        payload (DEMSettingsPayload): The settings payload containing parameters for DEM generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    task_id = str(uuid.uuid4())

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
