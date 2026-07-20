import os
from datetime import datetime
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .domain import (
    Incident,
    IncidentNotFoundError,
    IncidentStatus,
    InvalidStatusTransitionError,
)
from .service import IncidentService
from .database import create_session_factory
from .postgres_repository import PostgreSQLIncidentRepository


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
    if service is not None:
        app.state.incident_service = service
    elif database_url := os.getenv("DATABASE_URL"):
        session_factory = create_session_factory(database_url)
        app.state.incident_service = IncidentService(
            PostgreSQLIncidentRepository(session_factory)
        )
    else:
        app.state.incident_service = IncidentService()

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

    return app


app = create_app()
