def runtime_summary() -> dict[str, str]:
    """Return basic runtime information for edge diagnostics."""
    try:
        import torch

        cuda_available = str(torch.cuda.is_available())
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        cuda_available = "unknown"
        device_name = f"torch unavailable: {exc}"

    return {
        "cuda_available": cuda_available,
        "device": device_name,
    }
