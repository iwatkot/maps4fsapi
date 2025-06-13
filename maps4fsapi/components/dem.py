import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import api_key_auth, is_public
from maps4fsapi.tasks import TasksQueue, task_generation

dem_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])


@dem_router.post("/get_dem")
def get_dem(payload: MainSettingsPayload):
    # task_id = str(uuid.uuid4())
    task_id = "123"  # ! Debugging purpose only, remove in production

    payload.dem_settings.water_depth = 20

    # 1. Add task to the queue.
    # 2. Return the task ID to the user with a message.
    TasksQueue().add_task(
        task_generation,
        task_id,
        payload,
        ["Background"],
        ["dem"],
    )

    return {
        "success": True,
        "description": "Task has been added to the queue. Use the task ID to retrieve the result.",
        "task_id": task_id,
    }

    # output = generate(task_id, payload, ["Background"], ["dem"])

    # return FileResponse(
    #     output,
    #     media_type="application/octet-stream",
    #     filename=os.path.basename(output),
    # )
