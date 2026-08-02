from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager, contextmanager
from threading import Lock
from typing import Protocol
from uuid import UUID

from .domain import (
    Incident,
    ModelPrediction,
    ToolExecution,
    User,
    UserAlreadyExistsError,
)
from .workflow import (
    WorkflowAlreadyRunningError,
    WorkflowCheckpointConflictError,
    WorkflowState,
)


class IncidentRepository(Protocol):
    def is_ready(self) -> bool: ...

    def add(self, incident: Incident) -> None: ...

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]: ...

    def get(self, incident_id: UUID) -> Incident | None: ...

    def update(self, incident: Incident) -> None: ...


class UserRepository(Protocol):
    def add(self, user: User) -> None: ...

    def get_by_email(self, email: str) -> User | None: ...


class PredictionRepository(Protocol):
    def add(self, prediction: ModelPrediction) -> None: ...

    def get(self, prediction_id: UUID) -> ModelPrediction | None: ...


class ToolExecutionRepository(Protocol):
    def add(self, execution: ToolExecution) -> ToolExecution: ...

    def get(self, execution_id: UUID) -> ToolExecution | None: ...

    def get_by_idempotency_key(self, key: str) -> ToolExecution | None: ...


class WorkflowCheckpointRepository(Protocol):
    def add(self, state: WorkflowState) -> None: ...

    def get_latest(self, run_id: UUID) -> WorkflowState | None: ...


class WorkflowLock(Protocol):
    def acquire(self, run_id: UUID) -> AbstractContextManager[None]: ...


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


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users_by_email: dict[str, User] = {}
        self._lock = Lock()

    def add(self, user: User) -> None:
        with self._lock:
            if user.email in self._users_by_email:
                raise UserAlreadyExistsError(
                    f"user already exists: {user.email}"
                )
            self._users_by_email[user.email] = user

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        with self._lock:
            return self._users_by_email.get(normalized_email)


class InMemoryPredictionRepository:
    def __init__(self) -> None:
        self._predictions: dict[UUID, ModelPrediction] = {}
        self._lock = Lock()

    def add(self, prediction: ModelPrediction) -> None:
        with self._lock:
            self._predictions[prediction.id] = prediction

    def get(self, prediction_id: UUID) -> ModelPrediction | None:
        with self._lock:
            return self._predictions.get(prediction_id)


class InMemoryToolExecutionRepository:
    def __init__(self) -> None:
        self._executions: dict[UUID, ToolExecution] = {}
        self._by_idempotency_key: dict[str, UUID] = {}
        self._lock = Lock()

    def add(self, execution: ToolExecution) -> ToolExecution:
        with self._lock:
            if existing_id := self._by_idempotency_key.get(
                execution.idempotency_key
            ):
                return self._executions[existing_id]
            self._executions[execution.id] = execution
            self._by_idempotency_key[execution.idempotency_key] = execution.id
            return execution

    def get(self, execution_id: UUID) -> ToolExecution | None:
        with self._lock:
            return self._executions.get(execution_id)

    def get_by_idempotency_key(self, key: str) -> ToolExecution | None:
        with self._lock:
            execution_id = self._by_idempotency_key.get(key)
            return (
                self._executions.get(execution_id)
                if execution_id is not None
                else None
            )


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


class InMemoryWorkflowLock:
    def __init__(self) -> None:
        self._locks: dict[UUID, Lock] = {}
        self._guard = Lock()

    @contextmanager
    def acquire(self, run_id: UUID) -> Iterator[None]:
        with self._guard:
            lock = self._locks.setdefault(run_id, Lock())
        if not lock.acquire(blocking=False):
            raise WorkflowAlreadyRunningError(
                f"workflow run {run_id} is already being processed"
            )
        try:
            yield
        finally:
            lock.release()
