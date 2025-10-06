"""Generate GRLE data for the given payload."""

from fastapi import APIRouter, HTTPException, Request

from maps4fsapi.components.models import MapGenerationPayload
from maps4fsapi.config import PUBLIC_QUEUE_LIMIT, is_public
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
        dict | HTTPException: A dictionary containing the success status, description, and task ID.

    Raises:
        HTTPException: If the server is under high demand and cannot accept new tasks.
    """
    if is_public:
        queue_size = TasksQueue().tasks.qsize()
        if queue_size >= PUBLIC_QUEUE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="The server is currently experiencing high demand. Please try again later.",
            )

    task_id = get_session_name_from_payload(payload)

    TasksQueue().add_task(
        task_id,
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
