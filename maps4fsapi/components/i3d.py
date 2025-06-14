"""Generate GRLE data for the given payload."""

import uuid

from fastapi import APIRouter, Request

from maps4fsapi.components.models import I3DSettingsPayload
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, task_generation

i3d_router = APIRouter(dependencies=dependencies)


@i3d_router.post("/fields")
@i3d_router.post("/forests")
@i3d_router.post("/splines")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def i3d_generation(
    payload: I3DSettingsPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a I3D data based on the provided settings.

    Arguments:
        payload (I3DSettingsPayload): The settings payload containing parameters for I3D generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    endpoint = request.url.path

    task_id = str(uuid.uuid4())

    if endpoint.endswith("/forests"):
        assets = ["forests"]
        payload.i3d_settings.add_trees = True
    elif endpoint.endswith("/fields"):
        assets = ["fields"]
    else:
        assets = ["splines"]

    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        ["Background", "Texture", "I3d"],
        assets,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
