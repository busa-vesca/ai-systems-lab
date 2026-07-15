from fastapi.testclient import TestClient

from vision_inference_api.main import app


def test_predict_returns_file_metadata() -> None:
    client = TestClient(app)
    content = b"\xff\xd8\xff\xe0fake-jpeg-bytes"
    response = client.post(
        "/predict", files={"file": ("cat.jpg", content, "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "cat.jpg",
        "content_type": "image/jpeg",
        "size_bytes": len(content),
        "status": "received",
    }


def test_predict_without_file_returns_422() -> None:
    client = TestClient(app)
    response = client.post("/predict")

    assert response.status_code == 422
