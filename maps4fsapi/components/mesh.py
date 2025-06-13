"""Generate mesh data for the given payload."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from maps4fsapi.components.models import BackgroundSettingsPayload
from maps4fsapi.config import api_key_auth, is_public
from maps4fsapi.tasks import TasksQueue, task_generation

mesh_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])


@mesh_router.post("/background")
@mesh_router.post("/water")
def generate_background(
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

    task_id = str(uuid.uuid4())

    if not payload.background_settings:
        return HTTPException(
            status_code=400,
            detail="Background settings are required. Please provide valid Background settings.",
        )

    if endpoint.endswith("/water"):
        generate_water = True
        assets = ["water_mesh"]
    else:
        generate_water = False
        assets = ["background_mesh"]
    generate_background = not generate_water

    payload.background_settings.generate_background = generate_background
    payload.background_settings.generate_water = generate_water

    # section DEBUG
    payload.background_settings.remove_center = False  # TODO: Remove this line in production.
    # This does not work on MacOS, so we disable it for now.
    # section END DEBUG

    TasksQueue().add_task(
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
