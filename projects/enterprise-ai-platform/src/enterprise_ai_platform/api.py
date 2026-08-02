import os
from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from .auth import (
    AccessToken,
    AuthenticationNotConfiguredError,
    AuthenticationService,
    InvalidCredentialsError,
    InvalidAccessTokenError,
    InsufficientRoleError,
    JWTTokenService,
    PasswordHasher,
    RegistrationService,
)
from .database import create_session_factory
from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    InvalidStatusTransitionError,
    ModelInferenceError,
    ModelPrediction,
    User,
    UserAlreadyExistsError,
    UserRole,
)
from .inference import HuggingFaceIncidentClassifier
from .postgres_repository import (
    PostgreSQLIncidentRepository,
    PostgreSQLPredictionRepository,
    PostgreSQLToolExecutionRepository,
    PostgreSQLUserRepository,
    PostgreSQLWorkflowCheckpointRepository,
    PostgreSQLWorkflowLock,
)
from .repository import (
    InMemoryUserRepository,
    InMemoryPredictionRepository,
    InMemoryToolExecutionRepository,
    InMemoryWorkflowCheckpointRepository,
    InMemoryWorkflowLock,
    UserRepository,
)
from .service import (
    IncidentClassificationService,
    IncidentDiagnosis,
    IncidentDiagnosisService,
    IncidentService,
)
from .tools import (
    DatabaseHealthTool,
    SafeToolExecutor,
    ToolExecutionStatus,
    ToolNotAllowedError,
)
from .workflow import WorkflowStep
from .workflow import (
    WorkflowAlreadyRunningError,
    WorkflowCannotResumeError,
    WorkflowRunFailedError,
    WorkflowRunNotFoundError,
)


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)


class UserRegistration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(
        min_length=3,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+$",
    )
    password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    status: IncidentStatus
    created_at: datetime


class ModelPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    label: str
    score: float
    model_id: str
    model_revision: str
    latency_ms: float
    created_at: datetime


class ToolResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tool_name: str
    status: ToolExecutionStatus
    output: dict[str, object]
    error: str | None
    latency_ms: float
    attempts: int
    idempotency_key: str


class IncidentDiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction: ModelPredictionResponse
    tool_result: ToolResultResponse | None
    tool_execution_id: UUID | None
    skipped_reason: str | None
    workflow_run_id: UUID
    workflow_step: WorkflowStep
    workflow_version: int
    approval_required: bool
    parent_run_id: UUID | None
    approved_by: UUID | None
    failure_reason: str | None
    retryable: bool | None


def create_app(
    service: IncidentService | None = None,
    classification_service: IncidentClassificationService | None = None,
    tool_executor: SafeToolExecutor | None = None,
    user_repository: UserRepository | None = None,
    token_service: JWTTokenService | None = None,
) -> FastAPI:
    app = FastAPI(title="Enterprise AI Platform", version="0.1.0")
    bearer = HTTPBearer(auto_error=False)
    if service is not None:
        app.state.incident_service = service
        prediction_repository = InMemoryPredictionRepository()
        tool_execution_repository = InMemoryToolExecutionRepository()
        workflow_checkpoint_repository = (
            InMemoryWorkflowCheckpointRepository()
        )
        workflow_lock = InMemoryWorkflowLock()
        default_user_repository = InMemoryUserRepository()
        default_tool_executor = SafeToolExecutor(())
    elif database_url := os.getenv("DATABASE_URL"):
        session_factory = create_session_factory(database_url)
        app.state.incident_service = IncidentService(
            PostgreSQLIncidentRepository(session_factory)
        )
        prediction_repository = PostgreSQLPredictionRepository(session_factory)
        tool_execution_repository = PostgreSQLToolExecutionRepository(
            session_factory
        )
        workflow_checkpoint_repository = (
            PostgreSQLWorkflowCheckpointRepository(session_factory)
        )
        workflow_lock = PostgreSQLWorkflowLock(session_factory)
        default_user_repository = PostgreSQLUserRepository(session_factory)
        default_tool_executor = SafeToolExecutor(
            (DatabaseHealthTool(session_factory),)
        )
    else:
        app.state.incident_service = IncidentService()
        prediction_repository = InMemoryPredictionRepository()
        tool_execution_repository = InMemoryToolExecutionRepository()
        workflow_checkpoint_repository = (
            InMemoryWorkflowCheckpointRepository()
        )
        workflow_lock = InMemoryWorkflowLock()
        default_user_repository = InMemoryUserRepository()
        default_tool_executor = SafeToolExecutor(())

    app.state.classification_service = classification_service or (
        IncidentClassificationService(
            incidents=app.state.incident_service,
            classifier=HuggingFaceIncidentClassifier.from_environment(),
            predictions=prediction_repository,
        )
    )
    app.state.diagnosis_service = IncidentDiagnosisService(
        classification=app.state.classification_service,
        executor=tool_executor or default_tool_executor,
        executions=tool_execution_repository,
        checkpoints=workflow_checkpoint_repository,
        predictions=prediction_repository,
        workflow_lock=workflow_lock,
    )
    selected_user_repository = user_repository or default_user_repository
    password_hasher = PasswordHasher()
    app.state.registration_service = RegistrationService(
        users=selected_user_repository,
        passwords=password_hasher,
    )
    selected_token_service = token_service or JWTTokenService.from_environment()
    app.state.authentication_service = (
        AuthenticationService(
            users=selected_user_repository,
            passwords=password_hasher,
            tokens=selected_token_service,
        )
        if selected_token_service is not None
        else None
    )

    def get_service(request: Request) -> IncidentService:
        return request.app.state.incident_service

    def get_classification_service(
        request: Request,
    ) -> IncidentClassificationService:
        return request.app.state.classification_service

    def get_diagnosis_service(request: Request) -> IncidentDiagnosisService:
        return request.app.state.diagnosis_service

    def get_registration_service(request: Request) -> RegistrationService:
        return request.app.state.registration_service

    def get_authentication_service(request: Request) -> AuthenticationService:
        authentication = request.app.state.authentication_service
        if authentication is None:
            raise AuthenticationNotConfiguredError(
                "JWT authentication is not configured"
            )
        return authentication

    def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        authentication: AuthenticationService = Depends(
            get_authentication_service
        ),
    ) -> User:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise InvalidAccessTokenError("invalid access token")
        return authentication.current_user(credentials.credentials)

    def require_approver(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role is not UserRole.APPROVER:
            raise InsufficientRoleError("approver role is required")
        return user

    @app.exception_handler(AuthenticationNotConfiguredError)
    async def handle_authentication_not_configured(
        _request: Request, error: AuthenticationNotConfiguredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(error)},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def handle_invalid_credentials(
        _request: Request, _error: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "invalid email or password"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidAccessTokenError)
    async def handle_invalid_access_token(
        _request: Request, _error: InvalidAccessTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "invalid access token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InsufficientRoleError)
    async def handle_insufficient_role(
        _request: Request, error: InsufficientRoleError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(error)},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def handle_user_already_exists(
        _request: Request, _error: UserAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "user already exists"},
        )

    @app.exception_handler(IncidentNotFoundError)
    async def handle_not_found(
        _request: Request, error: IncidentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(InvalidStatusTransitionError)
    async def handle_invalid_transition(
        _request: Request, error: InvalidStatusTransitionError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(ModelInferenceError)
    async def handle_model_failure(
        _request: Request, error: ModelInferenceError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(error)})

    @app.exception_handler(ToolNotAllowedError)
    async def handle_tool_not_configured(
        _request: Request, _error: ToolNotAllowedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "diagnostic tool is not configured"},
        )

    @app.exception_handler(WorkflowRunNotFoundError)
    async def handle_workflow_not_found(
        _request: Request, error: WorkflowRunNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(error)})

    @app.exception_handler(WorkflowCannotResumeError)
    async def handle_workflow_cannot_resume(
        _request: Request, error: WorkflowCannotResumeError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(WorkflowAlreadyRunningError)
    async def handle_workflow_already_running(
        _request: Request, error: WorkflowAlreadyRunningError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(error)})

    @app.exception_handler(WorkflowRunFailedError)
    async def handle_workflow_run_failed(
        _request: Request, error: WorkflowRunFailedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503 if error.retryable else 500,
            content={
                "detail": error.reason,
                "workflow_run_id": str(error.run_id),
                "retryable": error.retryable,
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/auth/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def register_user(
        payload: UserRegistration,
        registration: RegistrationService = Depends(
            get_registration_service
        ),
    ) -> User:
        return registration.register(
            email=payload.email,
            password=payload.password,
        )

    @app.post("/auth/login", response_model=AccessTokenResponse)
    def login(
        payload: LoginRequest,
        authentication: AuthenticationService = Depends(
            get_authentication_service
        ),
    ) -> dict[str, str | int]:
        token: AccessToken = authentication.login(
            email=payload.email,
            password=payload.password,
        )
        return {
            "access_token": token.value,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
        }

    @app.get("/auth/me", response_model=UserResponse)
    def read_current_user(
        user: User = Depends(get_current_user),
    ) -> User:
        return user

    @app.get("/ready", response_model=None)
    def ready(
        incident_service: IncidentService = Depends(get_service),
    ) -> JSONResponse:
        if not incident_service.is_ready():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready"},
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready"},
        )

    @app.post(
        "/incidents",
        response_model=IncidentResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_incident(
        payload: IncidentCreate,
        incident_service: IncidentService = Depends(get_service),
    ) -> Incident:
        return incident_service.create(
            title=payload.title, description=payload.description
        )

    @app.get("/incidents", response_model=list[IncidentResponse])
    def list_incidents(
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        incident_service: IncidentService = Depends(get_service),
    ) -> list[Incident]:
        return list(incident_service.list(offset=offset, limit=limit))

    @app.get("/incidents/{incident_id}", response_model=IncidentResponse)
    def get_incident(
        incident_id: UUID,
        incident_service: IncidentService = Depends(get_service),
    ) -> Incident:
        return incident_service.get(incident_id)

    @app.patch("/incidents/{incident_id}", response_model=IncidentResponse)
    def update_incident(
        incident_id: UUID,
        payload: IncidentStatusUpdate,
        incident_service: IncidentService = Depends(get_service),
    ) -> Incident:
        return incident_service.update_status(incident_id, payload.status)

    @app.post(
        "/incidents/{incident_id}/classify",
        response_model=ModelPredictionResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def classify_incident(
        incident_id: UUID,
        classification: IncidentClassificationService = Depends(
            get_classification_service
        ),
    ) -> ModelPrediction:
        return classification.classify(incident_id)

    @app.post(
        "/incidents/{incident_id}/diagnose",
        response_model=IncidentDiagnosisResponse,
    )
    def diagnose_incident(
        incident_id: UUID,
        diagnosis: IncidentDiagnosisService = Depends(get_diagnosis_service),
    ) -> IncidentDiagnosis:
        return diagnosis.diagnose(incident_id)

    @app.post(
        "/workflows/{run_id}/resume",
        response_model=IncidentDiagnosisResponse,
    )
    def resume_workflow(
        run_id: UUID,
        diagnosis: IncidentDiagnosisService = Depends(get_diagnosis_service),
    ) -> IncidentDiagnosis:
        return diagnosis.resume(run_id)

    @app.post(
        "/workflows/{run_id}/approve",
        response_model=IncidentDiagnosisResponse,
    )
    def approve_workflow(
        run_id: UUID,
        diagnosis: IncidentDiagnosisService = Depends(get_diagnosis_service),
        approver: User = Depends(require_approver),
    ) -> IncidentDiagnosis:
        return diagnosis.approve(run_id, approver_id=approver.id)

    @app.post(
        "/workflows/{run_id}/retry",
        response_model=IncidentDiagnosisResponse,
    )
    def retry_workflow(
        run_id: UUID,
        diagnosis: IncidentDiagnosisService = Depends(get_diagnosis_service),
    ) -> IncidentDiagnosis:
        return diagnosis.retry(run_id)

    return app


app = create_app()
