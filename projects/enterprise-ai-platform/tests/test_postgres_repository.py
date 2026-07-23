import os

import pytest
from sqlalchemy import delete

from enterprise_ai_platform.database import create_session_factory
from enterprise_ai_platform.domain import (
    Incident,
    IncidentStatus,
    ModelPrediction,
    ToolExecution,
)
from enterprise_ai_platform.models import (
    IncidentRecord,
    ModelPredictionRecord,
    ToolExecutionRecord,
)
from enterprise_ai_platform.postgres_repository import (
    PostgreSQLIncidentRepository,
    PostgreSQLPredictionRepository,
    PostgreSQLToolExecutionRepository,
)


DATABASE_URL = os.getenv("DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL is required for PostgreSQL tests"
)


def test_postgres_repository_persists_incident() -> None:
    assert DATABASE_URL is not None
    session_factory = create_session_factory(DATABASE_URL)
    incident = Incident.create(title="Database alert", description="Timeout")
    try:
        repository = PostgreSQLIncidentRepository(session_factory)
        repository.add(incident)

        stored = repository.get(incident.id)
        assert stored == incident

        investigating = incident.transition_to(IncidentStatus.INVESTIGATING)
        repository.update(investigating)
        assert repository.get(incident.id) == investigating
    finally:
        with session_factory.begin() as session:
            session.execute(
                delete(IncidentRecord).where(IncidentRecord.id == incident.id)
            )


def test_postgres_repository_persists_prediction() -> None:
    assert DATABASE_URL is not None
    session_factory = create_session_factory(DATABASE_URL)
    incident = Incident.create(title="Database alert", description="Timeout")
    prediction = ModelPrediction.create(
        incident_id=incident.id,
        label="database",
        score=0.91,
        model_id="fake/model",
        model_revision="test-revision",
        latency_ms=12.5,
    )
    try:
        PostgreSQLIncidentRepository(session_factory).add(incident)
        PostgreSQLPredictionRepository(session_factory).add(prediction)

        with session_factory() as session:
            stored = session.get(ModelPredictionRecord, prediction.id)
            assert stored is not None
            assert stored.incident_id == incident.id
            assert stored.label == "database"
            assert stored.score == 0.91
    finally:
        with session_factory.begin() as session:
            session.execute(
                delete(ModelPredictionRecord).where(
                    ModelPredictionRecord.id == prediction.id
                )
            )
            session.execute(
                delete(IncidentRecord).where(IncidentRecord.id == incident.id)
            )


def test_postgres_repository_persists_tool_execution() -> None:
    assert DATABASE_URL is not None
    session_factory = create_session_factory(DATABASE_URL)
    incident = Incident.create(title="Database alert", description="Timeout")
    prediction = ModelPrediction.create(
        incident_id=incident.id,
        label="database",
        score=0.91,
        model_id="fake/model",
        model_revision="test-revision",
        latency_ms=12.5,
    )
    execution = ToolExecution.create(
        incident_id=incident.id,
        prediction_id=prediction.id,
        tool_name="check_database_health",
        status="succeeded",
        output={"database_available": True},
        error=None,
        latency_ms=1.4,
    )
    try:
        PostgreSQLIncidentRepository(session_factory).add(incident)
        PostgreSQLPredictionRepository(session_factory).add(prediction)
        PostgreSQLToolExecutionRepository(session_factory).add(execution)

        with session_factory() as session:
            stored = session.get(ToolExecutionRecord, execution.id)
            assert stored is not None
            assert stored.incident_id == incident.id
            assert stored.prediction_id == prediction.id
            assert stored.tool_name == "check_database_health"
            assert stored.output == {"database_available": True}
    finally:
        with session_factory.begin() as session:
            session.execute(
                delete(ToolExecutionRecord).where(
                    ToolExecutionRecord.id == execution.id
                )
            )
            session.execute(
                delete(ModelPredictionRecord).where(
                    ModelPredictionRecord.id == prediction.id
                )
            )
            session.execute(
                delete(IncidentRecord).where(IncidentRecord.id == incident.id)
            )
