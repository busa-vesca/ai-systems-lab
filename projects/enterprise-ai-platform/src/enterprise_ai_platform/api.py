from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    InvalidStatusTransitionError,
)
from .service import IncidentService


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


def create_app(service: IncidentService | None = None) -> FastAPI:
    app = FastAPI(title="Enterprise AI Platform", version="0.1.0")
    app.state.incident_service = service or IncidentService()

    def get_service(request: Request) -> IncidentService:
        return request.app.state.incident_service

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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

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
        incident_service: IncidentService = Depends(get_service),
    ) -> list[Incident]:
        return list(incident_service.list())

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

    return app


app = create_app()
