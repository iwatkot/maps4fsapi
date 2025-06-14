"""Task management for data retrieval in FastAPI application."""

import os

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from maps4fsapi.components.models import TaskIdPayload
from maps4fsapi.config import logger
from maps4fsapi.limits import dependencies
from maps4fsapi.storage import Storage

task_router = APIRouter(dependencies=dependencies)


@task_router.post("/get")
def get_task(payload: TaskIdPayload, background_tasks: BackgroundTasks):
    """Retrieve a task result based on the provided task ID.

    Arguments:
        payload (TaskIdPayload): The payload containing the task ID.
        background_tasks (BackgroundTasks): Background tasks to handle cleanup after response.

    Returns:
        FileResponse: A response containing the DEM file if successful, or an error message.
    """
    logger.info("Received request to get task with ID: %s", payload.task_id)
    entry = Storage().get_entry(payload.task_id)
    if not entry:
        logger.warning("Task ID %s not found.", payload.task_id)
        return HTTPException(
            status_code=404,
            detail="Task ID not found. It's expired or not finished yet.",
        )

    if not entry.success:
        logger.warning("Task %s failed with error: %s", payload.task_id, entry.description)
        return HTTPException(
            status_code=400,
            detail=entry.description,
        )

    if not entry.file_path:
        logger.warning("No file path found for task ID %s.", payload.task_id)
        return HTTPException(
            status_code=404,
            detail="No file path found for the task.",
        )

    if not os.path.isfile(entry.file_path):
        logger.warning(
            "File at path %s not found for task ID %s.", entry.file_path, payload.task_id
        )
        return HTTPException(
            status_code=404,
            detail="File not found.",
        )

    background_tasks.add_task(Storage().remove_entry, payload.task_id)
    logger.info("Returning file for task ID %s: %s", payload.task_id, entry.file_path)

    return FileResponse(
        entry.file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(entry.file_path),
    )
