"""Server management for the API."""

import docker
import maps4fs.generator.config as mfscfg
from fastapi import APIRouter, BackgroundTasks, HTTPException

from maps4fsapi.config import USERPROFILE, is_public, logger
from maps4fsapi.limits import dependencies

server_router = APIRouter(dependencies=dependencies)


@server_router.get("/upgradable")
def is_upgradable() -> dict[str, bool]:
    """Check if the server can be upgraded.

    Returns:
        dict[str, bool]: True if the server is upgradable, False otherwise.

    Raises:
        HTTPException: If the server is public, USERPROFILE is not set, or Docker is not available.
    """
    if is_public:
        raise HTTPException(status_code=403, detail="Upgrade not allowed on public server.")

    if not USERPROFILE:
        raise HTTPException(
            status_code=500,
            detail="USERPROFILE environment variable is not set. Can not upgrade.",
        )

    try:
        docker.from_env()
    except (docker.errors.DockerException, OSError) as e:
        logger.error("Docker client error: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Docker socket is not available. Can not upgrade.",
        )

    return {"upgradable": True}


@server_router.post("/reload_templates")
def reload_templates():
    """Reload the server templates by running the template reloader Docker container.

    Raises:
        HTTPException: If the server is public or if reloading templates fails.

    The reload process runs in the background after responding to the client.
    """
    logger.info("Received request to reload templates.")
    if is_public:
        raise HTTPException(
            status_code=403, detail="Reloading templates not allowed on public server."
        )

    try:
        mfscfg.reload_templates()
        logger.info("Templates reloaded successfully.")
        return {"success": True}
    except Exception as e:
        logger.error("Failed to reload templates: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to reload templates.",
        )


@server_router.post("/clean_cache")
def clean_cache():
    """Clean the server cache by removing all files in the cache directory.

    Raises:
        HTTPException: If the server is public or if cleaning the cache fails.

    Returns:
        dict[str, bool]: A dictionary indicating whether the cache was cleaned successfully.
    """
    logger.info("Received request to clean cache.")
    if is_public:
        raise HTTPException(status_code=403, detail="Cleaning cache not allowed on public server.")

    try:
        mfscfg.clean_cache()
        logger.info("Cache cleaned successfully.")
        return {"success": True}
    except Exception as e:
        logger.error("Failed to clean cache: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to clean cache.",
        )


def run_upgrader():
    """Background task to run the upgrader container.

    Launches the Docker container to perform the upgrade. Handles cleanup of existing
    containers and images before running the new upgrader.
    """
    logger.info("Running upgrader container...")
    try:
        client = docker.from_env()
        logger.info("Docker client initialized successfully.")

        try:
            existing_container = client.containers.get("maps4fsupgrader")
            logger.info("Found existing maps4fsupgrader container, stopping it...")
            existing_container.stop(timeout=10)
            logger.info("Stopped existing maps4fsupgrader container")
            existing_container.remove(force=True)
            logger.info("Removed existing maps4fsupgrader container")
        except docker.errors.NotFound:
            logger.debug("No existing maps4fsupgrader container found")
        except Exception as e:
            logger.warning("Failed to stop existing container: %s", e)

        try:
            client.images.remove("iwatkot/maps4fsupgrader:latest", force=True)
            logger.info("Removed existing iwatkot/maps4fsupgrader image")
        except docker.errors.ImageNotFound:
            logger.debug("No existing iwatkot/maps4fsupgrader image to remove")
        except Exception as e:
            logger.warning("Failed to remove existing image: %s", e)

        logger.info("Launching new maps4fsupgrader container...")

        container = client.containers.run(
            "iwatkot/maps4fsupgrader:latest",
            name="maps4fsupgrader",
            detach=True,
            auto_remove=True,
            environment={"USERPROFILE": USERPROFILE},
            volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}},
        )
        logger.info("Launched upgrader container with ID: %s", container.id)

    except Exception as e:
        logger.error("Failed to launch upgrader container: %s", e)


@server_router.post("/upgrade")
def upgrade_server(background_tasks: BackgroundTasks):
    """Upgrade the server by running the upgrader Docker container.

    The upgrade process runs in the background after responding to the client.

    Raises:
        HTTPException: If the server is not upgradable.
    """
    logger.info("Received request to upgrade the server.")
    res = is_upgradable()
    if not res.get("upgradable", False):
        logger.error("Server is not upgradable.")
        raise HTTPException(
            status_code=500, detail="Server is not upgradable for an unknown reason."
        )

    logger.info("Starting server upgrade in the background.")
    background_tasks.add_task(run_upgrader)

    return {
        "success": True,
        "message": "Server upgrade initiated. The upgrade will run in the background.",
    }
