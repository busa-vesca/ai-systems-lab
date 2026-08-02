from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from enterprise_ai_platform.api import create_app
from enterprise_ai_platform.auth import JWTTokenService
from enterprise_ai_platform.domain import (
    ModelInferenceError,
    ModelPrediction,
    ToolExecution,
    UserRole,
)
from enterprise_ai_platform.inference import ClassificationResult, IncidentClassifier
from enterprise_ai_platform.repository import (
    InMemoryPredictionRepository,
    InMemoryToolExecutionRepository,
    InMemoryUserRepository,
    InMemoryWorkflowCheckpointRepository,
    InMemoryWorkflowLock,
)
from enterprise_ai_platform.service import (
    IncidentClassificationService,
    IncidentDiagnosisService,
    IncidentService,
)
from enterprise_ai_platform.tools import SafeToolExecutor, ToolCall
from enterprise_ai_platform.workflow import WorkflowState, WorkflowStep


class FakeClassifier:
    def classify(self, _text: str) -> ClassificationResult:
        return ClassificationResult(
            label="database",
            score=0.91,
            model_id="fake/model",
            model_revision="test-revision",
            latency_ms=12.5,
        )


class FailingClassifier:
    def classify(self, _text: str) -> ClassificationResult:
        raise ModelInferenceError("model inference failed")


class FlakyClassifier:
    def __init__(self) -> None:
        self.calls = 0

    def classify(self, _text: str) -> ClassificationResult:
        self.calls += 1
        if self.calls == 1:
            raise ModelInferenceError("temporary model failure")
        return ClassificationResult(
            label="database",
            score=0.91,
            model_id="fake/model",
            model_revision="test-revision",
            latency_ms=12.5,
        )


class LabelClassifier:
    def __init__(self, label: str, score: float = 0.91) -> None:
        self._label = label
        self._score = score

    def classify(self, _text: str) -> ClassificationResult:
        return ClassificationResult(
            label=self._label,
            score=self._score,
            model_id="fake/model",
            model_revision="test-revision",
            latency_ms=12.5,
        )


class FakeDatabaseHealthTool:
    name = "check_database_health"
    retry_safe = True
    requires_approval = False

    def run(
        self,
        _arguments: dict[str, object],
        *,
        idempotency_key: str,
    ) -> dict[str, object]:
        del idempotency_key
        return {"database_available": True}


def make_client() -> TestClient:
    return TestClient(create_app(IncidentService()))


def make_classification_client(classifier: IncidentClassifier) -> TestClient:
    incidents = IncidentService()
    classification = IncidentClassificationService(
        incidents=incidents,
        classifier=classifier,
        predictions=InMemoryPredictionRepository(),
    )
    return TestClient(create_app(incidents, classification))


def make_diagnosis_client(
    classifier: IncidentClassifier,
    executor: SafeToolExecutor | None = None,
) -> TestClient:
    incidents = IncidentService()
    classification = IncidentClassificationService(
        incidents=incidents,
        classifier=classifier,
        predictions=InMemoryPredictionRepository(),
    )
    selected_executor = executor or SafeToolExecutor(
        (FakeDatabaseHealthTool(),)
    )
    return TestClient(
        create_app(incidents, classification, selected_executor)
    )


def test_health_and_readiness() -> None:
    client = make_client()

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_user_registration_hashes_password_and_hides_hash() -> None:
    users = InMemoryUserRepository()
    client = TestClient(
        create_app(IncidentService(), user_repository=users)
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "Viewer@Example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "viewer@example.com"
    assert response.json()["role"] == UserRole.VIEWER
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    stored = users.get_by_email("viewer@example.com")
    assert stored is not None
    assert stored.password_hash.startswith("$argon2")


def test_duplicate_user_registration_returns_controlled_409() -> None:
    users = InMemoryUserRepository()
    client = TestClient(
        create_app(IncidentService(), user_repository=users)
    )
    payload = {
        "email": "viewer@example.com",
        "password": "correct-horse-battery-staple",
    }

    assert client.post("/auth/register", json=payload).status_code == 201
    duplicate = client.post("/auth/register", json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json() == {"detail": "user already exists"}


def test_public_registration_cannot_choose_privileged_role() -> None:
    client = make_client()

    response = client.post(
        "/auth/register",
        json={
            "email": "attacker@example.com",
            "password": "correct-horse-battery-staple",
            "role": "approver",
        },
    )

    assert response.status_code == 422


def test_registered_user_can_login_and_receive_jwt() -> None:
    users = InMemoryUserRepository()
    tokens = JWTTokenService(secret="test-secret-that-is-at-least-32-characters")
    client = TestClient(
        create_app(
            IncidentService(),
            user_repository=users,
            token_service=tokens,
        )
    )
    credentials = {
        "email": "viewer@example.com",
        "password": "correct-horse-battery-staple",
    }
    client.post("/auth/register", json=credentials)

    response = client.post("/auth/login", json=credentials)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 1_800
    claims = tokens.decode(response.json()["access_token"])
    assert claims["role"] == "viewer"
    assert claims["sub"] == str(users.get_by_email("viewer@example.com").id)


def test_wrong_password_returns_generic_401() -> None:
    users = InMemoryUserRepository()
    tokens = JWTTokenService(secret="test-secret-that-is-at-least-32-characters")
    client = TestClient(
        create_app(
            IncidentService(),
            user_repository=users,
            token_service=tokens,
        )
    )
    client.post(
        "/auth/register",
        json={
            "email": "viewer@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "viewer@example.com",
            "password": "definitely-the-wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid email or password"}


def test_login_without_jwt_secret_returns_controlled_503() -> None:
    client = make_client()

    response = client.post(
        "/auth/login",
        json={
            "email": "viewer@example.com",
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "JWT authentication is not configured"}


def test_incident_lifecycle() -> None:
    client = make_client()
    created = client.post(
        "/incidents",
        json={"title": "Database alert", "description": "Connection timeout"},
    )

    assert created.status_code == 201
    incident_id = created.json()["id"]
    assert client.get("/incidents").json()[0]["id"] == incident_id
    assert client.get(f"/incidents/{incident_id}").status_code == 200

    updated = client.patch(
        f"/incidents/{incident_id}", json={"status": "investigating"}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "investigating"


def test_incident_list_is_paginated() -> None:
    client = make_client()
    for title in ("First", "Second"):
        client.post(
            "/incidents", json={"title": title, "description": "Failure"}
        )

    response = client.get("/incidents?offset=1&limit=1")

    assert response.status_code == 200
    assert [incident["title"] for incident in response.json()] == ["Second"]


def test_missing_incident_returns_404() -> None:
    client = make_client()

    response = client.get("/incidents/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_invalid_transition_returns_409() -> None:
    client = make_client()
    incident_id = client.post(
        "/incidents", json={"title": "Alert", "description": "Failure"}
    ).json()["id"]

    response = client.patch(
        f"/incidents/{incident_id}", json={"status": "resolved"}
    )

    assert response.status_code == 409


def test_incident_is_classified_without_loading_real_model() -> None:
    client = make_classification_client(FakeClassifier())
    incident_id = client.post(
        "/incidents",
        json={
            "title": "Database connection failure",
            "description": "PostgreSQL timed out",
        },
    ).json()["id"]

    response = client.post(f"/incidents/{incident_id}/classify")

    assert response.status_code == 201
    assert response.json()["incident_id"] == incident_id
    assert response.json()["label"] == "database"
    assert response.json()["score"] == 0.91
    assert response.json()["latency_ms"] == 12.5


def test_model_failure_returns_controlled_502() -> None:
    client = make_classification_client(FailingClassifier())
    incident_id = client.post(
        "/incidents", json={"title": "Alert", "description": "Failure"}
    ).json()["id"]

    response = client.post(f"/incidents/{incident_id}/classify")

    assert response.status_code == 502
    assert response.json() == {"detail": "model inference failed"}


def test_retryable_model_failure_starts_linked_workflow_run() -> None:
    classifier = FlakyClassifier()
    client = make_diagnosis_client(classifier)
    incident_id = client.post(
        "/incidents",
        json={"title": "Model alert", "description": "Temporary failure"},
    ).json()["id"]

    failed = client.post(f"/incidents/{incident_id}/diagnose")

    assert failed.status_code == 503
    assert failed.json()["detail"] == "temporary model failure"
    assert failed.json()["retryable"] is True
    failed_run_id = failed.json()["workflow_run_id"]

    retried = client.post(f"/workflows/{failed_run_id}/retry")

    assert retried.status_code == 200
    assert retried.json()["workflow_step"] == "completed"
    assert retried.json()["parent_run_id"] == failed_run_id
    assert retried.json()["workflow_run_id"] != failed_run_id
    assert classifier.calls == 2


class RecoveringDatabaseTool:
    name = "check_database_health"
    retry_safe = True
    requires_approval = False

    def __init__(self) -> None:
        self.calls = 0
        self.keys: list[str] = []

    def run(
        self,
        _arguments: dict[str, object],
        *,
        idempotency_key: str,
    ) -> dict[str, object]:
        self.calls += 1
        self.keys.append(idempotency_key)
        if self.calls == 1:
            raise SQLAlchemyError("temporary database failure")
        return {"database_available": True}


def test_retryable_tool_failure_uses_new_run_and_idempotency_key() -> None:
    tool = RecoveringDatabaseTool()
    executor = SafeToolExecutor((tool,), max_attempts=1)
    client = make_diagnosis_client(FakeClassifier(), executor)
    incident_id = client.post(
        "/incidents",
        json={"title": "Database alert", "description": "Timeout"},
    ).json()["id"]

    failed = client.post(f"/incidents/{incident_id}/diagnose")

    assert failed.status_code == 503
    assert failed.json()["retryable"] is True
    failed_run_id = failed.json()["workflow_run_id"]

    retried = client.post(f"/workflows/{failed_run_id}/retry")

    assert retried.status_code == 200
    assert retried.json()["workflow_step"] == "completed"
    assert retried.json()["parent_run_id"] == failed_run_id
    assert tool.calls == 2
    assert len(set(tool.keys)) == 2


def test_database_incident_runs_allowed_diagnostic_tool() -> None:
    client = make_diagnosis_client(LabelClassifier("database"))
    incident_id = client.post(
        "/incidents",
        json={
            "title": "Database connection failure",
            "description": "PostgreSQL timed out",
        },
    ).json()["id"]

    response = client.post(f"/incidents/{incident_id}/diagnose")

    assert response.status_code == 200
    assert response.json()["prediction"]["label"] == "database"
    assert response.json()["tool_result"]["tool_name"] == (
        "check_database_health"
    )
    assert response.json()["tool_result"]["status"] == "succeeded"
    assert response.json()["tool_result"]["attempts"] == 1
    assert response.json()["tool_result"]["output"] == {
        "database_available": True
    }
    assert response.json()["tool_result"]["idempotency_key"].endswith(
        ":check_database_health"
    )
    assert response.json()["tool_execution_id"] is not None
    assert response.json()["skipped_reason"] is None
    assert response.json()["workflow_step"] == "completed"
    assert response.json()["workflow_version"] == 5
    assert response.json()["workflow_run_id"] is not None
    assert response.json()["approval_required"] is False


def test_incident_without_configured_diagnostic_tool_is_skipped() -> None:
    client = make_diagnosis_client(LabelClassifier("network"))
    incident_id = client.post(
        "/incidents",
        json={"title": "Network alert", "description": "Connection lost"},
    ).json()["id"]

    response = client.post(f"/incidents/{incident_id}/diagnose")

    assert response.status_code == 200
    assert response.json()["prediction"]["label"] == "network"
    assert response.json()["tool_result"] is None
    assert response.json()["tool_execution_id"] is None
    assert response.json()["skipped_reason"] == (
        "no diagnostic tool configured for label: network"
    )
    assert response.json()["workflow_step"] == "completed"
    assert response.json()["workflow_version"] == 5


def test_low_confidence_prediction_does_not_run_tool() -> None:
    client = make_diagnosis_client(LabelClassifier("database", score=0.379))
    incident_id = client.post(
        "/incidents",
        json={
            "title": "DNS resolution failure",
            "description": "Cannot resolve the upstream hostname",
        },
    ).json()["id"]

    response = client.post(f"/incidents/{incident_id}/diagnose")

    assert response.status_code == 200
    assert response.json()["prediction"]["label"] == "database"
    assert response.json()["prediction"]["score"] == 0.379
    assert response.json()["tool_result"] is None
    assert response.json()["tool_execution_id"] is None
    assert response.json()["skipped_reason"] == (
        "prediction confidence 0.379 is below tool threshold 0.600"
    )
    assert response.json()["workflow_step"] == "completed"
    assert response.json()["workflow_version"] == 5


def test_workflow_resumes_after_policy_checkpoint_without_reclassification() -> None:
    incidents = IncidentService()
    incident = incidents.create(title="Database alert", description="Timeout")
    predictions = InMemoryPredictionRepository()
    prediction = ModelPrediction.create(
        incident_id=incident.id,
        label="database",
        score=0.91,
        model_id="fake/model",
        model_revision="test-revision",
        latency_ms=12.5,
    )
    predictions.add(prediction)
    checkpoints = InMemoryWorkflowCheckpointRepository()
    state = WorkflowState.start(incident_id=incident.id)
    checkpoints.add(state)
    state = state.transition_to(
        WorkflowStep.CLASSIFIED,
        prediction_id=prediction.id,
    )
    checkpoints.add(state)
    state = state.transition_to(WorkflowStep.POLICY_CHECKED)
    checkpoints.add(state)
    executions = InMemoryToolExecutionRepository()
    diagnosis = IncidentDiagnosisService(
        classification=IncidentClassificationService(
            incidents=incidents,
            classifier=FailingClassifier(),
            predictions=predictions,
        ),
        executor=SafeToolExecutor((FakeDatabaseHealthTool(),)),
        executions=executions,
        checkpoints=checkpoints,
        predictions=predictions,
        workflow_lock=InMemoryWorkflowLock(),
    )

    result = diagnosis.resume(state.run_id)

    assert result.workflow_step is WorkflowStep.COMPLETED
    assert result.workflow_version == 5
    assert result.prediction.id == prediction.id
    assert result.tool_result is not None
    assert result.tool_result.output == {"database_available": True}


class FakeSensitiveTool:
    name = "restart_service"
    retry_safe = False
    requires_approval = True

    def __init__(self) -> None:
        self.calls = 0
        self._processed_keys: set[str] = set()

    def run(
        self,
        _arguments: dict[str, object],
        *,
        idempotency_key: str,
    ) -> dict[str, object]:
        if idempotency_key not in self._processed_keys:
            self._processed_keys.add(idempotency_key)
            self.calls += 1
        return {"restart_requested": True}


def test_sensitive_tool_waits_for_approval_before_execution() -> None:
    incidents = IncidentService()
    incident = incidents.create(title="Service failure", description="Restart")
    predictions = InMemoryPredictionRepository()
    executions = InMemoryToolExecutionRepository()
    checkpoints = InMemoryWorkflowCheckpointRepository()
    tool = FakeSensitiveTool()
    diagnosis = IncidentDiagnosisService(
        classification=IncidentClassificationService(
            incidents=incidents,
            classifier=LabelClassifier("infrastructure"),
            predictions=predictions,
        ),
        executor=SafeToolExecutor((tool,)),
        executions=executions,
        checkpoints=checkpoints,
        predictions=predictions,
        workflow_lock=InMemoryWorkflowLock(),
        tool_by_label={"infrastructure": "restart_service"},
    )

    waiting = diagnosis.diagnose(incident.id)

    assert waiting.workflow_step is WorkflowStep.AWAITING_APPROVAL
    assert waiting.workflow_version == 4
    assert waiting.approval_required is True
    assert waiting.tool_result is None
    assert tool.calls == 0

    completed = diagnosis.approve(waiting.workflow_run_id)

    assert completed.workflow_step is WorkflowStep.COMPLETED
    assert completed.workflow_version == 7
    assert completed.approval_required is False
    assert completed.tool_result is not None
    assert completed.tool_result.output == {"restart_requested": True}
    assert completed.tool_result.idempotency_key == (
        f"{waiting.workflow_run_id}:restart_service"
    )
    assert tool.calls == 1


def test_sensitive_tool_deduplicates_repeated_idempotency_key() -> None:
    tool = FakeSensitiveTool()
    executor = SafeToolExecutor((tool,))
    call = ToolCall(
        name="restart_service",
        arguments={},
        idempotency_key="workflow-123:restart_service",
    )

    first = executor.execute(call)
    second = executor.execute(call)

    assert first.output == second.output
    assert first.idempotency_key == second.idempotency_key
    assert tool.calls == 1


def test_execution_repository_returns_original_for_duplicate_key() -> None:
    repository = InMemoryToolExecutionRepository()
    incident_id = uuid4()
    prediction_id = uuid4()
    key = "workflow-123:restart_service"
    first = ToolExecution.create(
        incident_id=incident_id,
        prediction_id=prediction_id,
        tool_name="restart_service",
        status="succeeded",
        output={"restart_requested": True},
        error=None,
        latency_ms=2.0,
        attempts=1,
        idempotency_key=key,
    )
    duplicate = ToolExecution.create(
        incident_id=incident_id,
        prediction_id=prediction_id,
        tool_name="restart_service",
        status="succeeded",
        output={"restart_requested": True},
        error=None,
        latency_ms=3.0,
        attempts=1,
        idempotency_key=key,
    )

    assert repository.add(first) == first
    assert repository.add(duplicate) == first
