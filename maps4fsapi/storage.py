"""Storage management module for maps4fsapi."""

from typing import NamedTuple

from cachetools import TTLCache

from maps4fsapi.config import STORAGE_MAX_SIZE, STORAGE_TTL, Singleton, logger


class StorageEntry(NamedTuple):
    """A storage entry that contains information about a stored asset.

    Attributes:
        success (bool): Indicates whether the storage operation was successful.
        description (str): A description containing details about the status.
        directory (str): The directory where the asset is stored.
        file_path (str): The path to the file within the directory.
        previews (list[str] | None): A list of preview file paths for the asset.
    """

    success: bool
    description: str
    directory: str | None = None
    file_path: str | None = None
    previews: list[str] = []


class Storage(metaclass=Singleton):
    """A singleton class that manages storage of assets with a TTL cache."""

    def __init__(self):
        self.cache = TTLCache(maxsize=STORAGE_MAX_SIZE, ttl=STORAGE_TTL)

    def add_entry(self, key: str, entry: StorageEntry) -> None:
        """Add an entry to the storage cache.

        Arguments:
            key (str): The unique key for the entry.
            entry (StorageEntry): The storage entry to be added.
        """
        logger.debug("Adding entry to storage: %s", key)
        self.cache[key] = entry

    def create_entry(
        self,
        key: str,
        success: bool,
        description: str,
        directory: str,
        file_path: str,
        previews: list[str] | None = None,
    ) -> None:
        """Create and add a new storage entry.

        Arguments:
            key (str): The unique key for the entry.
            success (bool): Indicates whether the storage operation was successful.
            description (str): A description containing details about the status.
            directory (str): The directory where the asset is stored.
            file_path (str): The path to the file within the directory.
            previews (list[str] | None): A list of preview file paths for the asset.
        """
        previews = previews or []

        entry = StorageEntry(
            success=success,
            description=description,
            directory=directory,
            file_path=file_path,
            previews=previews,
        )
        self.add_entry(key, entry)

    def get_entry(self, key: str) -> StorageEntry | None:
        """Retrieve an entry from the storage cache.

        Arguments:
            key (str): The unique key for the entry.

        Returns:
            StorageEntry | None: The storage entry if found, otherwise None.
        """
        logger.debug("Retrieving entry from storage: %s", key)
        return self.cache.get(key)

    def pop_entry(self, key: str) -> StorageEntry | None:
        """Remove and return an entry from the storage cache.

        Arguments:
            key (str): The unique key for the entry.

        Returns:
            StorageEntry | None: The storage entry if found and removed, otherwise None.
        """
        return self.cache.pop(key, None)

    def remove_entry(self, key: str) -> None:
        """Remove an entry from the storage.

        Arguments:
            key (str): The unique key for the entry.
        """
        logger.debug("Removing entry from storage: %s", key)
        if key in self.cache:
            self.pop_entry(key)
