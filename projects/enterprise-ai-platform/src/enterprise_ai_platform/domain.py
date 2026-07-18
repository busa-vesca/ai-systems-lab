from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


ALLOWED_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.OPEN: {IncidentStatus.INVESTIGATING},
    IncidentStatus.INVESTIGATING: {IncidentStatus.OPEN, IncidentStatus.RESOLVED},
    IncidentStatus.RESOLVED: set(),
}


class IncidentError(Exception):
    """Base error for controlled incident failures."""


class IncidentNotFoundError(IncidentError):
    pass


class InvalidStatusTransitionError(IncidentError):
    pass


@dataclass(frozen=True, slots=True)
class Incident:
    id: UUID
    title: str
    description: str
    status: IncidentStatus
    created_at: datetime

    @classmethod
    def create(cls, *, title: str, description: str) -> "Incident":
        clean_title = title.strip()
        clean_description = description.strip()
        if not clean_title:
            raise ValueError("title must not be empty")
        if not clean_description:
            raise ValueError("description must not be empty")
        return cls(
            id=uuid4(),
            title=clean_title,
            description=clean_description,
            status=IncidentStatus.OPEN,
            created_at=datetime.now(UTC),
        )

    def transition_to(self, status: IncidentStatus) -> "Incident":
        if status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(
                f"cannot transition incident from {self.status} to {status}"
            )
        return replace(self, status=status)
