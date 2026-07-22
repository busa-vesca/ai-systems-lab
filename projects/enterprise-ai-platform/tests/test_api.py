from fastapi.testclient import TestClient

from enterprise_ai_platform.api import create_app
from enterprise_ai_platform.domain import ModelInferenceError
from enterprise_ai_platform.inference import ClassificationResult, IncidentClassifier
from enterprise_ai_platform.repository import InMemoryPredictionRepository
from enterprise_ai_platform.service import (
    IncidentClassificationService,
    IncidentService,
)


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


def test_health_and_readiness() -> None:
    client = make_client()

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


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
