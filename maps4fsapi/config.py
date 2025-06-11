from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

STORAGE_TTL = 3600
STORAGE_MAX_SIZE = 1000

security = HTTPBearer()

is_public = False  # TODO: Change to correct check if API is public or not.


def api_key_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to check if the provided API key is valid.
    """
    # TODO: Remember to add actual API key validation logic here.
    if credentials.scheme.lower() != "bearer" or credentials.credentials != "12345":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
