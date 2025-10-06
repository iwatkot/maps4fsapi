"""This module provides functionality for managing tasks related to map generation."""

import os
import queue
import threading
import zipfile
from typing import Callable

import maps4fs as mfs
import maps4fs.generator.config as mfscfg

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import MFS_CUSTOM_OSM_DIR, Singleton, is_public, logger
from maps4fsapi.storage import Storage, StorageEntry


class TasksQueue(metaclass=Singleton):
    """A singleton class that manages a queue of tasks for map generation."""

    def __init__(self):
        self.tasks = queue.Queue()
        self.active_sessions = set()  # Track session names currently in queue or processing
        self.processing_now = None
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def add_task(self, session_name: str, func: Callable, *args, **kwargs):
        """Adds a task to the queue with a session name identifier.

        Arguments:
            session_name (str): Unique session identifier for the task.
            func (Callable): The function to be executed as a task.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        logger.debug("Adding task to queue: %s (session: %s)", func.__name__, session_name)
        self.active_sessions.add(session_name)
        self.tasks.put((session_name, func, args, kwargs))

    def is_in_queue(self, session_name: str) -> bool:
        """Check if a task with the given session name is currently in queue or being processed.

        Arguments:
            session_name (str): The session name to check.

        Returns:
            bool: True if session is active (queued or processing), False otherwise.
        """
        return session_name in self.active_sessions

    def is_processing(self, session_name: str) -> bool:
        """Check if a task with the given session name is currently being processed.

        Arguments:
            session_name (str): The session name to check.

        Returns:
            bool: True if session is currently being processed, False otherwise.
        """
        return session_name == self.processing_now

    def _worker(self):
        while True:
            session_name, func, args, kwargs = self.tasks.get()
            self.processing_now = session_name
            try:
                func(*args, **kwargs)
                logger.debug("Task completed: %s (session: %s)", func.__name__, session_name)
            except Exception as e:
                logger.error(
                    "Task %s (session: %s) failed with error: %s", func.__name__, session_name, e
                )
                raise e
            finally:
                # Remove session from active set when task completes or fails
                self.active_sessions.discard(session_name)
                self.tasks.task_done()
                self.processing_now = None


def get_session_name(coordinates: tuple[float, float], game_code: str) -> str:
    """Generates a session name based on the coordinates and game code.

    Arguments:
        coordinates (tuple[float, float]): The latitude and longitude coordinates.
        game_code (str): The game code.

    Returns:
        str: The generated session name.
    """
    return mfs.Map.suggest_directory_name(coordinates, game_code)


def get_session_name_from_payload(payload: MainSettingsPayload) -> str:
    """Generates a session name based on the payload.

    Arguments:
        payload (MainSettingsPayload): The settings payload containing map generation parameters.

    Returns:
        str: The generated session name.
    """
    return get_session_name((payload.lat, payload.lon), payload.game_code)


def task_generation(
    session_name: str,
    payload: MainSettingsPayload,
    components: list[str] | None = None,
    assets: list[str] | None = None,
    include_all: bool = False,
) -> None:
    """Generates a map based on the provided payload and saves the output.

    Arguments:
        session_name (str): Unique identifier for the task.
        payload (MainSettingsPayload): The settings payload containing map generation parameters.
        components (list[str]): List of components to be included in the map.
        assets (list[str] | None): Optional list of specific assets to include in the output.
        include_all (bool): If True, includes all components in the map generation.
    """
    task_directory = None
    output_path = None
    try:
        # Log payload without the potentially huge OSM data
        payload_summary = {
            "game_code": payload.game_code,
            "dtm_code": payload.dtm_code,
            "lat": payload.lat,
            "lon": payload.lon,
            "size": payload.size,
            "output_size": payload.output_size,
            "rotation": payload.rotation,
            "is_public": payload.is_public,
            "has_custom_osm": hasattr(payload, "custom_osm_xml")
            and payload.custom_osm_xml is not None,
            "has_custom_osm_path": hasattr(payload, "custom_osm_path")
            and payload.custom_osm_path is not None,
            "has_custom_dem_path": hasattr(payload, "custom_dem_path")
            and payload.custom_dem_path is not None,
        }
        logger.info("Starting task %s with payload summary: %s", session_name, payload_summary)
        success = True
        description = "Task completed successfully."

        if not isinstance(payload, MainSettingsPayload):
            raise TypeError("Payload must be an instance of MainSettingsPayload")
        game = mfs.Game.from_code(payload.game_code)
        if components:
            logger.debug("Setting components for the game: %s", components)
            game.set_components_by_names(components)
        dtm_provider = mfs.DTMProvider.get_provider_by_code(payload.dtm_code)

        if not dtm_provider:
            raise ValueError(f"DTM provider with code {payload.dtm_code} not found.")

        dtm_provider_settings = None
        if dtm_provider.settings_required():
            logger.debug("DTM provider requires settings, will validate provided settings.")
            if not payload.dtm_settings:
                raise ValueError(
                    "Specified DTM Provider requires additional settings, but none were provided."
                )
            logger.debug("Validating DTM provider settings: %s", payload.dtm_settings)
            try:
                dtm_provider_settings = dtm_provider.settings()(**payload.dtm_settings)
                logger.debug("DTM provider settings validated successfully.")
            except Exception as e:
                logger.error("Failed to validate DTM provider settings: %s", e)
                raise

        coordinates = (payload.lat, payload.lon)
        task_directory = os.path.join(mfscfg.MFS_DATA_DIR, session_name)
        os.makedirs(task_directory, exist_ok=True)

        prepared_settings = {
            attr: getattr(payload, attr)
            for attr in dir(payload)
            if attr.endswith("_settings") and hasattr(payload, attr)
        }
        generation_settings_json = {}
        for key, value in prepared_settings.items():
            if isinstance(value, mfs.settings.SettingsModel):
                new_value = value.model_dump()
            elif isinstance(value, dict):
                new_value = value
            else:
                continue
            generation_settings_json[key] = new_value

        generation_settings = mfs.GenerationSettings.from_json(
            generation_settings_json, from_snake=True, safe=True
        )

        custom_osm = None
        if payload.custom_osm_xml:
            try:
                save_path = os.path.join(MFS_CUSTOM_OSM_DIR, f"{session_name}_custom.osm")
                osm_str_to_xml(payload.custom_osm_xml, save_path)
                custom_osm = save_path
            except Exception as e:
                logger.error("Failed to convert custom OSM XML: %s", e)
                raise ValueError(f"Error processing custom OSM data: {e}")
        elif payload.custom_osm_path:
            expected_osm_path = os.path.join(mfscfg.MFS_OSM_DEFAULTS_DIR, payload.custom_osm_path)
            if not os.path.isfile(expected_osm_path):
                logger.error("Custom OSM path does not exist: %s", expected_osm_path)
                raise ValueError(f"Custom OSM path does not exist: {expected_osm_path}")
            logger.info("Using custom OSM file from path: %s", expected_osm_path)
            custom_osm = expected_osm_path

        custom_background_path = None
        if payload.custom_dem_path:
            expected_dem_path = os.path.join(mfscfg.MFS_DEM_DEFAULTS_DIR, payload.custom_dem_path)
            if not os.path.isfile(expected_dem_path):
                logger.error("Custom DEM path does not exist: %s", expected_dem_path)
                raise ValueError(f"Custom DEM path does not exist: {expected_dem_path}")
            logger.info("Using custom DEM file from path: %s", expected_dem_path)
            custom_background_path = expected_dem_path

        mp = mfs.Map(
            game,
            dtm_provider,
            dtm_provider_settings,
            coordinates,
            payload.size,
            payload.rotation,
            map_directory=task_directory,
            generation_settings=generation_settings,
            custom_osm=custom_osm,
            is_public=payload.is_public,
            output_size=payload.output_size,
            custom_background_path=custom_background_path,
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

        previews = mp.previews()

        outputs = []
        if not include_all and components:
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
            archive_path = os.path.join(mfscfg.MFS_DATA_DIR, f"{session_name}.zip")
            mp.pack(archive_path.replace(".zip", ""), remove_source=False)
            outputs.append(archive_path)

        logger.debug("Generated outputs: %s", outputs)
        if not outputs:
            raise ValueError("No outputs generated. Check the provided settings and components.")
        if len(outputs) > 1:
            output_path = os.path.join(task_directory, f"{session_name}.zip")
            files_to_archive(outputs, output_path)
        else:
            output_path = outputs[0]

        logger.info("Task %s completed successfully. Output saved to %s", session_name, output_path)
    except Exception as e:
        success = False
        description = f"Task failed with error: {e}"
        logger.error("Task %s failed with error: %s", session_name, e)

        previews = []
    finally:
        storage_entry = StorageEntry(
            success=success,
            description=description,
            directory=task_directory,
            file_path=output_path,
            previews=previews,
        )

    Storage().add_entry(session_name, storage_entry)


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
    mp.satellite_settings.zoom_level = min(mp.satellite_settings.zoom_level, 16)
    mp.texture_settings.dissolve = False

    logger.debug("Adjusted map settings for public access.")


def osm_str_to_xml(custom_osm_str: str, save_path: str) -> None:
    """Converts an OSM stringified data to XML format and saves it to a file.

    Arguments:
        custom_osm_str (str): The OSM XML string to save.
        save_path (str): The path to save the XML file.
    """
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(custom_osm_str)

        logger.debug("Successfully saved OSM XML to: %s", save_path)

    except Exception as e:
        logger.error("Failed to save OSM XML to file: %s", e)
        raise ValueError(f"Error saving OSM data: {e}")
