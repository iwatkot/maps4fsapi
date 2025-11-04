"""Main entry point for the Maps4FS API application."""

import asyncio
import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from maps4fsapi.components.dtm import dtm_router
from maps4fsapi.components.grle import grle_router
from maps4fsapi.components.i3d import i3d_router
from maps4fsapi.components.map import map_router
from maps4fsapi.components.mesh import mesh_router
from maps4fsapi.components.satellite import satellite_router
from maps4fsapi.components.server import server_router
from maps4fsapi.components.task import task_router
from maps4fsapi.components.templates import templates_router
from maps4fsapi.components.texture import texture_router
from maps4fsapi.components.users import users_router
from maps4fsapi.config import (
    apply_queue,
    is_heavy_endpoint,
    is_public,
    logger,
    package_version,
    version_status,
)
from maps4fsapi.tasks import TasksQueue

# Configure logging to suppress INFO level access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

app = FastAPI()


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Middleware to log incoming requests with IP addresses for map generation endpoint.

    This middleware only logs requests to the /map/generate endpoint. It is designed
    to be fail-safe - if any part of the logging fails, it will continue processing
    the request normally. It captures client IP addresses (including handling proxy
    headers), request timing, and response status codes for monitoring map generation requests.

    Arguments:
        request (Request): The incoming HTTP request object containing headers,
            client information, and request details.
        call_next (Callable): The next middleware or endpoint handler in the
            processing chain to be called with the request.

    Returns:
        Response: The HTTP response object returned by the next handler in the chain.
    """
    # Check if this is the map generation endpoint
    is_heavy = is_heavy_endpoint(request.url.path)

    start_time = time.time() if is_heavy else None
    client_ip = "unknown"

    if is_heavy:
        try:
            # Get client IP (handles proxies with X-Forwarded-For header)
            client_ip = request.client.host if request.client else "unknown"
            if forwarded_for := request.headers.get("X-Forwarded-For"):
                client_ip = forwarded_for.split(",")[0].strip()
            elif real_ip := request.headers.get("X-Real-IP"):
                client_ip = real_ip
        except Exception:
            pass

    origin = request.headers.get("origin", "not_specified")
    if is_heavy:
        if not apply_queue(origin):
            await asyncio.sleep(30)

            return Response(content="", headers={"Connection": "close"})

    response = await call_next(request)

    if is_heavy and start_time is not None:
        try:
            process_time = time.time() - start_time
            user_agent = request.headers.get("user-agent", "unknown")
            logger.info(
                "IP: %s - Origin: %s - %s %s - Status: %s - Time: %.3fs - UA: %s",
                client_ip,
                origin,
                request.method,
                request.url.path,
                response.status_code,
                process_time,
                user_agent[:50] + "..." if len(user_agent) > 50 else user_agent,
            )
        except Exception:
            pass

    return response


if is_public:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://maps4fs.xyz",
            "https://www.maps4fs.xyz",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local deployment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(dtm_router, prefix="/dtm")
app.include_router(mesh_router, prefix="/mesh")
app.include_router(grle_router, prefix="/grle")
app.include_router(task_router, prefix="/task")
app.include_router(i3d_router, prefix="/i3d")
app.include_router(texture_router, prefix="/texture")
app.include_router(map_router, prefix="/map")
app.include_router(satellite_router, prefix="/satellite")
app.include_router(templates_router, prefix="/templates")
app.include_router(server_router, prefix="/server")
app.include_router(users_router, prefix="/users")


@app.get("/info/version")
async def get_version():
    """Endpoint to retrieve the version of the Maps4FS package."""
    return {"version": package_version}


@app.get("/info/status")
async def get_version_status():
    """Endpoint to retrieve the version status of the Maps4FS package."""
    return version_status("maps4fs")


@app.get("/info/queue_size")
async def get_queue_size():
    """Endpoint to retrieve the current number of active tasks (queued + processing)."""
    return {"queue_size": TasksQueue().get_active_tasks_count()}
