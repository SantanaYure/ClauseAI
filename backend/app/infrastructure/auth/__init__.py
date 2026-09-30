"""Identity adapters: Firebase Auth (anonymous accounts) and a local fake."""

from app.infrastructure.auth.fake import FakeAccountRemover, FakeIdentityVerifier
from app.infrastructure.auth.firebase import FirebaseAccountRemover, FirebaseIdentityVerifier

__all__ = [
    "FakeAccountRemover",
    "FakeIdentityVerifier",
    "FirebaseAccountRemover",
    "FirebaseIdentityVerifier",
]
