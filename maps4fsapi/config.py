import os
import platform

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

STORAGE_TTL = 3600
STORAGE_MAX_SIZE = 1000

security = HTTPBearer()

tasks_dir = os.path.join(os.getcwd(), "tasks")
# ! DEBUG
import shutil

if os.path.exists(tasks_dir):
    shutil.rmtree(tasks_dir)
# ! End of DEBUG

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


def get_package_version(package_name: str) -> str:
    """Get the package version of a given package.

    Returns:
        str: The package version.
    """
    current_os = platform.system().lower()
    if current_os == "windows":
        command = f"pip list 2>NUL | findstr {package_name}"
    else:
        command = f"pip list 2>/dev/null | grep {package_name}"

    response = os.popen(command).read()
    return response.replace(package_name, "").strip()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
