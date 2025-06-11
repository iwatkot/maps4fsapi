import os
import uuid
from typing import Type

import maps4fs as mfs
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from maps4fs.generator.settings import DEMSettings

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import api_key_auth, is_public

dem_router = APIRouter(dependencies=[Depends(api_key_auth)] if is_public else [])

tasks_dir = os.path.join(os.getcwd(), "tasks")
# ! DEBUG
import shutil

if os.path.exists(tasks_dir):
    shutil.rmtree(tasks_dir)
# ! End of DEBUG


@dem_router.post("/get_dem")
def get_dem(payload: MainSettingsPayload):
    print(payload)
    task_id = str(uuid.uuid4())

    if not payload.dem_settings:
        payload.dem_settings = DEMSettings()

    payload.dem_settings.water_depth = 20

    output = generate(task_id, payload, ["Background"], ["dem"])

    return FileResponse(
        output,
        media_type="application/octet-stream",
        filename=os.path.basename(output),
    )


def generate(
    task_id: str, payload: MainSettingsPayload, components: list[str], assets: list[str]
) -> str:
    game = mfs.Game.from_code(payload.game_code)
    game.set_components_by_names(components)
    dtm_provider = mfs.DTMProvider.get_provider_by_code(payload.dtm_code)
    coordinates = (payload.lat, payload.lon)
    task_directory = os.path.join(tasks_dir, task_id)
    os.makedirs(task_directory, exist_ok=True)
    map = mfs.Map(
        game,
        dtm_provider,
        None,
        coordinates,
        payload.size,
        payload.rotation,
        map_directory=task_directory,
        dem_settings=payload.dem_settings,
    )
    for _ in map.generate():
        pass

    outputs = []
    for component in components:
        active_component = map.get_component(component)
        for asset in assets:
            output = active_component.assets.get(asset)
            outputs.append(output)

    if len(outputs) > 1:
        # TODO: Pack to archive.

        output_path = "blabla.zip"

    else:
        output_path = outputs[0]

    return output_path
