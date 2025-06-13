"""Task management for DEM retrieval in FastAPI application."""

import os

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse

from maps4fsapi.components.models import TaskIdPayload
from maps4fsapi.config import api_key_auth, is_public
from maps4fsapi.storage import Storage

task_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])


@task_router.post("/get")
def get_dem(payload: TaskIdPayload, background_tasks: BackgroundTasks):
    """Retrieve a DEM file based on the provided task ID.

    Arguments:
        payload (TaskIdPayload): The payload containing the task ID.
        background_tasks (BackgroundTasks): Background tasks to handle cleanup after response.

    Returns:
        FileResponse: A response containing the DEM file if successful, or an error message.
    """

    entry = Storage().get_entry(payload.task_id)
    if not entry:
        return {
            "success": False,
            "description": "Task ID not found or has expired.",
        }

    if not entry.success:
        return {
            "success": False,
            "description": entry.description,
        }

    if not os.path.isfile(entry.file_path):
        return {
            "success": False,
            "description": "File not found.",
        }

    background_tasks.add_task(Storage().remove_entry, payload.task_id)

    return FileResponse(
        entry.file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(entry.file_path),
    )
