from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    ModelInferenceError,
    ModelPrediction,
    ToolExecution,
)
from .inference import IncidentClassifier
from .repository import (
    IncidentRepository,
    InMemoryIncidentRepository,
    PredictionRepository,
    ToolExecutionRepository,
    WorkflowCheckpointRepository,
    WorkflowLock,
)
from .tools import (
    SafeToolExecutor,
    ToolCall,
    ToolExecutionStatus,
    ToolResult,
)
from .workflow import (
    WorkflowCannotResumeError,
    WorkflowRunFailedError,
    WorkflowRunNotFoundError,
    WorkflowState,
    WorkflowStep,
)


class IncidentService:
    """Application service independent of the persistence technology."""

    def __init__(self, repository: IncidentRepository | None = None) -> None:
        self._repository = repository or InMemoryIncidentRepository()

    def is_ready(self) -> bool:
        return self._repository.is_ready()

    def create(self, *, title: str, description: str) -> Incident:
        incident = Incident.create(title=title, description=description)
        self._repository.add(incident)
        return incident

    def list(self, *, offset: int = 0, limit: int = 50) -> Iterable[Incident]:
        return self._repository.list(offset=offset, limit=limit)

    def get(self, incident_id: UUID) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"incident {incident_id} was not found")
        return incident

    def update_status(self, incident_id: UUID, status: IncidentStatus) -> Incident:
        incident = self._repository.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(f"incident {incident_id} was not found")
        updated = incident.transition_to(status)
        self._repository.update(updated)
        return updated


class IncidentClassificationService:
    def __init__(
        self,
        *,
        incidents: IncidentService,
        classifier: IncidentClassifier,
        predictions: PredictionRepository,
    ) -> None:
        self._incidents = incidents
        self._classifier = classifier
        self._predictions = predictions

    def classify(self, incident_id: UUID) -> ModelPrediction:
        incident = self._incidents.get(incident_id)
        result = self._classifier.classify(
            f"{incident.title}. {incident.description}"
        )
        prediction = ModelPrediction.create(
            incident_id=incident.id,
            label=result.label,
            score=result.score,
            model_id=result.model_id,
            model_revision=result.model_revision,
            latency_ms=result.latency_ms,
        )
        self._predictions.add(prediction)
        return prediction


@dataclass(frozen=True, slots=True)
class IncidentDiagnosis:
    prediction: ModelPrediction
    tool_result: ToolResult | None
    tool_execution_id: UUID | None
    skipped_reason: str | None
    workflow_run_id: UUID
    workflow_step: WorkflowStep
    workflow_version: int
    approval_required: bool
    parent_run_id: UUID | None
    failure_reason: str | None
    retryable: bool | None


class IncidentDiagnosisService:
    MIN_TOOL_CONFIDENCE = 0.60
    TOOL_BY_LABEL = {
        "database": "check_database_health",
    }

    def __init__(
        self,
        *,
        classification: IncidentClassificationService,
        executor: SafeToolExecutor,
        executions: ToolExecutionRepository,
        checkpoints: WorkflowCheckpointRepository,
        predictions: PredictionRepository,
        workflow_lock: WorkflowLock,
        tool_by_label: dict[str, str] | None = None,
    ) -> None:
        self._classification = classification
        self._executor = executor
        self._executions = executions
        self._checkpoints = checkpoints
        self._predictions = predictions
        self._workflow_lock = workflow_lock
        self._tool_by_label = tool_by_label or self.TOOL_BY_LABEL

    def _transition(
        self,
        state: WorkflowState,
        step: WorkflowStep,
        prediction_id: UUID | None = None,
        tool_execution_id: UUID | None = None,
        skipped_reason: str | None = None,
        failure_reason: str | None = None,
        retryable: bool | None = None,
    ) -> WorkflowState:
        next_state = state.transition_to(
            step,
            prediction_id=prediction_id,
            tool_execution_id=tool_execution_id,
            skipped_reason=skipped_reason,
            failure_reason=failure_reason,
            retryable=retryable,
        )
        self._checkpoints.add(next_state)
        return next_state

    def _result(
        self,
        *,
        state: WorkflowState,
        prediction: ModelPrediction,
        tool_result: ToolResult | None = None,
        tool_execution_id: UUID | None = None,
        skipped_reason: str | None = None,
    ) -> IncidentDiagnosis:
        return IncidentDiagnosis(
            prediction=prediction,
            tool_result=tool_result,
            tool_execution_id=tool_execution_id,
            skipped_reason=skipped_reason,
            workflow_run_id=state.run_id,
            workflow_step=state.step,
            workflow_version=state.version,
            approval_required=(
                state.step is WorkflowStep.AWAITING_APPROVAL
            ),
            parent_run_id=state.parent_run_id,
            failure_reason=state.failure_reason,
            retryable=state.retryable,
        )

    def diagnose(self, incident_id: UUID) -> IncidentDiagnosis:
        state = WorkflowState.start(incident_id=incident_id)
        self._checkpoints.add(state)
        with self._workflow_lock.acquire(state.run_id):
            return self._continue(state)

    def resume(self, run_id: UUID) -> IncidentDiagnosis:
        with self._workflow_lock.acquire(run_id):
            state = self._checkpoints.get_latest(run_id)
            if state is None:
                raise WorkflowRunNotFoundError(
                    f"workflow run {run_id} was not found"
                )
            if state.step is WorkflowStep.FAILED:
                raise WorkflowCannotResumeError(
                    f"workflow run {run_id} is already failed"
                )
            return self._continue(state)

    def approve(self, run_id: UUID) -> IncidentDiagnosis:
        with self._workflow_lock.acquire(run_id):
            state = self._checkpoints.get_latest(run_id)
            if state is None:
                raise WorkflowRunNotFoundError(
                    f"workflow run {run_id} was not found"
                )
            if state.step is not WorkflowStep.AWAITING_APPROVAL:
                raise WorkflowCannotResumeError(
                    f"workflow run {run_id} is not awaiting approval"
                )
            state = self._transition(state, WorkflowStep.APPROVED)
            return self._continue(state)

    def retry(self, run_id: UUID) -> IncidentDiagnosis:
        with self._workflow_lock.acquire(run_id):
            failed_state = self._checkpoints.get_latest(run_id)
            if failed_state is None:
                raise WorkflowRunNotFoundError(
                    f"workflow run {run_id} was not found"
                )
            if (
                failed_state.step is not WorkflowStep.FAILED
                or failed_state.retryable is not True
            ):
                raise WorkflowCannotResumeError(
                    f"workflow run {run_id} is not retryable"
                )
            retry_state = WorkflowState.start(
                incident_id=failed_state.incident_id,
                parent_run_id=run_id,
            )
            self._checkpoints.add(retry_state)

        with self._workflow_lock.acquire(retry_state.run_id):
            return self._continue(retry_state)

    def _require_prediction(self, state: WorkflowState) -> ModelPrediction:
        if state.prediction_id is None:
            raise WorkflowCannotResumeError(
                f"workflow run {state.run_id} has no saved prediction"
            )
        prediction = self._predictions.get(state.prediction_id)
        if prediction is None:
            raise WorkflowCannotResumeError(
                f"prediction {state.prediction_id} was not found"
            )
        return prediction

    def _saved_tool_result(self, state: WorkflowState) -> ToolResult | None:
        if state.tool_execution_id is None:
            return None
        execution = self._executions.get(state.tool_execution_id)
        if execution is None:
            raise WorkflowCannotResumeError(
                f"tool execution {state.tool_execution_id} was not found"
            )
        return ToolResult(
            tool_name=execution.tool_name,
            status=ToolExecutionStatus(execution.status),
            output=execution.output,
            error=execution.error,
            latency_ms=execution.latency_ms,
            attempts=execution.attempts,
            idempotency_key=execution.idempotency_key,
        )

    def _continue(self, state: WorkflowState) -> IncidentDiagnosis:
        try:
            if state.step is WorkflowStep.RECEIVED:
                prediction = self._classification.classify(state.incident_id)
                state = self._transition(
                    state,
                    WorkflowStep.CLASSIFIED,
                    prediction_id=prediction.id,
                )
            else:
                prediction = self._require_prediction(state)

            if state.step is WorkflowStep.CLASSIFIED:
                state = self._transition(state, WorkflowStep.POLICY_CHECKED)

            if state.step is WorkflowStep.POLICY_CHECKED:
                if prediction.score < self.MIN_TOOL_CONFIDENCE:
                    reason = (
                        f"prediction confidence {prediction.score:.3f} is below "
                        f"tool threshold {self.MIN_TOOL_CONFIDENCE:.3f}"
                    )
                    state = self._transition(
                        state,
                        WorkflowStep.SKIPPED,
                        skipped_reason=reason,
                    )
                elif (
                    tool_name := self._tool_by_label.get(prediction.label)
                ) is None:
                    reason = (
                        "no diagnostic tool configured for label: "
                        f"{prediction.label}"
                    )
                    state = self._transition(
                        state,
                        WorkflowStep.SKIPPED,
                        skipped_reason=reason,
                    )
                else:
                    if self._executor.requires_approval(tool_name):
                        state = self._transition(
                            state,
                            WorkflowStep.AWAITING_APPROVAL,
                        )

            if state.step is WorkflowStep.AWAITING_APPROVAL:
                return self._result(state=state, prediction=prediction)

            if state.step in {
                WorkflowStep.POLICY_CHECKED,
                WorkflowStep.APPROVED,
            }:
                tool_name = self._tool_by_label[prediction.label]
                idempotency_key = f"{state.run_id}:{tool_name}"
                execution = self._executions.get_by_idempotency_key(
                    idempotency_key
                )
                if execution is None:
                    tool_result = self._executor.execute(
                        ToolCall(
                            name=tool_name,
                            arguments={},
                            idempotency_key=idempotency_key,
                        )
                    )
                    execution = self._executions.add(
                        ToolExecution.create(
                            incident_id=prediction.incident_id,
                            prediction_id=prediction.id,
                            tool_name=tool_result.tool_name,
                            status=tool_result.status.value,
                            output=tool_result.output,
                            error=tool_result.error,
                            latency_ms=tool_result.latency_ms,
                            attempts=tool_result.attempts,
                            idempotency_key=tool_result.idempotency_key,
                        )
                    )
                if execution.status == ToolExecutionStatus.FAILED.value:
                    reason = execution.error or "tool execution failed"
                    retryable = self._executor.is_retry_safe(tool_name)
                    state = self._transition(
                        state,
                        WorkflowStep.FAILED,
                        tool_execution_id=execution.id,
                        failure_reason=reason,
                        retryable=retryable,
                    )
                    raise WorkflowRunFailedError(
                        run_id=state.run_id,
                        reason=reason,
                        retryable=retryable,
                    )
                state = self._transition(
                    state,
                    WorkflowStep.TOOL_EXECUTED,
                    tool_execution_id=execution.id,
                )

            if state.step in {
                WorkflowStep.TOOL_EXECUTED,
                WorkflowStep.SKIPPED,
            }:
                state = self._transition(state, WorkflowStep.COMPLETED)

            if state.step is not WorkflowStep.COMPLETED:
                raise WorkflowCannotResumeError(
                    f"cannot continue workflow from {state.step}"
                )

            return self._result(
                state=state,
                prediction=prediction,
                tool_result=self._saved_tool_result(state),
                tool_execution_id=state.tool_execution_id,
                skipped_reason=state.skipped_reason,
            )
        except WorkflowRunFailedError:
            raise
        except Exception as error:
            if state.step not in {
                WorkflowStep.COMPLETED,
                WorkflowStep.FAILED,
            }:
                retryable = isinstance(error, ModelInferenceError)
                state = self._transition(
                    state,
                    WorkflowStep.FAILED,
                    failure_reason=str(error),
                    retryable=retryable,
                )
                raise WorkflowRunFailedError(
                    run_id=state.run_id,
                    reason=str(error),
                    retryable=retryable,
                ) from error
            raise
