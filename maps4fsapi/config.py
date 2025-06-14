"""Configuration module for the Maps4FS API."""

import os
import shutil
import subprocess
from typing import Any

import maps4fs as mfs
from dotenv import load_dotenv

logger = mfs.Logger(level="DEBUG")

local_env = os.path.join(os.getcwd(), "local.env")
if os.path.isfile(local_env):
    logger.info("Loading local environment variables from %s", local_env)
    load_dotenv(local_env)

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
directories = [tasks_dir, archives_dir]
for directory in directories:
    if os.path.exists(directory):
        logger.info("Removing existing directory: %s", directory)
        shutil.rmtree(directory)

    os.makedirs(directory, exist_ok=True)

SECRET_SALT = os.getenv("SECRET_SALT")

is_public = check_is_public()
if is_public:
    logger.info("Running on a public server, will require API key and apply rate limiting.")
    if not SECRET_SALT:
        raise ValueError(
            "SECRET_SALT environment variable is not set. Please set it to a secure value."
        )
    logger.info("SECRET_SALT: %s", "*" * len(SECRET_SALT))
else:
    logger.info("Running on a private server, no API key or rate limiting required.")


def get_package_version(package_name: str) -> str:
    """Get the package version."""
    try:
        result = subprocess.run(
            [os.sys.executable, "-m", "pip", "show", package_name],  # type: ignore
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
        return ""
    except Exception:
        return ""


package_version = get_package_version("maps4fs")
logger.info("Maps4FS package version: %s", package_version)


class Singleton(type):
    """A metaclass for creating singleton classes."""

    _instances: dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
