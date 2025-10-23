"""User-related API endpoints for Maps4FS."""

from fastapi import APIRouter, HTTPException
from maps4fs.generator.statistics import send_survey

from maps4fsapi.components.models import UserSurveyPayload
from maps4fsapi.config import logger
from maps4fsapi.limits import dependencies

users_router = APIRouter(dependencies=dependencies)


@users_router.post("/receive_survey")
def receive_survey(payload: UserSurveyPayload):
    """Receive survey responses and process them.

    Arguments:
        payload (UserSurveyPayload): The survey responses from the user.

    Raises:
        HTTPException: If the server is not upgradable.
    """
    try:
        logger.info("Received survey data: %s", payload.model_dump())
        send_survey(payload.model_dump())
        logger.info("Survey data sent successfully.")
    except Exception as e:
        logger.error("Failed to send survey data: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process survey data.")

    return {
        "success": True,
        "message": "Survey responses received successfully.",
    }
