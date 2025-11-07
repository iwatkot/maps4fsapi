"""Generate GRLE data for the given payload."""

import os

import maps4fs.generator.config as mfscfg
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from maps4fsapi.components.models import MapGenerationPayload
from maps4fsapi.config import PUBLIC_QUEUE_LIMIT, is_public
from maps4fsapi.limits import HIGH_DEMAND_PUBLIC_LIMIT, dependencies, public_limiter
from maps4fsapi.tasks import TasksQueue, get_session_name_from_payload, task_generation

map_router = APIRouter()


@map_router.post("/generate", dependencies=dependencies)
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
        active_tasks_count = TasksQueue().get_active_tasks_count()
        if active_tasks_count >= PUBLIC_QUEUE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="The server is currently experiencing high demand. Please try again later.",
            )

    task_id = get_session_name_from_payload(payload)

    TasksQueue().add_task(
        task_id,
        task_generation,
        # task_id,
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


@map_router.get("/download/{task_id}")
def download_map(task_id: str) -> FileResponse:
    """Download the generated map file for the given task ID.
    This endpoint can be used outside of the UI to directly download the map.

    Arguments:
        task_id (str): The unique identifier for the map generation task.

    Returns:
        FileResponse: The response containing the map file for download.

    Raises:
        HTTPException: If the map file is not found for the given task ID.
    """
    if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    archive_name = f"{task_id}.zip"
    archive_file_path = os.path.join(mfscfg.MFS_DATA_DIR, archive_name)

    # Resolve absolute paths and ensure the file is within the allowed directory
    data_dir_abs = os.path.abspath(mfscfg.MFS_DATA_DIR)
    archive_file_abs = os.path.abspath(archive_file_path)

    # Check if the resolved path is within the data directory
    if not os.path.commonpath([data_dir_abs, archive_file_abs]) == data_dir_abs:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not os.path.isfile(archive_file_abs):
        raise HTTPException(
            status_code=404,
            detail=(
                "The requested map file was not found. If the task ID is correct, "
                "it can be that the task is still processing, was already removed "
                "from the server, or it's been an error during generation."
            ),
        )

    return FileResponse(
        archive_file_abs,
        media_type="application/octet-stream",
        filename=os.path.basename(archive_file_abs),
    )
