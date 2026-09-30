"""Firebase Admin initialization shared by the API and the maintenance scripts."""

from typing import Any

from app.shared.config.settings import Settings

FIREBASE_APP_NAME = "clauseai"


def firebase_app(settings: Settings) -> Any:
    """Return the process-wide Firebase app, initializing it on first use."""

    import firebase_admin
    from firebase_admin import credentials

    if FIREBASE_APP_NAME in firebase_admin._apps:  # already initialized in this process
        return firebase_admin.get_app(FIREBASE_APP_NAME)
    if settings.firebase_credentials_path:
        credential = credentials.Certificate(settings.firebase_credentials_path)
    else:
        credential = credentials.Certificate(
            {
                "type": "service_account",
                "project_id": settings.firebase_project_id,
                "client_email": settings.firebase_client_email,
                "private_key": settings.firebase_private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
    options = (
        {"storageBucket": settings.firebase_storage_bucket}
        if settings.firebase_storage_bucket
        else None
    )
    return firebase_admin.initialize_app(credential, options, name=FIREBASE_APP_NAME)
