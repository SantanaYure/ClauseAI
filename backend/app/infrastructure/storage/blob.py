"""Binary storage adapters for the original documents (SPEC-002)."""

import asyncio
import hashlib
import shutil
from pathlib import Path
from typing import Any

from app.domain.interfaces.ports import StoredObject
from app.shared.exceptions import InfrastructureError


def _folder_prefix(prefix: str) -> str:
    """Prefix deletion works on whole folders only, so a typo never matches siblings."""

    if not prefix.endswith("/") or prefix.strip("/") == "":
        raise InfrastructureError("Prefixo de armazenamento inválido.", code="STORAGE_UNAVAILABLE")
    return prefix


def _stored(key: str, data: bytes) -> StoredObject:
    return StoredObject(
        storage_key=key, size_bytes=len(data), checksum_sha256=hashlib.sha256(data).hexdigest()
    )


class FirebaseBlobStorage:
    """Firebase Storage bucket; objects are private (no public URL)."""

    def __init__(self, bucket: Any) -> None:
        self._bucket = bucket

    async def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        blob = self._bucket.blob(key)
        try:
            await asyncio.to_thread(blob.upload_from_string, data, content_type=content_type)
        except Exception as exc:
            raise InfrastructureError(
                "Não foi possível armazenar o arquivo.", code="STORAGE_UNAVAILABLE"
            ) from exc
        return _stored(key, data)

    async def get(self, key: str) -> bytes:
        blob = self._bucket.blob(key)
        data: bytes = await asyncio.to_thread(blob.download_as_bytes)
        return data

    async def delete(self, key: str) -> None:
        from google.api_core.exceptions import NotFound

        blob = self._bucket.blob(key)
        try:
            await asyncio.to_thread(blob.delete)
        except NotFound:
            return

    async def delete_prefix(self, prefix: str) -> None:
        folder = _folder_prefix(prefix)
        blobs = await asyncio.to_thread(lambda: list(self._bucket.list_blobs(prefix=folder)))
        for blob in blobs:
            await self.delete(blob.name)


class LocalBlobStorage:
    """Local folder, used when PERSISTENCE_BACKEND=memory."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if self._root.resolve() not in path.parents:
            raise InfrastructureError(
                "Chave de armazenamento inválida.", code="STORAGE_UNAVAILABLE"
            )
        return path

    async def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._path(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return _stored(key, data)

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._path(key).unlink, missing_ok=True)

    async def delete_prefix(self, prefix: str) -> None:
        folder = self._path(_folder_prefix(prefix).rstrip("/"))
        await asyncio.to_thread(shutil.rmtree, folder, ignore_errors=True)
