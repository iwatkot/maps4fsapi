from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def api_key_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to check if the provided API key is valid.
    """
    if credentials.scheme.lower() != "bearer" or credentials.credentials != "12345":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
