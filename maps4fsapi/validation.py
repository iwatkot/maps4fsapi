"""Input validation and sanitization utilities for security."""

import os
import re
from pathlib import Path
from typing import Any


class SecurityValidationError(ValueError):
    """Exception raised when security validation fails."""


def validate_filename(filename: str) -> bool:
    """Validate that a filename is safe and doesn't contain malicious patterns.

    This uses a blocklist approach - allowing most characters but blocking
    dangerous patterns that could lead to command injection or path traversal.

    Arguments:
        filename: The filename to validate

    Returns:
        True if filename is safe

    Raises:
        SecurityValidationError: If filename contains malicious patterns
    """
    if not filename:
        raise SecurityValidationError("Filename cannot be empty")

    # Check length first (prevent DOS via extremely long filenames)
    if len(filename) > 255:
        raise SecurityValidationError("Filename is too long (max 255 characters)")

    # Prevent null bytes (can bypass security checks in some systems)
    if "\0" in filename:
        raise SecurityValidationError("Filename contains null bytes")

    # Prevent path traversal
    if ".." in filename:
        raise SecurityValidationError("Filename contains path traversal pattern '..'")

    # Prevent absolute paths and directory separators
    if filename.startswith("/") or filename.startswith("\\"):
        raise SecurityValidationError("Filename cannot be an absolute path")

    if "/" in filename or "\\" in filename:
        raise SecurityValidationError("Filename cannot contain directory separators")

    # Block command injection characters
    dangerous_chars = [";", "|", "&", "$", "`", "\n", "\r", "<", ">"]
    for char in dangerous_chars:
        if char in filename:
            raise SecurityValidationError(f"Filename contains dangerous character: '{char}'")

    # Block shell variable expansion patterns
    if "${" in filename or "$(" in filename:
        raise SecurityValidationError("Filename contains shell variable expansion pattern")

    # Prevent files that start with dash (can be interpreted as command flags)
    if filename.startswith("-"):
        raise SecurityValidationError("Filename cannot start with a dash")

    return True


def safe_path_join(base_dir: str, user_path: str) -> str:
    """Safely join a base directory with a user-provided path.

    This prevents path traversal attacks by ensuring the resulting
    path is within the base directory.

    Arguments:
        base_dir: The base directory (trusted)
        user_path: User-provided path component (untrusted)

    Returns:
        Absolute path within base directory

    Raises:
        SecurityValidationError: If path traversal is detected
    """
    if not base_dir:
        raise SecurityValidationError("Base directory cannot be empty")

    if not user_path:
        raise SecurityValidationError("User path cannot be empty")

    # Prevent null bytes
    if "\0" in user_path:
        raise SecurityValidationError("Path contains null bytes")

    # Resolve to absolute paths
    base = Path(base_dir).resolve()

    # Join and resolve the user path
    try:
        target = (base / user_path).resolve()
    except (ValueError, OSError) as e:
        raise SecurityValidationError(f"Invalid path: {e}")

    # Ensure the target is within the base directory
    try:
        target.relative_to(base)
    except ValueError:
        raise SecurityValidationError(
            f"Path traversal detected: '{user_path}' escapes base directory"
        )

    return str(target)


def validate_path_exists(path: str, must_be_file: bool = True) -> bool:
    """Validate that a path exists and is of the expected type.

    Arguments:
        path: Path to validate
        must_be_file: If True, path must be a file; if False, must be a directory

    Returns:
        True if path exists and is correct type

    Raises:
        SecurityValidationError: If path doesn't exist or is wrong type
    """
    if not os.path.exists(path):
        raise SecurityValidationError(f"Path does not exist: {path}")

    if must_be_file and not os.path.isfile(path):
        raise SecurityValidationError(f"Path is not a file: {path}")

    if not must_be_file and not os.path.isdir(path):
        raise SecurityValidationError(f"Path is not a directory: {path}")

    return True


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Validate that a filename has an allowed extension.

    Arguments:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.osm', '.xml'])

    Returns:
        True if extension is allowed

    Raises:
        SecurityValidationError: If extension is not allowed
    """
    _, ext = os.path.splitext(filename.lower())

    if ext not in [e.lower() for e in allowed_extensions]:
        raise SecurityValidationError(
            f"File extension '{ext}' not allowed. "
            f"Allowed extensions: {', '.join(allowed_extensions)}"
        )

    return True


def sanitize_dict_values(data: dict[str, Any], max_string_length: int = 10000) -> dict[str, Any]:
    """Sanitize dictionary values to prevent injection attacks.

    This checks for common injection patterns in string values.

    Arguments:
        data: Dictionary to sanitize
        max_string_length: Maximum length for string values

    Returns:
        The original dictionary if validation passes

    Raises:
        SecurityValidationError: If suspicious patterns detected
    """
    dangerous_patterns = [
        r";\s*wget",
        r";\s*curl",
        r"\$\(",  # Command substitution
        r"`",  # Backtick execution
        r"\|\s*sh",
        r"\|\s*bash",
        r"eval\s*\(",
        r"exec\s*\(",
        r"__import__",
        r"subprocess",
        r"os\.system",
    ]

    pattern = re.compile("|".join(dangerous_patterns), re.IGNORECASE)

    for key, value in data.items():
        if isinstance(value, str):
            # Check string length
            if len(value) > max_string_length:
                raise SecurityValidationError(
                    f"Value for key '{key}' is too long " f"(max {max_string_length} characters)"
                )

            # Check for suspicious patterns
            if pattern.search(value):
                raise SecurityValidationError(
                    f"Suspicious pattern detected in value for key '{key}'"
                )

        elif isinstance(value, dict):
            # Recursively check nested dictionaries
            sanitize_dict_values(value, max_string_length)

    return data


# Extension-based validation (more flexible than hardcoded filenames)
ALLOWED_OSM_EXTENSIONS = {".osm", ".xml"}
ALLOWED_DEM_EXTENSIONS = {".tif", ".tiff", ".png", ".dem"}
ALLOWED_SCHEMA_EXTENSIONS = {".json"}
ALLOWED_TEMPLATE_EXTENSIONS = {".xml", ".i3d"}


def validate_file_type(
    filename: str, allowed_extensions: set[str], file_type: str = "file"
) -> bool:
    """Validate that a filename has an allowed extension for its type.

    Arguments:
        filename: Filename to validate
        allowed_extensions: Set of allowed extensions (e.g., {'.osm', '.xml'})
        file_type: Type of file (for error message)

    Returns:
        True if extension is allowed

    Raises:
        SecurityValidationError: If extension not allowed
    """
    _, ext = os.path.splitext(filename.lower())

    if not ext:
        raise SecurityValidationError(f"{file_type} '{filename}' has no extension")

    if ext not in {e.lower() for e in allowed_extensions}:
        raise SecurityValidationError(
            f"{file_type} extension '{ext}' not allowed. "
            f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
        )

    return True
