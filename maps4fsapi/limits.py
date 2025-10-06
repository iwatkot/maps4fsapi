"""Rate limiting and API key validation for FastAPI endpoints."""

import base64
import hashlib
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter

from maps4fsapi.config import FRONTEND_API_KEY, SECRET_SALT, is_public, logger

security = HTTPBearer()
DEFAULT_PUBLIC_LIMIT = "10/hour"
HIGH_DEMAND_PUBLIC_LIMIT = "5/hour"


def api_key_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to check if the provided API key is valid.

    Arguments:
        credentials (HTTPAuthorizationCredentials): The credentials provided in the request.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if credentials.scheme.lower() != "bearer" or not validate_api_key(credentials.credentials):
        logger.warning("Invalid or missing API key: %s", credentials.credentials)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_bearer_token(request: Request) -> str:
    """Extract the Bearer token from the request headers.

    Arguments:
        request (Request): The FastAPI request object.

    Returns:
        str: The Bearer token if present, otherwise raises an HTTPException.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    return auth_header.split(" ")[1]


def get_rate_limit_key(request: Request) -> str:
    """Get the key for rate limiting. Frontend API key bypasses limits.

    Arguments:
        request (Request): The FastAPI request object.

    Returns:
        str: A unique key for rate limiting or bypass.
    """
    try:
        token = get_bearer_token(request)
        # If it's the frontend API key, return a unique key to bypass rate limits
        if FRONTEND_API_KEY and token == FRONTEND_API_KEY:
            logger.debug("Frontend API key detected, bypassing rate limits.")
            return f"frontend_{id(request)}"
        return token
    except HTTPException:
        # If we can't get the token, fall back to IP-based limiting
        return request.client.host if request.client else "unknown"


def public_limiter(*args, **kwargs) -> Callable:
    """Decorator to apply rate limiting to public API endpoints.

    Arguments:
        *args: Positional arguments for the rate limit.
        **kwargs: Keyword arguments for the rate limit.

    Returns:
        Callable: A decorator that applies the rate limit to the function.
    """

    def wrapper(func: Callable) -> Callable:
        """Wrapper function to apply rate limiting.

        Arguments:
            func (Callable): The function to be decorated.

        Returns:
            Callable: The decorated function with rate limiting applied.
        """
        if is_public:
            return limiter.limit(*args, **kwargs)(func)
        return func

    return wrapper


limiter = Limiter(key_func=get_rate_limit_key)
dependencies = [Depends(api_key_auth)] if is_public else []


def decode_user_id(encoded: str) -> int:
    """Decode the user ID from the encoded string.

    Arguments:
        encoded (str): The encoded user ID string.
    Returns:
        int: The decoded user ID.
    """
    padded = encoded + "=" * (-len(encoded) % 4)
    return int(base64.urlsafe_b64decode(padded.encode()).decode())


def validate_api_key(api_key: str) -> bool:
    """Validate the API key.

    Arguments:
        api_key (str): The API key to validate.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # Check if it's the frontend API key
    if FRONTEND_API_KEY and api_key == FRONTEND_API_KEY:
        logger.debug("Frontend API key validated.")
        return True

    logger.debug("Validating API key: %s", "*" * len(api_key))
    try:
        encoded_id, key_hash = api_key.split(".")
        user_id = decode_user_id(encoded_id)
        expected_hash = hashlib.sha256(f"{user_id}:{SECRET_SALT}".encode()).hexdigest()[:32]
        return key_hash == expected_hash
    except Exception:
        logger.warning("Invalid API key format or decoding error.")
        return False
