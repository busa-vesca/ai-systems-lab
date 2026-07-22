import os

import pytest
from sqlalchemy import delete

from enterprise_ai_platform.database import create_session_factory
from enterprise_ai_platform.domain import Incident, IncidentStatus, ModelPrediction
from enterprise_ai_platform.models import IncidentRecord, ModelPredictionRecord
from enterprise_ai_platform.postgres_repository import (
    PostgreSQLIncidentRepository,
    PostgreSQLPredictionRepository,
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
