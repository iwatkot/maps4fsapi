"""Generate GRLE data for the given payload."""

from fastapi import APIRouter, Request

from maps4fsapi.components.models import SatelliteSettingsPayload
from maps4fsapi.limits import DEFAULT_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, get_session_name_from_payload, task_generation

satellite_router = APIRouter(dependencies=dependencies)


@satellite_router.post("/overview")
@satellite_router.post("/background")
@public_limiter(DEFAULT_PUBLIC_LIMIT)
def satellite_generation(
    payload: SatelliteSettingsPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a satellite data based on the provided settings.

    Arguments:
        payload (SatelliteSettingsPayload): The settings payload containing parameters for satellite generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    endpoint = request.url.path

    task_id = get_session_name_from_payload(payload)

    payload.satellite_settings.download_images = True

    if endpoint.endswith("/overview"):
        assets = ["overview"]
    else:
        assets = ["background"]

    TasksQueue().add_task(
        task_id,
        task_generation,
        # task_id,
        payload,
        ["Satellite"],
        assets,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
