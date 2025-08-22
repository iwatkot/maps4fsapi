"""Task management for data retrieval in FastAPI application."""

import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse

from maps4fsapi.components.models import TaskIdPayload
from maps4fsapi.config import logger
from maps4fsapi.limits import dependencies
from maps4fsapi.storage import Storage
from maps4fsapi.tasks import TasksQueue

task_router = APIRouter(dependencies=dependencies)


@task_router.post("/status")
@task_router.post("/get")
def get_task(payload: TaskIdPayload, request: Request, background_tasks: BackgroundTasks):
    """Retrieve a task result based on the provided task ID.
    If used the 'status' endpoint, does not return actual data.
    If used the 'get' endpoint, returns the actual data and removes the entry from storage.

    Arguments:
        payload (TaskIdPayload): The payload containing the task ID.
        request (Request): The request object.
        background_tasks (BackgroundTasks): Background tasks to handle cleanup after response.
    Raises:
        HTTPException: If the task ID is not found, the task failed, or the file is not available.
    Returns:
        FileResponse: A response containing the DEM file if successful, or an error message.
    """
    logger.info("Received request to get task with ID: %s", payload.task_id)
    entry = Storage().get_entry(payload.task_id)
    if not entry:
        # * Order matters! Currently processing task is also in the queue.
        if TasksQueue().is_processing(payload.task_id):
            logger.warning("Task ID %s is currently being processed.", payload.task_id)
            raise HTTPException(
                status_code=202,
                detail=f"Task ID {payload.task_id} is currently being processed.",
            )
        if TasksQueue().is_in_queue(payload.task_id):
            logger.warning("Task ID %s is still in the queue.", payload.task_id)
            raise HTTPException(
                status_code=204,
                detail=f"Task ID {payload.task_id} is still in the queue.",
            )

        logger.warning("Task ID %s not found.", payload.task_id)
        raise HTTPException(
            status_code=404,
            detail=f"Task ID {payload.task_id} not found. It's expired or not finished yet.",
        )

    if not entry.success:
        logger.warning("Task %s failed with error: %s", payload.task_id, entry.description)
        raise HTTPException(
            status_code=400,
            detail=entry.description,
        )

    if not entry.file_path:
        logger.warning("No file path found for task ID %s.", payload.task_id)
        raise HTTPException(
            status_code=404,
            detail=f"No file path found for task ID {payload.task_id}.",
        )

    if not os.path.isfile(entry.file_path):
        logger.warning(
            "File at path %s not found for task ID %s.", entry.file_path, payload.task_id
        )
        raise HTTPException(
            status_code=404,
            detail=f"File not found for task ID {payload.task_id}.",
        )

    endpoint = request.url.path
    if endpoint.endswith("/status"):
        return {
            "success": True,
            "description": "Task completed successfully. Use the 'get' endpoint to retrieve the file.",
            "task_id": payload.task_id,
        }

    background_tasks.add_task(Storage().remove_entry, payload.task_id)
    logger.info("Returning file for task ID %s: %s", payload.task_id, entry.file_path)

    return FileResponse(
        entry.file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(entry.file_path),
    )
