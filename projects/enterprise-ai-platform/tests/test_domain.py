import pytest

from enterprise_ai_platform.domain import (
    Incident,
    IncidentStatus,
    InvalidStatusTransitionError,
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
