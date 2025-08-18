"""Generate mesh data for the given payload."""

from fastapi import APIRouter, Request

from maps4fsapi.components.models import BackgroundSettingsPayload
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, get_session_name_from_payload, task_generation

mesh_router = APIRouter(dependencies=dependencies)


@mesh_router.post("/background")
@mesh_router.post("/water")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def mesh_generation(
    payload: BackgroundSettingsPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a mesh background based on the provided settings.

    Arguments:
        payload (BackgroundSettingsPayload): The settings payload containing parameters for mesh generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    endpoint = request.url.path

    task_id = get_session_name_from_payload(payload)

    if endpoint.endswith("/water"):
        generate_water = True
        assets = ["water_mesh"]
    else:
        generate_water = False
        assets = ["background_mesh"]

    payload.background_settings.generate_background = not generate_water
    payload.background_settings.generate_water = generate_water

    TasksQueue().add_task(
        task_id,
        task_generation,
        task_id,
        payload,
        ["Background"],
        assets,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
