"""Generate GRLE data for the given payload."""

import uuid

from fastapi import APIRouter, Request

from maps4fsapi.components.models import GRLESettingsPayload
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, task_generation

grle_router = APIRouter(dependencies=dependencies)


@grle_router.post("/plants")
@grle_router.post("/farmlands")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def grle_generation(
    payload: GRLESettingsPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a GRLE (Georeferenced Raster Layer) based on the provided settings.

    Arguments:
        payload (GRLESettingsPayload): The settings payload containing parameters for GRLE generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    endpoint = request.url.path

    task_id = str(uuid.uuid4())

    if endpoint.endswith("/plants"):
        assets = ["plants"]
    else:
        assets = ["farmlands"]

    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        ["Texture", "GRLE"],
        assets,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
