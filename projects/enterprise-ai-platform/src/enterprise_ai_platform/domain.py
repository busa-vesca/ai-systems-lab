from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class UserRole(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"


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


class ModelInferenceError(IncidentError):
    """The model could not produce a usable prediction."""


class UserAlreadyExistsError(Exception):
    """A user with the normalized email already exists."""


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    password_hash: str
    role: UserRole
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.VIEWER,
    ) -> "User":
        normalized_email = email.strip().lower()
        if "@" not in normalized_email:
            raise ValueError("email must be valid")
        if not password_hash.strip():
            raise ValueError("password hash must not be empty")
        return cls(
            id=uuid4(),
            email=normalized_email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.now(UTC),
        )


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


@dataclass(frozen=True, slots=True)
class ModelPrediction:
    id: UUID
    incident_id: UUID
    label: str
    score: float
    model_id: str
    model_revision: str
    latency_ms: float
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        incident_id: UUID,
        label: str,
        score: float,
        model_id: str,
        model_revision: str,
        latency_ms: float,
    ) -> "ModelPrediction":
        if not 0.0 <= score <= 1.0:
            raise ValueError("prediction score must be between 0 and 1")
        if latency_ms < 0:
            raise ValueError("prediction latency must not be negative")
        return cls(
            id=uuid4(),
            incident_id=incident_id,
            label=label,
            score=score,
            model_id=model_id,
            model_revision=model_revision,
            latency_ms=latency_ms,
            created_at=datetime.now(UTC),
        )


@dataclass(frozen=True, slots=True)
class ToolExecution:
    id: UUID
    incident_id: UUID
    prediction_id: UUID
    tool_name: str
    status: str
    output: dict[str, object]
    error: str | None
    latency_ms: float
    attempts: int
    idempotency_key: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        incident_id: UUID,
        prediction_id: UUID,
        tool_name: str,
        status: str,
        output: dict[str, object],
        error: str | None,
        latency_ms: float,
        attempts: int,
        idempotency_key: str,
    ) -> "ToolExecution":
        if status not in {"succeeded", "failed"}:
            raise ValueError("unsupported tool execution status")
        if latency_ms < 0:
            raise ValueError("tool execution latency must not be negative")
        if attempts < 1:
            raise ValueError("tool execution attempts must be at least 1")
        if not idempotency_key.strip():
            raise ValueError("idempotency key must not be empty")
        return cls(
            id=uuid4(),
            incident_id=incident_id,
            prediction_id=prediction_id,
            tool_name=tool_name,
            status=status,
            output=dict(output),
            error=error,
            latency_ms=latency_ms,
            attempts=attempts,
            idempotency_key=idempotency_key,
            created_at=datetime.now(UTC),
        )
