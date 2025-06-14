from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter

from maps4fsapi.config import is_public

security = HTTPBearer()


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


def get_bearer_token(request: Request) -> str:
    """
    Extract the Bearer token from the request headers.

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


limiter = Limiter(key_func=get_bearer_token)
dependencies = [Depends(api_key_auth)] if is_public else []
