import os
from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .database import create_session_factory
from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    InvalidStatusTransitionError,
    ModelInferenceError,
    ModelPrediction,
)
from .inference import HuggingFaceIncidentClassifier
from .postgres_repository import (
    PostgreSQLIncidentRepository,
    PostgreSQLPredictionRepository,
    PostgreSQLToolExecutionRepository,
    PostgreSQLWorkflowCheckpointRepository,
)
from .repository import (
    InMemoryPredictionRepository,
    InMemoryToolExecutionRepository,
    InMemoryWorkflowCheckpointRepository,
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
from .workflow import WorkflowCannotResumeError, WorkflowRunNotFoundError


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)


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


class IncidentDiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction: ModelPredictionResponse
    tool_result: ToolResultResponse | None
    tool_execution_id: UUID | None
    skipped_reason: str | None
    workflow_run_id: UUID
    workflow_step: WorkflowStep
    workflow_version: int


def create_app(
    service: IncidentService | None = None,
    classification_service: IncidentClassificationService | None = None,
    tool_executor: SafeToolExecutor | None = None,
) -> FastAPI:
    app = FastAPI(title="Enterprise AI Platform", version="0.1.0")
    if service is not None:
        app.state.incident_service = service
        prediction_repository = InMemoryPredictionRepository()
        tool_execution_repository = InMemoryToolExecutionRepository()
        workflow_checkpoint_repository = (
            InMemoryWorkflowCheckpointRepository()
        )
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
    )

    def get_service(request: Request) -> IncidentService:
        return request.app.state.incident_service

    def get_classification_service(
        request: Request,
    ) -> IncidentClassificationService:
        return request.app.state.classification_service

    def get_diagnosis_service(request: Request) -> IncidentDiagnosisService:
        return request.app.state.diagnosis_service

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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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

    return app


app = create_app()
