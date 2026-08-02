from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from .database import session_scope
from .domain import (
    Incident,
    IncidentStatus,
    ModelPrediction,
    ToolExecution,
    User,
    UserAlreadyExistsError,
    UserRole,
)
from .models import (
    IncidentRecord,
    ModelPredictionRecord,
    ToolExecutionRecord,
    UserRecord,
    WorkflowCheckpointRecord,
)
from .workflow import (
    WorkflowAlreadyRunningError,
    WorkflowCheckpointConflictError,
    WorkflowState,
    WorkflowStep,
)


def _advisory_lock_key(run_id: UUID) -> int:
    return run_id.int % (2**63 - 1)


def _to_domain(record: IncidentRecord) -> Incident:
    return Incident(
        id=record.id,
        title=record.title,
        description=record.description,
        status=IncidentStatus(record.status),
        created_at=record.created_at,
    )


def _user_to_domain(record: UserRecord) -> User:
    return User(
        id=record.id,
        email=record.email,
        password_hash=record.password_hash,
        role=UserRole(record.role),
        is_active=record.is_active,
        created_at=record.created_at,
    )


class PostgreSQLUserRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, user: User) -> None:
        try:
            with session_scope(self._session_factory) as session:
                session.add(
                    UserRecord(
                        id=user.id,
                        email=user.email,
                        password_hash=user.password_hash,
                        role=user.role.value,
                        is_active=user.is_active,
                        created_at=user.created_at,
                    )
                )
        except IntegrityError as error:
            raise UserAlreadyExistsError(
                f"user already exists: {user.email}"
            ) from error

    def get_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        with session_scope(self._session_factory) as session:
            record = session.scalar(
                select(UserRecord).where(
                    UserRecord.email == normalized_email
                )
            )
            return _user_to_domain(record) if record is not None else None


def _prediction_to_domain(record: ModelPredictionRecord) -> ModelPrediction:
    return ModelPrediction(
        id=record.id,
        incident_id=record.incident_id,
        label=record.label,
        score=record.score,
        model_id=record.model_id,
        model_revision=record.model_revision,
        latency_ms=record.latency_ms,
        created_at=record.created_at,
    )


def _execution_to_domain(record: ToolExecutionRecord) -> ToolExecution:
    return ToolExecution(
        id=record.id,
        incident_id=record.incident_id,
        prediction_id=record.prediction_id,
        tool_name=record.tool_name,
        status=record.status,
        output=record.output,
        error=record.error,
        latency_ms=record.latency_ms,
        attempts=record.attempts,
        idempotency_key=record.idempotency_key,
        created_at=record.created_at,
    )


class PostgreSQLIncidentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def is_ready(self) -> bool:
        try:
            with session_scope(self._session_factory) as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def add(self, incident: Incident) -> None:
        with session_scope(self._session_factory) as session:
            session.add(
                IncidentRecord(
                    id=incident.id,
                    title=incident.title,
                    description=incident.description,
                    status=incident.status.value,
                    created_at=incident.created_at,
                )
            )

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]:
        with session_scope(self._session_factory) as session:
            records = session.scalars(
                select(IncidentRecord)
                .order_by(IncidentRecord.created_at)
                .offset(offset)
                .limit(limit)
            ).all()
            return tuple(_to_domain(record) for record in records)

    def get(self, incident_id: UUID) -> Incident | None:
        with session_scope(self._session_factory) as session:
            record = session.get(IncidentRecord, incident_id)
            return _to_domain(record) if record is not None else None

    def update(self, incident: Incident) -> None:
        with session_scope(self._session_factory) as session:
            record = session.get(IncidentRecord, incident.id)
            if record is None:
                return
            record.title = incident.title
            record.description = incident.description
            record.status = incident.status.value
            record.created_at = incident.created_at


class PostgreSQLPredictionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, prediction: ModelPrediction) -> None:
        with session_scope(self._session_factory) as session:
            session.add(
                ModelPredictionRecord(
                    id=prediction.id,
                    incident_id=prediction.incident_id,
                    label=prediction.label,
                    score=prediction.score,
                    model_id=prediction.model_id,
                    model_revision=prediction.model_revision,
                    latency_ms=prediction.latency_ms,
                    created_at=prediction.created_at,
                )
            )

    def get(self, prediction_id: UUID) -> ModelPrediction | None:
        with session_scope(self._session_factory) as session:
            record = session.get(ModelPredictionRecord, prediction_id)
            return (
                _prediction_to_domain(record) if record is not None else None
            )


class PostgreSQLToolExecutionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, execution: ToolExecution) -> ToolExecution:
        with session_scope(self._session_factory) as session:
            existing = session.scalar(
                select(ToolExecutionRecord).where(
                    ToolExecutionRecord.idempotency_key
                    == execution.idempotency_key
                )
            )
            if existing is not None:
                return _execution_to_domain(existing)
            session.add(
                ToolExecutionRecord(
                    id=execution.id,
                    incident_id=execution.incident_id,
                    prediction_id=execution.prediction_id,
                    tool_name=execution.tool_name,
                    status=execution.status,
                    output=execution.output,
                    error=execution.error,
                    latency_ms=execution.latency_ms,
                    attempts=execution.attempts,
                    idempotency_key=execution.idempotency_key,
                    created_at=execution.created_at,
                )
            )
            return execution

    def get(self, execution_id: UUID) -> ToolExecution | None:
        with session_scope(self._session_factory) as session:
            record = session.get(ToolExecutionRecord, execution_id)
            return _execution_to_domain(record) if record is not None else None

    def get_by_idempotency_key(self, key: str) -> ToolExecution | None:
        with session_scope(self._session_factory) as session:
            record = session.scalar(
                select(ToolExecutionRecord).where(
                    ToolExecutionRecord.idempotency_key == key
                )
            )
            return _execution_to_domain(record) if record is not None else None


def _checkpoint_to_domain(
    record: WorkflowCheckpointRecord,
) -> WorkflowState:
    return WorkflowState(
        run_id=record.run_id,
        incident_id=record.incident_id,
        step=WorkflowStep(record.step),
        version=record.version,
        created_at=record.created_at,
        updated_at=record.updated_at,
        prediction_id=record.prediction_id,
        tool_execution_id=record.tool_execution_id,
        skipped_reason=record.skipped_reason,
        parent_run_id=record.parent_run_id,
        failure_reason=record.failure_reason,
        retryable=record.retryable,
    )


class PostgreSQLWorkflowCheckpointRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, state: WorkflowState) -> None:
        try:
            with session_scope(self._session_factory) as session:
                session.add(
                    WorkflowCheckpointRecord(
                        run_id=state.run_id,
                        incident_id=state.incident_id,
                        step=state.step.value,
                        version=state.version,
                        created_at=state.created_at,
                        updated_at=state.updated_at,
                        prediction_id=state.prediction_id,
                        tool_execution_id=state.tool_execution_id,
                        skipped_reason=state.skipped_reason,
                        parent_run_id=state.parent_run_id,
                        failure_reason=state.failure_reason,
                        retryable=state.retryable,
                    )
                )
        except IntegrityError as error:
            raise WorkflowCheckpointConflictError(
                f"workflow checkpoint {state.run_id} version "
                f"{state.version} already exists"
            ) from error

    def get_latest(self, run_id: UUID) -> WorkflowState | None:
        with session_scope(self._session_factory) as session:
            record = session.scalar(
                select(WorkflowCheckpointRecord)
                .where(WorkflowCheckpointRecord.run_id == run_id)
                .order_by(WorkflowCheckpointRecord.version.desc())
                .limit(1)
            )
            return (
                _checkpoint_to_domain(record) if record is not None else None
            )


class PostgreSQLWorkflowLock:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @contextmanager
    def acquire(self, run_id: UUID) -> Iterator[None]:
        lock_key = _advisory_lock_key(run_id)
        with self._session_factory() as session:
            acquired = bool(
                session.scalar(
                    text("SELECT pg_try_advisory_lock(:lock_key)"),
                    {"lock_key": lock_key},
                )
            )
            if not acquired:
                raise WorkflowAlreadyRunningError(
                    f"workflow run {run_id} is already being processed"
                )
            try:
                yield
            finally:
                session.execute(
                    text("SELECT pg_advisory_unlock(:lock_key)"),
                    {"lock_key": lock_key},
                )
