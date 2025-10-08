"""Server management for the API."""

import docker
from fastapi import APIRouter, BackgroundTasks, HTTPException

from maps4fsapi.config import USERPROFILE, is_public, logger
from maps4fsapi.limits import dependencies

server_router = APIRouter(dependencies=dependencies)


@server_router.get("/upgradable")
def is_upgradable() -> dict[str, bool]:
    """Check if the server can be upgraded.

    Returns:
        bool: True if the server is upgradable, False otherwise.
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


def run_upgrader():
    """Background task to run the upgrader container."""
    try:
        client = docker.from_env()
        container = client.containers.run(
            "iwatkot/maps4fsupgrader:latest",
            detach=True,
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
    """
    try:
        res = is_upgradable()
    except HTTPException as e:
        raise e

    if not res.get("upgradable", False):
        raise HTTPException(
            status_code=500, detail="Server is not upgradable for an unknown reason."
        )

    background_tasks.add_task(run_upgrader)

    return {
        "success": True,
        "message": "Server upgrade initiated. The upgrade will run in the background.",
    }
