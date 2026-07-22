from collections.abc import Iterable
from uuid import UUID

from .domain import Incident, IncidentNotFoundError, IncidentStatus, ModelPrediction
from .inference import IncidentClassifier
from .repository import (
    IncidentRepository,
    InMemoryIncidentRepository,
    PredictionRepository,
)


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


class IncidentClassificationService:
    def __init__(
        self,
        *,
        incidents: IncidentService,
        classifier: IncidentClassifier,
        predictions: PredictionRepository,
    ) -> None:
        self._incidents = incidents
        self._classifier = classifier
        self._predictions = predictions

    def classify(self, incident_id: UUID) -> ModelPrediction:
        incident = self._incidents.get(incident_id)
        result = self._classifier.classify(
            f"{incident.title}. {incident.description}"
        )
        prediction = ModelPrediction.create(
            incident_id=incident.id,
            label=result.label,
            score=result.score,
            model_id=result.model_id,
            model_revision=result.model_revision,
            latency_ms=result.latency_ms,
        )
        self._predictions.add(prediction)
        return prediction
