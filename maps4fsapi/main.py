"""Main entry point for the Maps4FS API application."""

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
from maps4fsapi.components.task import task_router
from maps4fsapi.components.templates import templates_router
from maps4fsapi.components.texture import texture_router
from maps4fsapi.config import logger, package_version, version_status

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
    is_map_generate = request.url.path == "/map/generate"

    start_time = time.time() if is_map_generate else None
    client_ip = "unknown"

    if is_map_generate:
        try:
            # Get client IP (handles proxies with X-Forwarded-For header)
            client_ip = request.client.host if request.client else "unknown"
            if forwarded_for := request.headers.get("X-Forwarded-For"):
                client_ip = forwarded_for.split(",")[0].strip()
            elif real_ip := request.headers.get("X-Real-IP"):
                client_ip = real_ip
        except Exception:
            pass

    response = await call_next(request)

    if is_map_generate:
        try:
            process_time = time.time() - start_time
            logger.info(
                "IP: %s - %s %s - Status: %s - Time: %.3fs",
                client_ip,
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )
        except Exception:
            pass

    return response


# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for public API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
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


@app.get("/info/version")
async def get_version():
    """Endpoint to retrieve the version of the Maps4FS package."""
    return {"version": package_version}


@app.get("/info/status")
async def get_version_status():
    """Endpoint to retrieve the version status of the Maps4FS package."""
    return version_status("maps4fs")
