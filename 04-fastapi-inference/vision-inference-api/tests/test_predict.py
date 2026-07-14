from fastapi.testclient import TestClient

from vision_inference_api.main import app


def test_predict_accepts_uploaded_image() -> None:
    client = TestClient(app)
    image_content = b"fake-image-bytes"

    response = client.post(
        "/predict",
        files={"file": ("leaf.jpg", image_content, "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "leaf.jpg",
        "content_type": "image/jpeg",
        "size_bytes": len(image_content),
        "status": "received",
    }


def test_predict_requires_a_file() -> None:
    client = TestClient(app)

    response = client.post("/predict")

    assert response.status_code == 422
