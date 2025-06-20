"""Generate GRLE data for the given payload."""

import uuid

from fastapi import APIRouter, Request

from maps4fsapi.components.models import TextureSettingsPayload
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, task_generation

texture_router = APIRouter(dependencies=dependencies)


@texture_router.post("/images")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def texture_generation(
    payload: TextureSettingsPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a texture data based on the provided settings.

    Arguments:
        payload (I3DSettingsPayload): The settings payload containing parameters for I3D generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    task_id = str(uuid.uuid4())

    assets = None
    if payload.layer_names:
        assets = payload.layer_names

    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        ["Texture"],
        assets,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
