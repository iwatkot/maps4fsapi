"""Configuration module for the Maps4FS API."""

import os
import subprocess
from typing import Any

import maps4fs as mfs
import maps4fs.generator.config as mfscfg
import requests
from dotenv import load_dotenv
from packaging import version

logger = mfs.Logger(level="INFO")

MFS_CUSTOM_OSM_DIR = os.path.join(mfscfg.MFS_ROOT_DIR, "custom_osm")
os.makedirs(MFS_CUSTOM_OSM_DIR, exist_ok=True)

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

FRONTEND_API_KEY = os.getenv("FRONTEND_API_KEY")
if FRONTEND_API_KEY:
    logger.info("FRONTEND_API_KEY: %s", "*" * len(FRONTEND_API_KEY))


def get_package_version(package_name: str) -> str:
    """Get the package version.

    Arguments:
        package_name (str): The name of the package to check.

    Returns:
        str: The version string of the package or an empty string if not found.
    """
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


def get_package_latest_version(package_name: str) -> str:
    """Get the latest package version from PyPI.

    Arguments:
        package_name (str): The name of the package to check.

    Returns:
        str | None: The latest version string if available, otherwise an empty string.
    """
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]
        return latest_version
    except Exception:
        return ""


def is_latest_version(package_name: str) -> bool:
    """Check if the current version is the latest version.

    Arguments:
        current_version (str): The current version string.
        latest_version (str): The latest version string.

    Returns:
        bool: True if the current version is the latest, False otherwise.
    """
    current_version = get_package_version(package_name)
    latest_version = get_package_latest_version(package_name)

    if not current_version or not latest_version:
        return True

    try:
        return version.parse(current_version) >= version.parse(latest_version)
    except Exception:
        return True


def version_status(package_name: str) -> dict[str, bool | str]:
    """Get the version status of the package.

    Arguments:
        package_name (str): The name of the package to check.

    Returns:
        dict[str, bool | str]: A dictionary containing the current version, latest version,
        and whether the current version is the latest.
    """
    current_version = get_package_version(package_name)
    latest_version = get_package_latest_version(package_name)
    return {
        "current_version": current_version,
        "latest_version": latest_version,
        "is_latest": is_latest_version(package_name),
    }


package_version = get_package_version("maps4fs")
logger.info("Maps4FS package version: %s", package_version)


class Singleton(type):
    """A metaclass for creating singleton classes."""

    _instances: dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
