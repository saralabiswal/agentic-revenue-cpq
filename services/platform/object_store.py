"""Object store provider boundary.

Author: Sarala Biswal
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from services.platform.config import PlatformConfig, get_platform_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OBJECT_STORE_PATH = PROJECT_ROOT / "app_data" / "objects"


class ObjectStore(Protocol):
    """Interface for binary object storage."""

    def put_object(self, key: str, data: bytes) -> str:
        """Write bytes to an object key and return the normalized key."""

    def get_object(self, key: str) -> bytes:
        """Read bytes from an object key."""

    def delete_object(self, key: str) -> None:
        """Delete an object key when present."""

    def exists(self, key: str) -> bool:
        """Return whether an object key exists."""


class LocalFilesystemObjectStore:
    """Object store backed by the local filesystem."""

    def __init__(self, root_path: str | Path | None = None) -> None:
        """Create a local object store rooted under app_data by default."""
        configured_path = root_path or os.getenv("OBJECT_STORE_PATH")
        self.root_path = Path(configured_path) if configured_path else DEFAULT_OBJECT_STORE_PATH
        self.root_path.mkdir(parents=True, exist_ok=True)

    def put_object(self, key: str, data: bytes) -> str:
        """Write bytes to an object key and return the normalized key."""
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self._normalize_key(key)

    def get_object(self, key: str) -> bytes:
        """Read bytes from an object key."""
        path = self._path_for_key(key)
        if not path.exists():
            raise FileNotFoundError(f"Object not found: {key}")
        return path.read_bytes()

    def delete_object(self, key: str) -> None:
        """Delete an object key when present."""
        path = self._path_for_key(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        """Return whether an object key exists."""
        return self._path_for_key(key).exists()

    def _path_for_key(self, key: str) -> Path:
        """Resolve a safe object path under the configured root."""
        normalized_key = self._normalize_key(key)
        path = (self.root_path / normalized_key).resolve()
        root = self.root_path.resolve()
        if root != path and root not in path.parents:
            raise ValueError(f"Object key escapes local object store root: {key}")
        return path

    def _normalize_key(self, key: str) -> str:
        """Normalize object keys to relative POSIX-style paths."""
        normalized = key.strip().lstrip("/")
        if not normalized or normalized in {".", ".."} or ".." in Path(normalized).parts:
            raise ValueError("Object key must be a relative path within the object store.")
        return normalized


class ProviderObjectStore:
    """Stub for cloud object stores that are not implemented yet."""

    def __init__(self, provider_name: str) -> None:
        """Store provider name for clear runtime errors."""
        self._provider_name = provider_name

    def put_object(self, key: str, data: bytes) -> str:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def get_object(self, key: str) -> bytes:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def delete_object(self, key: str) -> None:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def exists(self, key: str) -> bool:
        """Raise until the provider SDK integration is intentionally implemented."""
        raise self._not_implemented()

    def _not_implemented(self) -> NotImplementedError:
        """Build the clear stub error."""
        return NotImplementedError(
            f"OBJECT_STORE_PROVIDER={self._provider_name!r} is a stub. "
            "Use OBJECT_STORE_PROVIDER=local_fs for local runs."
        )


def create_object_store(config: PlatformConfig | None = None) -> ObjectStore:
    """Create the configured object store."""
    platform_config = config or get_platform_config()
    provider = platform_config.object_store_provider
    if provider == "local_fs":
        return LocalFilesystemObjectStore()
    if provider in {"oci_object_storage", "gcs", "s3_compatible"}:
        return ProviderObjectStore(provider)

    raise ValueError(
        f"Unsupported OBJECT_STORE_PROVIDER={provider!r}. "
        "Supported values: local_fs, oci_object_storage, gcs, s3_compatible."
    )
