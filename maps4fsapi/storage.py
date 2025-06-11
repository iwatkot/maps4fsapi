import os
import shutil
from typing import NamedTuple

from cachetools import TTLCache

from maps4fsapi.config import STORAGE_MAX_SIZE, STORAGE_TTL


class StorageEntry(NamedTuple):
    """A storage entry that contains information about a stored asset.

    Attributes:
        success (bool): Indicates whether the storage operation was successful.
        description (str): A description containing details about the status.
        directory (str): The directory where the asset is stored.
        file_path (str): The path to the file within the directory.
    """

    success: bool
    description: str
    directory: str
    file_path: str


class CleanableTTLCache(TTLCache):
    """A TTLCache that will remove related directory when the entry is removed."""

    def __delitem__(self, key):
        """Remove the related directory when the entry is deleted."""
        entry = self.get(key)
        if entry and entry.directory:
            entry_directory = entry.directory
            if os.path.isdir(entry_directory):
                shutil.rmtree(entry_directory, ignore_errors=True)
        super().__delitem__(key)


class Storage:
    def __init__(self):
        self.cache = CleanableTTLCache(maxsize=STORAGE_MAX_SIZE, ttl=STORAGE_TTL)

    def add_entry(self, key: str, entry: StorageEntry) -> None:
        self.cache[key] = entry

    def create_entry(
        self, key: str, success: bool, description: str, directory: str, file_path: str
    ) -> None:
        entry = StorageEntry(
            success=success, description=description, directory=directory, file_path=file_path
        )
        self.add_entry(key, entry)

    def get_entry(self, key: str) -> StorageEntry | None:
        return self.cache.get(key)

    def pop_entry(self, key: str) -> StorageEntry | None:
        return self.cache.pop(key, None)
