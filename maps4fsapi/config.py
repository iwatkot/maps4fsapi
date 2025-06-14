"""Configuration module for the Maps4FS API."""

import os
import platform
import shutil
from typing import Any

import maps4fs as mfs

logger = mfs.Logger(level="DEBUG")

STORAGE_TTL = 3600
STORAGE_MAX_SIZE = 1000
PUBLIC_HOSTNAME_KEY = "PUBLIC_HOSTNAME"
PUBLIC_HOSTNAME_VALUE = "maps4fs"


def check_is_public() -> bool:
    """Check if the script is running on a public server.

    Returns:
        bool: True if the script is running on a public server, False otherwise.
    """
    return os.environ.get(PUBLIC_HOSTNAME_KEY) == PUBLIC_HOSTNAME_VALUE


tasks_dir = os.path.join(os.getcwd(), "tasks")
archives_dir = os.path.join(tasks_dir, "archives")
os.makedirs(archives_dir, exist_ok=True)

# ! DEBUG
if os.path.exists(tasks_dir):
    shutil.rmtree(tasks_dir)  # TODO: Remove this line in production.
if os.path.exists(archives_dir):
    shutil.rmtree(archives_dir)  # TODO: Remove this line in production.
# ! End of DEBUG

is_public = check_is_public()
if is_public:
    logger.info("Running on a public server, will require API key and apply rate limiting.")
else:
    logger.info("Running on a private server, no API key or rate limiting required.")


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


package_version = get_package_version("maps4fs")
logger.info("Maps4FS package version: %s", package_version)


class Singleton(type):
    """A metaclass for creating singleton classes."""

    _instances: dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
