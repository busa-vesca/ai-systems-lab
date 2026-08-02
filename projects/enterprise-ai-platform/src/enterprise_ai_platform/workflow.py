from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class WorkflowStep(StrEnum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    POLICY_CHECKED = "policy_checked"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    TOOL_EXECUTED = "tool_executed"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    FAILED = "failed"


ALLOWED_WORKFLOW_TRANSITIONS: dict[WorkflowStep, set[WorkflowStep]] = {
    WorkflowStep.RECEIVED: {
        WorkflowStep.CLASSIFIED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.CLASSIFIED: {
        WorkflowStep.POLICY_CHECKED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.POLICY_CHECKED: {
        WorkflowStep.AWAITING_APPROVAL,
        WorkflowStep.TOOL_EXECUTED,
        WorkflowStep.SKIPPED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.AWAITING_APPROVAL: {
        WorkflowStep.APPROVED,
        WorkflowStep.SKIPPED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.APPROVED: {
        WorkflowStep.TOOL_EXECUTED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.TOOL_EXECUTED: {
        WorkflowStep.COMPLETED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.SKIPPED: {
        WorkflowStep.COMPLETED,
        WorkflowStep.FAILED,
    },
    WorkflowStep.COMPLETED: set(),
    WorkflowStep.FAILED: set(),
}


class InvalidWorkflowTransitionError(Exception):
    """The requested workflow transition is not allowed."""


class WorkflowCheckpointConflictError(Exception):
    """The workflow checkpoint version has already been saved."""


class WorkflowRunNotFoundError(Exception):
    """The requested workflow run does not exist."""


class WorkflowCannotResumeError(Exception):
    """The workflow cannot be resumed from its current state."""


class WorkflowAlreadyRunningError(Exception):
    """Another worker is already processing the workflow run."""


class WorkflowRunFailedError(Exception):
    """A workflow run failed and recorded its recovery metadata."""

    def __init__(self, *, run_id: UUID, reason: str, retryable: bool) -> None:
        super().__init__(reason)
        self.run_id = run_id
        self.reason = reason
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class WorkflowState:
    run_id: UUID
    incident_id: UUID
    step: WorkflowStep
    version: int
    created_at: datetime
    updated_at: datetime
    prediction_id: UUID | None = None
    tool_execution_id: UUID | None = None
    skipped_reason: str | None = None
    parent_run_id: UUID | None = None
    approved_by: UUID | None = None
    failure_reason: str | None = None
    retryable: bool | None = None

    @classmethod
    def start(
        cls,
        *,
        incident_id: UUID,
        parent_run_id: UUID | None = None,
    ) -> "WorkflowState":
        now = datetime.now(UTC)
        return cls(
            run_id=uuid4(),
            incident_id=incident_id,
            step=WorkflowStep.RECEIVED,
            version=1,
            created_at=now,
            updated_at=now,
            parent_run_id=parent_run_id,
        )

    def transition_to(
        self,
        step: WorkflowStep,
        *,
        prediction_id: UUID | None = None,
        tool_execution_id: UUID | None = None,
        skipped_reason: str | None = None,
        approved_by: UUID | None = None,
        failure_reason: str | None = None,
        retryable: bool | None = None,
    ) -> "WorkflowState":
        if step not in ALLOWED_WORKFLOW_TRANSITIONS[self.step]:
            raise InvalidWorkflowTransitionError(
                f"cannot transition workflow from {self.step} to {step}"
            )
        return replace(
            self,
            step=step,
            version=self.version + 1,
            updated_at=datetime.now(UTC),
            prediction_id=prediction_id or self.prediction_id,
            tool_execution_id=tool_execution_id or self.tool_execution_id,
            skipped_reason=skipped_reason or self.skipped_reason,
            approved_by=approved_by or self.approved_by,
            failure_reason=failure_reason or self.failure_reason,
            retryable=(
                retryable if retryable is not None else self.retryable
            ),
        )
