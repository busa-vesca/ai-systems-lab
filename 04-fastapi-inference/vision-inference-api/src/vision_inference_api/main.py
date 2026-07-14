from fastapi import FastAPI, UploadFile

app = FastAPI(title="Vision Inference API")


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile) -> dict[str, str | int | None]:
    """Acknowledge receipt of one uploaded image file."""
    content = await file.read()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "status": "received",
    }
