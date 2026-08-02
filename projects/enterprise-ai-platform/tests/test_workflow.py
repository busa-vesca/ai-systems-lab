from uuid import uuid4

import pytest

from enterprise_ai_platform.repository import (
    InMemoryWorkflowCheckpointRepository,
    InMemoryWorkflowLock,
)
from enterprise_ai_platform.workflow import (
    InvalidWorkflowTransitionError,
    WorkflowCheckpointConflictError,
    WorkflowAlreadyRunningError,
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
    approver_id = uuid4()

    for step in (
        WorkflowStep.CLASSIFIED,
        WorkflowStep.POLICY_CHECKED,
        WorkflowStep.AWAITING_APPROVAL,
    ):
        state = state.transition_to(step)
    state = state.transition_to(
        WorkflowStep.APPROVED,
        approved_by=approver_id,
    )
    state = state.transition_to(WorkflowStep.TOOL_EXECUTED)
    state = state.transition_to(WorkflowStep.COMPLETED)

    assert state.step is WorkflowStep.COMPLETED
    assert state.version == 7
    assert state.approved_by == approver_id


def test_invalid_transition_is_rejected() -> None:
    state = WorkflowState.start(incident_id=uuid4())

    with pytest.raises(InvalidWorkflowTransitionError):
        state.transition_to(WorkflowStep.COMPLETED)


def test_checkpoint_repository_returns_latest_version() -> None:
    repository = InMemoryWorkflowCheckpointRepository()
    received = WorkflowState.start(incident_id=uuid4())
    classified = received.transition_to(WorkflowStep.CLASSIFIED)

    repository.add(received)
    repository.add(classified)

    assert repository.get_latest(received.run_id) == classified


def test_duplicate_checkpoint_version_is_rejected() -> None:
    repository = InMemoryWorkflowCheckpointRepository()
    state = WorkflowState.start(incident_id=uuid4())
    repository.add(state)

    with pytest.raises(WorkflowCheckpointConflictError):
        repository.add(state)


def test_workflow_lock_rejects_parallel_processing() -> None:
    workflow_lock = InMemoryWorkflowLock()
    run_id = uuid4()

    with workflow_lock.acquire(run_id):
        with pytest.raises(WorkflowAlreadyRunningError):
            with workflow_lock.acquire(run_id):
                pass

    with workflow_lock.acquire(run_id):
        pass
