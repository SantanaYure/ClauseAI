"""A tiny in-memory stand-in for the synchronous Firestore client used by the adapters.

It supports only what the repositories and the purge script call: documents,
subcollections, `where(filter=FieldFilter)`, `order_by`, `limit`, `select` and `stream`.
It also records every query filter, so tests can prove the owner filter is applied.
"""

import operator
from collections.abc import Callable
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "<": operator.lt,
    ">": operator.gt,
}


class FakeSnapshot:
    def __init__(self, reference: "FakeDocument", data: dict[str, Any] | None) -> None:
        self.reference = reference
        self.id = reference.id
        self.exists = data is not None
        self._data = data

    def to_dict(self) -> dict[str, Any] | None:
        return dict(self._data) if self._data is not None else None


class FakeDocument:
    def __init__(self, store: dict[str, dict[str, Any]], path: str) -> None:
        self._store = store
        self.path = path
        self.id = path.rsplit("/", 1)[-1]

    def set(self, data: dict[str, Any]) -> None:
        self._store[self.path] = dict(data)

    def get(self) -> FakeSnapshot:
        return FakeSnapshot(self, self._store.get(self.path))

    def delete(self) -> None:
        self._store.pop(self.path, None)

    def collection(self, name: str) -> "FakeCollection":
        return FakeCollection(self._store, f"{self.path}/{name}")


class FakeQuery:
    def __init__(self, collection: "FakeCollection") -> None:
        self._collection = collection
        self._filters: list[FieldFilter] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._fields: list[str] | None = None

    def where(self, *, filter: FieldFilter) -> "FakeQuery":
        self._filters.append(filter)
        self._collection.client_filters.append(filter)
        return self

    def order_by(self, field: str, direction: str = "ASCENDING") -> "FakeQuery":
        self._order = (field, direction == "DESCENDING")
        return self

    def limit(self, count: int) -> "FakeQuery":
        self._limit = count
        return self

    def select(self, fields: list[str]) -> "FakeQuery":
        self._fields = fields
        return self

    def stream(self) -> list[FakeSnapshot]:
        snapshots = [s for s in self._collection.stream() if self._matches(s.to_dict() or {})]
        if self._order:
            field, descending = self._order
            snapshots.sort(key=lambda s: (s.to_dict() or {})[field], reverse=descending)
        if self._limit is not None:
            snapshots = snapshots[: self._limit]
        if self._fields is not None:
            fields = self._fields
            snapshots = [
                FakeSnapshot(
                    s.reference, {k: v for k, v in (s.to_dict() or {}).items() if k in fields}
                )
                for s in snapshots
            ]
        return snapshots

    def _matches(self, data: dict[str, Any]) -> bool:
        for item in self._filters:
            if item.field_path not in data:
                return False  # Firestore never matches a missing field
            if not _OPERATORS[item.op_string](data[item.field_path], item.value):
                return False
        return True


class FakeCollection:
    def __init__(self, store: dict[str, dict[str, Any]], path: str) -> None:
        self._store = store
        self._path = path
        self.client_filters: list[FieldFilter] = []

    def document(self, document_id: str) -> FakeDocument:
        return FakeDocument(self._store, f"{self._path}/{document_id}")

    def _children(self) -> list[str]:
        prefix = f"{self._path}/"
        return [
            key for key in self._store if key.startswith(prefix) and "/" not in key[len(prefix) :]
        ]

    def list_documents(self) -> list[FakeDocument]:
        return [FakeDocument(self._store, key) for key in self._children()]

    def stream(self) -> list[FakeSnapshot]:
        return [FakeDocument(self._store, key).get() for key in self._children()]

    def where(self, *, filter: FieldFilter) -> FakeQuery:
        return FakeQuery(self).where(filter=filter)

    def order_by(self, field: str, direction: str = "ASCENDING") -> FakeQuery:
        return FakeQuery(self).order_by(field, direction)

    def select(self, fields: list[str]) -> FakeQuery:
        return FakeQuery(self).select(fields)


class FakeFirestoreClient:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def collection(self, name: str) -> FakeCollection:
        return FakeCollection(self.store, name)
