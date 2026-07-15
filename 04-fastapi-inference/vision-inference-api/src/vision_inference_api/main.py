from fastapi import FastAPI, UploadFile

app = FastAPI(title="Vision Inference API")


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile) -> dict[str, str | int | None]:
    """Accept an uploaded image file and return basic file metadata.

    This is a stub endpoint. Real model inference will be added later.
    """
    content = await file.read()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "status": "received",
    }
