from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    ModelPrediction,
    ToolExecution,
)
from .inference import IncidentClassifier
from .repository import (
    IncidentRepository,
    InMemoryIncidentRepository,
    PredictionRepository,
    ToolExecutionRepository,
)
from .tools import SafeToolExecutor, ToolCall, ToolResult


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


@dataclass(frozen=True, slots=True)
class IncidentDiagnosis:
    prediction: ModelPrediction
    tool_result: ToolResult | None
    tool_execution_id: UUID | None
    skipped_reason: str | None


class IncidentDiagnosisService:
    MIN_TOOL_CONFIDENCE = 0.60
    TOOL_BY_LABEL = {
        "database": "check_database_health",
    }

    def __init__(
        self,
        *,
        classification: IncidentClassificationService,
        executor: SafeToolExecutor,
        executions: ToolExecutionRepository,
    ) -> None:
        self._classification = classification
        self._executor = executor
        self._executions = executions

    def diagnose(self, incident_id: UUID) -> IncidentDiagnosis:
        prediction = self._classification.classify(incident_id)
        if prediction.score < self.MIN_TOOL_CONFIDENCE:
            return IncidentDiagnosis(
                prediction=prediction,
                tool_result=None,
                tool_execution_id=None,
                skipped_reason=(
                    f"prediction confidence {prediction.score:.3f} is below "
                    f"tool threshold {self.MIN_TOOL_CONFIDENCE:.3f}"
                ),
            )

        tool_name = self.TOOL_BY_LABEL.get(prediction.label)
        if tool_name is None:
            return IncidentDiagnosis(
                prediction=prediction,
                tool_result=None,
                tool_execution_id=None,
                skipped_reason=(
                    f"no diagnostic tool configured for label: {prediction.label}"
                ),
            )

        tool_result = self._executor.execute(
            ToolCall(name=tool_name, arguments={})
        )
        execution = ToolExecution.create(
            incident_id=prediction.incident_id,
            prediction_id=prediction.id,
            tool_name=tool_result.tool_name,
            status=tool_result.status.value,
            output=tool_result.output,
            error=tool_result.error,
            latency_ms=tool_result.latency_ms,
            attempts=tool_result.attempts,
        )
        self._executions.add(execution)
        return IncidentDiagnosis(
            prediction=prediction,
            tool_result=tool_result,
            tool_execution_id=execution.id,
            skipped_reason=None,
        )
