from collections.abc import Iterable
from threading import Lock
from typing import Protocol
from uuid import UUID

from .domain import Incident, ModelPrediction, ToolExecution
from .workflow import WorkflowCheckpointConflictError, WorkflowState


class IncidentRepository(Protocol):
    def is_ready(self) -> bool: ...

    def add(self, incident: Incident) -> None: ...

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]: ...

    def get(self, incident_id: UUID) -> Incident | None: ...

    def update(self, incident: Incident) -> None: ...


class PredictionRepository(Protocol):
    def add(self, prediction: ModelPrediction) -> None: ...


class ToolExecutionRepository(Protocol):
    def add(self, execution: ToolExecution) -> None: ...


class WorkflowCheckpointRepository(Protocol):
    def add(self, state: WorkflowState) -> None: ...

    def get_latest(self, run_id: UUID) -> WorkflowState | None: ...


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


class InMemoryPredictionRepository:
    def __init__(self) -> None:
        self._predictions: dict[UUID, ModelPrediction] = {}
        self._lock = Lock()

    def add(self, prediction: ModelPrediction) -> None:
        with self._lock:
            self._predictions[prediction.id] = prediction


class InMemoryToolExecutionRepository:
    def __init__(self) -> None:
        self._executions: dict[UUID, ToolExecution] = {}
        self._lock = Lock()

    def add(self, execution: ToolExecution) -> None:
        with self._lock:
            self._executions[execution.id] = execution


class InMemoryWorkflowCheckpointRepository:
    def __init__(self) -> None:
        self._checkpoints: dict[tuple[UUID, int], WorkflowState] = {}
        self._lock = Lock()

    def add(self, state: WorkflowState) -> None:
        key = (state.run_id, state.version)
        with self._lock:
            if key in self._checkpoints:
                raise WorkflowCheckpointConflictError(
                    f"workflow checkpoint {state.run_id} version "
                    f"{state.version} already exists"
                )
            self._checkpoints[key] = state

    def get_latest(self, run_id: UUID) -> WorkflowState | None:
        with self._lock:
            states = [
                state
                for (stored_run_id, _), state in self._checkpoints.items()
                if stored_run_id == run_id
            ]
            return max(states, key=lambda state: state.version, default=None)
