from fastapi.testclient import TestClient

from enterprise_ai_platform.api import create_app
from enterprise_ai_platform.service import IncidentService


def make_client() -> TestClient:
    return TestClient(create_app(IncidentService()))


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
