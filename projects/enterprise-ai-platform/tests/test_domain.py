import pytest
from uuid import uuid4

from enterprise_ai_platform.domain import (
    Incident,
    IncidentStatus,
    InvalidStatusTransitionError,
    ModelPrediction,
    User,
    UserRole,
)


def test_incident_is_created_open_with_trimmed_text() -> None:
    incident = Incident.create(title="  Database alert ", description="  Timeout  ")

    assert incident.title == "Database alert"
    assert incident.description == "Timeout"
    assert incident.status is IncidentStatus.OPEN


def test_empty_title_is_rejected() -> None:
    with pytest.raises(ValueError, match="title must not be empty"):
        Incident.create(title="  ", description="Timeout")


def test_resolved_incident_cannot_be_reopened() -> None:
    incident = Incident.create(title="Database alert", description="Timeout")
    investigating = incident.transition_to(IncidentStatus.INVESTIGATING)
    resolved = investigating.transition_to(IncidentStatus.RESOLVED)

    with pytest.raises(InvalidStatusTransitionError):
        resolved.transition_to(IncidentStatus.OPEN)


def test_prediction_rejects_invalid_score() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        ModelPrediction.create(
            incident_id=uuid4(),
            label="database",
            score=1.5,
            model_id="fake/model",
            model_revision="test",
            latency_ms=10,
        )


def test_user_is_created_with_normalized_email_and_role() -> None:
    user = User.create(
        email="  Operator@Example.COM ",
        password_hash="test-password-hash",
        role=UserRole.OPERATOR,
    )

    assert user.email == "operator@example.com"
    assert user.role is UserRole.OPERATOR
    assert user.is_active is True


def test_user_rejects_empty_password_hash() -> None:
    with pytest.raises(ValueError, match="password hash must not be empty"):
        User.create(email="viewer@example.com", password_hash="  ")
