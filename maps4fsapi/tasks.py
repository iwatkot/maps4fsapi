"""This module provides functionality for managing tasks related to map generation."""

import json
import os
import queue
import threading
import zipfile
from collections import deque
from typing import Any, Callable, Literal, NamedTuple

import maps4fs as mfs
import maps4fs.generator.config as mfscfg

from maps4fsapi.components.models import MainSettingsPayload
from maps4fsapi.config import (
    MFS_CUSTOM_OSM_DIR,
    PUBLIC_MAX_MAP_SIZE,
    Singleton,
    human_readable_time_diff,
    is_public,
    logger,
    rounded_time_now,
)
from maps4fsapi.storage import Storage, StorageEntry


class HistoryEntry(NamedTuple):
    """A named tuple representing an entry in the task history."""

    session_name: str
    coordinates: tuple[int, int]  # To not include detailed coordinates, we just round them to int.
    game_code: str  # Game code, e.g., "fs25".
    size: int  # Size of the map in meters.
    status: Literal["Completed", "Failed", "Started processing", "Added to queue"]
    # Tasks that wait in queue do not have a timestamp yet.
    timestamp: int

    def to_json(self) -> dict[str, str | int]:
        """Convert the HistoryEntry to a JSON-serializable dictionary.

        Returns:
            dict[str, str | int]: A dictionary representation of the HistoryEntry.
        """
        time_diff = rounded_time_now() - self.timestamp if self.timestamp else None
        human_time = ""
        if time_diff is not None:
            human_time = human_readable_time_diff(time_diff)

        status_text = f"{self.status} {human_time}"
        coordinates_text = f"{self.coordinates[0]}, {self.coordinates[1]}"

        return {
            "coordinates": coordinates_text,
            "game_code": self.game_code,
            "size": self.size,
            "status": status_text,
        }


class TasksQueue(metaclass=Singleton):
    """A singleton class that manages a queue of tasks for map generation."""

    def __init__(self):
        self.tasks = queue.Queue()
        self.history = deque(maxlen=10)
        self.active_sessions = set()  # Track session names currently in queue or processing
        self.active_sessions_info = set()
        self.processing_now = None
        self.processing_now_info = None
        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def add_task(
        self, session_name: str, func: Callable, payload: MainSettingsPayload, *args, **kwargs
    ):
        """Adds a task to the queue with a session name identifier.

        Arguments:
            session_name (str): Unique session identifier for the task.
            func (Callable): The function to be executed as a task.
            payload (MainSettingsPayload): The payload containing settings for the task.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        self.active_sessions.add(session_name)
        entry = HistoryEntry(
            session_name=session_name,
            coordinates=(int(payload.lat), int(payload.lon)),
            game_code=payload.game_code.upper(),
            size=payload.size,
            status="Added to queue",
            timestamp=rounded_time_now(),
        )
        self.active_sessions_info.add(entry)

        self.tasks.put((session_name, func, payload, args, kwargs))
        queue_size = self.tasks.qsize()
        logger.info(
            "Adding task to queue: %s (session: %s), queue size: %d",
            func.__name__,
            session_name,
            queue_size,
        )

    def get_all_task_info(self) -> list[dict[str, str | int]]:
        """Retrieve information about all tasks: queued, processing, and completed.

        Returns:
            list[dict[str, str | int]]: A list of dictionaries containing task information.
        """
        queued_tasks = list(self.active_sessions_info)
        processing_task = [self.processing_now_info] if self.processing_now_info else []
        completed_tasks = list(self.history)
        all_tasks = completed_tasks + processing_task + queued_tasks
        return [task.to_json() for task in all_tasks]

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

    def what_is_processing(self) -> HistoryEntry | None:
        """Get information about the task that is currently being processed.

        Returns:
            HistoryEntry | None: Information about the currently processing task,
                or None if no task is being processed.
        """
        return self.processing_now_info

    def remove_active_session(self, session_name: str) -> None:
        """Removes a session name from the active sessions info set.

        Arguments:
            session_name (str): The session name to remove.
        """
        entry = next((e for e in self.active_sessions_info if e.session_name == session_name), None)
        if entry:
            self.active_sessions_info.remove(entry)

    def get_active_tasks_count(self) -> int:
        """Get the total number of active tasks (queued + processing).

        Returns:
            int: The total number of active tasks.
        """
        return len(self.active_sessions)

    def _worker(self):
        while True:
            session_name, func, payload, args, kwargs = self.tasks.get()
            self.processing_now = session_name
            self.processing_now_info = HistoryEntry(
                session_name=session_name,
                coordinates=(int(payload.lat), int(payload.lon)),
                game_code=payload.game_code.upper(),
                size=payload.size,
                status="Started processing",
                timestamp=rounded_time_now(),
            )
            self.remove_active_session(session_name)
            history_status = "Failed"
            try:
                func(session_name, payload, *args, **kwargs)
                remaining_tasks = self.tasks.qsize()
                logger.info(
                    "Task completed: %s (session: %s), remaining tasks: %d",
                    func.__name__,
                    session_name,
                    remaining_tasks,
                )
                history_status = "Completed"
            except Exception as e:
                remaining_tasks = self.tasks.qsize()
                logger.error(
                    "Task %s (session: %s) failed with error: %s, remaining tasks: %d",
                    func.__name__,
                    session_name,
                    e,
                    remaining_tasks,
                )
                raise
            finally:
                # Remove session from active set when task completes or fails
                self.active_sessions.discard(session_name)
                self.tasks.task_done()
                self.processing_now = None
                self.processing_now_info = None

                history_entry = HistoryEntry(
                    session_name=session_name,
                    coordinates=(int(payload.lat), int(payload.lon)),
                    game_code=payload.game_code.upper(),
                    size=payload.size,
                    status=history_status,
                    timestamp=rounded_time_now(),
                )

                # Add the history entry to the processing history
                self.history.append(history_entry)


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
            "custom_texture_schema_path": payload.custom_texture_schema_path,
            "custom_tree_schema_path": payload.custom_tree_schema_path,
            "custom_map_template_path": payload.custom_map_template_path,
            "custom_buildings_schema_path": payload.custom_buildings_schema_path,
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

        texture_custom_schema = None
        tree_custom_schema = None
        buildings_custom_schema = None
        if payload.custom_texture_schema_path:
            texture_custom_schema = load_custom_schemas(
                payload.game_code, "texture", payload.custom_texture_schema_path
            )
            logger.info("Loaded custom texture schema from: %s", payload.custom_texture_schema_path)
        if payload.custom_tree_schema_path:
            tree_custom_schema = load_custom_schemas(
                payload.game_code, "tree", payload.custom_tree_schema_path
            )
            logger.info("Loaded custom tree schema from: %s", payload.custom_tree_schema_path)
        if payload.custom_buildings_schema_path:
            buildings_custom_schema = load_custom_schemas(
                payload.game_code, "buildings", payload.custom_buildings_schema_path
            )
            logger.info(
                "Loaded custom buildings schema from: %s", payload.custom_buildings_schema_path
            )

        custom_template_path = None
        if payload.custom_map_template_path:
            full_template_path = os.path.join(
                mfscfg.MFS_TEMPLATES_DIR,
                payload.game_code,
                "map_templates",
                payload.custom_map_template_path,
            )
            logger.info("Using custom map template from path: %s", full_template_path)
            if not os.path.isfile(full_template_path):
                logger.error("Custom map template path does not exist: %s", full_template_path)
                raise ValueError(f"Custom map template path does not exist: {full_template_path}")

            custom_template_path = full_template_path

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
            texture_custom_schema=texture_custom_schema,
            tree_custom_schema=tree_custom_schema,
            custom_template_path=custom_template_path,
            buildings_custom_schema=buildings_custom_schema,
        )

        if is_public:
            # logger.info("Running in public mode, will adjust map settings accordingly.")
            # adjust_settings_for_public(mp)

            if mp.size > PUBLIC_MAX_MAP_SIZE:
                logger.warning(
                    "Map size %s is larger than %s, will stop generation to prevent issues.",
                    mp.size,
                    PUBLIC_MAX_MAP_SIZE,
                )
                raise ValueError(
                    f"Map size exceeds the maximum allowed size for public access {PUBLIC_MAX_MAP_SIZE}."
                )

            if mp.output_size is not None and mp.output_size > PUBLIC_MAX_MAP_SIZE:
                logger.warning(
                    "Output size %s is larger than %s, will stop generation to prevent issues.",
                    mp.output_size,
                    PUBLIC_MAX_MAP_SIZE,
                )
                raise ValueError(
                    f"Output size exceeds the maximum allowed size for public access {PUBLIC_MAX_MAP_SIZE}."
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


def load_custom_schemas(
    game_code: str, schema_type: Literal["texture", "tree", "buildings"], file_name: str
) -> list[dict[str, Any]]:
    """Loads custom texture or tree schemas from a specified file.
    Arguments:
        game_code (str): The game code.
        schema_type (Literal["texture", "tree", "buildings"]): The type of schema to load.
        file_name (str): The name of the schema file to load.

    Raises:
        ValueError: If the schema file does not exist, is empty, or is not a valid list.

    Returns:
        list[dict[str, Any]]: The loaded schema data.
    """
    schema_dirs = {
        "texture": "texture_schemas",
        "tree": "tree_schemas",
        "buildings": "buildings_schemas",
    }
    file_path = os.path.join(
        mfscfg.MFS_TEMPLATES_DIR, game_code, schema_dirs[schema_type], file_name
    )
    if not os.path.isfile(file_path):
        logger.error("Custom %s schema file does not exist: %s", schema_type, file_path)
        raise ValueError(f"Custom {schema_type} schema file does not exist: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        logger.debug("Successfully loaded custom %s schema from: %s", schema_type, file_path)
    except Exception as e:
        logger.error("Failed to load custom %s schema from file: %s", schema_type, e)
        raise ValueError(f"Error loading {schema_type} schema: {e}")

    if not schema_data:
        logger.error("Custom %s schema file is empty: %s", schema_type, file_path)
        raise ValueError(f"Custom {schema_type} schema file is empty: {file_path}")

    if not isinstance(schema_data, list):
        logger.error("Custom %s schema file is not a valid list: %s", schema_type, file_path)
        raise ValueError(f"Custom {schema_type} schema file is not a valid list: {file_path}")

    return schema_data


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


# def adjust_settings_for_public(mp: mfs.Map) -> None:
#     """Adjusts the map settings for public access, modifying the map instance in place.

#     Arguments:
#         mp (mfs.Map): The map instance to adjust.
#     """
#     mp.satellite_settings.zoom_level = min(mp.satellite_settings.zoom_level, 16)
#     mp.texture_settings.dissolve = False
#     mp.background_settings.flatten_roads = False

#     logger.debug("Adjusted map settings for public access.")


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
