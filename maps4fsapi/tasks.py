"""This module provides functionality for managing tasks related to map generation."""

import os
import queue
import threading
import zipfile
from typing import Callable, Type

import maps4fs as mfs

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import Singleton, tasks_dir
from maps4fsapi.storage import Storage, StorageEntry


class TasksQueue(metaclass=Singleton):
    """A singleton class that manages a queue of tasks for map generation."""

    def __init__(self):
        self.tasks = queue.Queue()
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def add_task(self, func: Callable, *args, **kwargs):
        """Adds a task to the queue.

        Arguments:
            func (Callable): The function to be executed as a task.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        self.tasks.put((func, args, kwargs))

    def _worker(self):
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Task failed: {e}")
            self.tasks.task_done()


def task_generation(
    task_id: str,
    payload: Type[MainSettingsPayload],
    components: list[str],
    assets: list[str] | None = None,
) -> None:
    """Generates a map based on the provided payload and saves the output.

    Arguments:
        task_id (str): Unique identifier for the task.
        payload (MainSettingsPayload): The settings payload containing map generation parameters.
        components (list[str]): List of components to be included in the map.
        assets (list[str] | None): Optional list of specific assets to include in the output.
    """
    try:
        success = True
        description = "Task completed successfully."

        if not isinstance(payload, MainSettingsPayload):
            raise TypeError("Payload must be an instance of MainSettingsPayload")
        game = mfs.Game.from_code(payload.game_code)
        game.set_components_by_names(components)
        dtm_provider = mfs.DTMProvider.get_provider_by_code(payload.dtm_code)
        coordinates = (payload.lat, payload.lon)
        task_directory: str = os.path.join(tasks_dir, task_id)
        os.makedirs(task_directory, exist_ok=True)

        map_settings = {
            attr: getattr(payload, attr)
            for attr in dir(payload)
            if attr.endswith("_settings") and hasattr(payload, attr)
        }

        map = mfs.Map(
            game,
            dtm_provider,
            None,
            coordinates,
            payload.size,
            payload.rotation,
            map_directory=task_directory,
            **map_settings,
        )
        for _ in map.generate():
            pass

        outputs = []
        for component in components:
            active_component = map.get_component(component)
            if not assets:
                outputs.extend(list(active_component.assets.values()))
                continue
            for asset in assets:
                output = active_component.assets.get(asset)
                outputs.append(output)

        if len(outputs) > 1:
            output_path: str = os.path.join(task_directory, f"{task_id}.zip")
            files_to_archive(outputs, output_path)

        else:
            output_path = outputs[0]
    except Exception as e:
        success = False
        description = f"Task failed with error: {e}"

    storage_entry = StorageEntry(
        success=success, description=description, directory=task_directory, file_path=output_path
    )

    Storage().add_entry(task_id, storage_entry)


def files_to_archive(filepaths: list[str], archive_path: str) -> None:
    """Creates a zip archive containing the specified files.

    Arguments:
        filepaths (list[str]): List of file paths to include in the archive.
        archive_path (str): Path where the zip archive will be created.
    """
    with zipfile.ZipFile(archive_path, "w") as archive:
        for filepath in filepaths:
            if os.path.isfile(filepath):
                archive.write(filepath, arcname=os.path.basename(filepath))
