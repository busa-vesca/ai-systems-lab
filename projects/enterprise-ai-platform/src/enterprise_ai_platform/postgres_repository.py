from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from .database import session_scope
from .domain import Incident, IncidentStatus, ModelPrediction, ToolExecution
from .models import (
    IncidentRecord,
    ModelPredictionRecord,
    ToolExecutionRecord,
)


def _to_domain(record: IncidentRecord) -> Incident:
    return Incident(
        id=record.id,
        title=record.title,
        description=record.description,
        status=IncidentStatus(record.status),
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


class PostgreSQLToolExecutionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, execution: ToolExecution) -> None:
        with session_scope(self._session_factory) as session:
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
                    created_at=execution.created_at,
                )
            )
