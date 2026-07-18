from collections.abc import Iterable
from threading import Lock
from uuid import UUID

from .domain import Incident, IncidentNotFoundError, IncidentStatus


class IncidentService:
    """Thread-safe in-memory service; replaced by PostgreSQL in Week 3."""

    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._lock = Lock()

    def create(self, *, title: str, description: str) -> Incident:
        incident = Incident.create(title=title, description=description)
        with self._lock:
            self._incidents[incident.id] = incident
        return incident

    def list(self) -> Iterable[Incident]:
        with self._lock:
            return tuple(self._incidents.values())

    def get(self, incident_id: UUID) -> Incident:
        with self._lock:
            incident = self._incidents.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"incident {incident_id} was not found")
        return incident

    def update_status(self, incident_id: UUID, status: IncidentStatus) -> Incident:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is None:
                raise IncidentNotFoundError(f"incident {incident_id} was not found")
            updated = incident.transition_to(status)
            self._incidents[incident_id] = updated
        return updated
