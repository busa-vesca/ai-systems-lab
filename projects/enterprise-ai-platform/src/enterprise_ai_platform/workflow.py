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


@dataclass(frozen=True, slots=True)
class WorkflowState:
    run_id: UUID
    incident_id: UUID
    step: WorkflowStep
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def start(cls, *, incident_id: UUID) -> "WorkflowState":
        now = datetime.now(UTC)
        return cls(
            run_id=uuid4(),
            incident_id=incident_id,
            step=WorkflowStep.RECEIVED,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def transition_to(self, step: WorkflowStep) -> "WorkflowState":
        if step not in ALLOWED_WORKFLOW_TRANSITIONS[self.step]:
            raise InvalidWorkflowTransitionError(
                f"cannot transition workflow from {self.step} to {step}"
            )
        return replace(
            self,
            step=step,
            version=self.version + 1,
            updated_at=datetime.now(UTC),
        )
