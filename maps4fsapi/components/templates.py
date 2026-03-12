"""Templates API endpoints for Maps4FS."""

import json
import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from maps4fs.generator.constants import Paths

from maps4fsapi.components.models import SchemaPayload
from maps4fsapi.limits import dependencies

templates_router = APIRouter(dependencies=dependencies)


@templates_router.post("/schemas")
def get_schema(payload: SchemaPayload):
    """Get JSON schema for provided parameters.

    Arguments:
        payload (SchemaPayload): The payload containing the game code and schema type.
    Returns:
        dict: The JSON schema for the specified game code and schema type.
    """
    schema_path = get_schema_path(payload.game_code, payload.schema_type)
    if not schema_path:
        raise HTTPException(status_code=404, detail="Schema not found")

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading schema: {str(e)}")


def get_schema_path(
    game_code: Literal["fs25", "FS25"], schema: Literal["texture", "tree", "grle"]
) -> str | None:
    """Get the path to the schema file based on game code and schema type.

    Arguments:
        game_code (Literal["fs25", "FS25"]): The game code.
        schema (Literal["texture", "tree", "grle"]): The schema type, either "texture", "tree", or "grle".

    Returns:
        str | None: The path to the schema file if it exists, otherwise None.
    """
    normalized_game_code = game_code.lower()
    schema_file_name = f"{normalized_game_code}-{schema}-schema.json"
    schema_path = os.path.join(Paths.TEMPLATES_DIR, schema_file_name)

    if not os.path.isfile(schema_path):
        return None

    return schema_path
