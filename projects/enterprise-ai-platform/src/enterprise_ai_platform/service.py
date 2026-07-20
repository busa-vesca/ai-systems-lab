from collections.abc import Iterable
from uuid import UUID

from .domain import Incident, IncidentNotFoundError, IncidentStatus
from .repository import IncidentRepository, InMemoryIncidentRepository


class IncidentService:
    """Application service independent of the persistence technology."""

    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self._repository = repository or InMemoryIncidentRepository()

    def is_ready(self) -> bool:
        return self._repository.is_ready()

    def create(self, *, title: str, description: str) -> Incident:
        incident = Incident.create(title=title, description=description)
        self._repository.add(incident)
        return incident

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]:
        return self._repository.list(offset=offset, limit=limit)

    def get(self, incident_id: UUID) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"incident {incident_id} was not found")
        return incident

    def update_status(self, incident_id: UUID, status: IncidentStatus) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"incident {incident_id} was not found")
        updated = incident.transition_to(status)
        self._repository.update(updated)
        return updated
