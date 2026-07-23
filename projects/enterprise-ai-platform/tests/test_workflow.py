from uuid import uuid4

import pytest

from enterprise_ai_platform.workflow import (
    InvalidWorkflowTransitionError,
    WorkflowState,
    WorkflowStep,
)


def test_workflow_starts_at_received() -> None:
    incident_id = uuid4()

    state = WorkflowState.start(incident_id=incident_id)

    assert state.incident_id == incident_id
    assert state.step is WorkflowStep.RECEIVED
    assert state.version == 1


def test_read_only_tool_path_reaches_completed() -> None:
    state = WorkflowState.start(incident_id=uuid4())

    for step in (
        WorkflowStep.CLASSIFIED,
        WorkflowStep.POLICY_CHECKED,
        WorkflowStep.TOOL_EXECUTED,
        WorkflowStep.COMPLETED,
    ):
        state = state.transition_to(step)

    assert state.step is WorkflowStep.COMPLETED
    assert state.version == 5


def test_write_tool_can_wait_for_approval() -> None:
    state = WorkflowState.start(incident_id=uuid4())

    for step in (
        WorkflowStep.CLASSIFIED,
        WorkflowStep.POLICY_CHECKED,
        WorkflowStep.AWAITING_APPROVAL,
        WorkflowStep.APPROVED,
        WorkflowStep.TOOL_EXECUTED,
        WorkflowStep.COMPLETED,
    ):
        state = state.transition_to(step)

    assert state.step is WorkflowStep.COMPLETED
    assert state.version == 7


def test_invalid_transition_is_rejected() -> None:
    state = WorkflowState.start(incident_id=uuid4())

    with pytest.raises(InvalidWorkflowTransitionError):
        state.transition_to(WorkflowStep.COMPLETED)
