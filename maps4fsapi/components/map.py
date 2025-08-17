"""Generate GRLE data for the given payload."""

from fastapi import APIRouter, Request

from maps4fsapi.components.models import MapGenerationPayload
from maps4fsapi.limits import HIGH_DEMAND_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, get_session_name_from_payload, task_generation

map_router = APIRouter(dependencies=dependencies)


@map_router.post("/generate")
@public_limiter(HIGH_DEMAND_PUBLIC_LIMIT)
def map_generation(
    payload: MapGenerationPayload,
    request: Request,
) -> dict[str, str | bool]:
    """Generate a complete map based on the provided settings.

    Arguments:
        payload (MapGenerationPayload): The settings payload containing parameters for map generation.

    Returns:
        dict: A dictionary containing the success status, description, and task ID.
    """
    task_id = get_session_name_from_payload(payload)

    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        None,
        None,
        include_all=True,
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }
