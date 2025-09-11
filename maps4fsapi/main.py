"""Main entry point for the Maps4FS API application."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from maps4fsapi.components.dtm import dtm_router
from maps4fsapi.components.grle import grle_router
from maps4fsapi.components.i3d import i3d_router
from maps4fsapi.components.map import map_router
from maps4fsapi.components.mesh import mesh_router
from maps4fsapi.components.satellite import satellite_router
from maps4fsapi.components.task import task_router
from maps4fsapi.components.texture import texture_router
from maps4fsapi.config import package_version

# Configure logging to suppress INFO level access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

app = FastAPI()

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


@app.get("/info/version")
async def get_version():
    """Endpoint to retrieve the version of the Maps4FS package."""
    return {"version": package_version}
