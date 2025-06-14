"""This module provides functionality for managing tasks related to map generation."""

import os
import queue
import threading
import zipfile
from typing import Callable, Type

import maps4fs as mfs

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import Singleton, archives_dir, is_public, logger, tasks_dir
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
        logger.debug("Adding task to queue: %s", func.__name__)
        self.tasks.put((func, args, kwargs))

    def _worker(self):
        while True:
            func, args, kwargs = self.tasks.get()
            try:
                func(*args, **kwargs)
                logger.debug("Task completed: %s", func.__name__)
            except Exception as e:
                logger.error("Task %s failed with error: %s", func.__name__, e)
            self.tasks.task_done()


def task_generation(
    task_id: str,
    payload: Type[MainSettingsPayload],
    components: list[str] | None = None,
    assets: list[str] | None = None,
    include_all: bool = False,
) -> None:
    """Generates a map based on the provided payload and saves the output.

    Arguments:
        task_id (str): Unique identifier for the task.
        payload (MainSettingsPayload): The settings payload containing map generation parameters.
        components (list[str]): List of components to be included in the map.
        assets (list[str] | None): Optional list of specific assets to include in the output.
        include_all (bool): If True, includes all components in the map generation.
    """
    try:
        logger.debug("Starting task %s with payload: %s", task_id, payload)
        success = True
        description = "Task completed successfully."

        if not isinstance(payload, MainSettingsPayload):
            raise TypeError("Payload must be an instance of MainSettingsPayload")
        game = mfs.Game.from_code(payload.game_code)
        if components:
            logger.debug("Setting components for the game: %s", components)
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

        mp = mfs.Map(
            game,
            dtm_provider,
            None,
            coordinates,
            payload.size,
            payload.rotation,
            map_directory=task_directory,
            **map_settings,
        )

        if is_public:
            logger.info("Running in public mode, will adjust map settings accordingly.")
            adjust_settings_for_public(mp)

            if mp.size > 4096:
                logger.warning(
                    "Map size %s is larger than 4096, will stop generation to prevent issues.",
                    mp.size,
                )
                raise ValueError(
                    "Map size exceeds the maximum allowed size for public access (4096)."
                )

        for _ in mp.generate():
            pass

        outputs = []
        if not include_all:
            for component in components:
                active_component = mp.get_component(component)
                if not active_component:
                    logger.warning("Component %s not found in the map.", component)
                    continue
                if assets:
                    for asset in assets:
                        output = active_component.assets.get(asset)
                        if output:
                            outputs.append(output)
                else:
                    logger.debug(
                        "No specific assets provided for component %s, generating all assets.",
                        component,
                    )
                    outputs.extend(list(active_component.assets.values()))
        else:
            logger.debug("Working with a mode including all components.")
            archive_path = os.path.join(archives_dir, f"{task_id}.zip")
            mp.pack(archive_path.replace(".zip", ""))
            outputs.append(archive_path)

        logger.debug("Generated outputs: %s", outputs)
        if not outputs:
            raise ValueError("No outputs generated. Check the provided settings and components.")
        if len(outputs) > 1:
            output_path: str = os.path.join(task_directory, f"{task_id}.zip")
            files_to_archive(outputs, output_path)
        else:
            output_path = outputs[0]

        logger.info("Task %s completed successfully. Output saved to %s", task_id, output_path)
    except Exception as e:
        success = False
        description = f"Task failed with error: {e}"
        logger.error("Task %s failed with error: %s", task_id, e)

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


def adjust_settings_for_public(mp: mfs.Map) -> None:
    """Adjusts the map settings for public access, modifying the map instance in place.

    Arguments:
        mp (mfs.Map): The map instance to adjust.
    """
    if mp.background_settings.resize_factor < 8:
        mp.background_settings.resize_factor = 8

    if mp.satellite_settings.zoom_level > 16:
        mp.satellite_settings.zoom_level = 16

    mp.texture_settings.dissolve = False

    logger.debug("Adjusted map settings for public access.")
