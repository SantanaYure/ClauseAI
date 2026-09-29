"""Binary storage adapters."""

from app.infrastructure.storage.blob import FirebaseBlobStorage, LocalBlobStorage

__all__ = ["FirebaseBlobStorage", "LocalBlobStorage"]
