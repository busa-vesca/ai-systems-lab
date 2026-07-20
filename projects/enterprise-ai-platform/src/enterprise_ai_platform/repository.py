from collections.abc import Iterable
from threading import Lock
from typing import Protocol
from uuid import UUID

from .domain import Incident


class IncidentRepository(Protocol):
    def is_ready(self) -> bool: ...

    def add(self, incident: Incident) -> None: ...

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]: ...

    def get(self, incident_id: UUID) -> Incident | None: ...

    def update(self, incident: Incident) -> None: ...


class InMemoryIncidentRepository:
    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._lock = Lock()

    def is_ready(self) -> bool:
        return True

    def add(self, incident: Incident) -> None:
        with self._lock:
            self._incidents[incident.id] = incident

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]:
        with self._lock:
            incidents = tuple(self._incidents.values())
            return incidents[offset : offset + limit]

    def get(self, incident_id: UUID) -> Incident | None:
        with self._lock:
            return self._incidents.get(incident_id)

    def update(self, incident: Incident) -> None:
        with self._lock:
            self._incidents[incident.id] = incident
