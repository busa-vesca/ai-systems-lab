from fastapi.testclient import TestClient

from vision_inference_api.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_accepts_uploaded_image_stub() -> None:
    image_bytes = b"fake-image-bytes"

    response = client.post(
        "/predict",
        files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "leaf.jpg",
        "content_type": "image/jpeg",
        "size_bytes": len(image_bytes),
        "status": "received",
    }
