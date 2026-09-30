"""Blob key layout: every original lives under its owner's folder, so erasing an
owner's data is a single prefix deletion (LGPD)."""


def owner_prefix(owner_id: str) -> str:
    return f"owners/{owner_id}/"


def policy_prefix(owner_id: str, policy_id: str) -> str:
    return f"{owner_prefix(owner_id)}policies/{policy_id}/"


def document_key(owner_id: str, policy_id: str, document_id: str, extension: str) -> str:
    return f"{policy_prefix(owner_id, policy_id)}{document_id}.{extension}"
