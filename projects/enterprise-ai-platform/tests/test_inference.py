from typing import Any

from enterprise_ai_platform.inference import (
    HuggingFaceIncidentClassifier,
    select_pipeline_device,
)


class FakePipeline:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _text: str, **_kwargs: Any) -> dict[str, object]:
        self.calls += 1
        return {
            "labels": ["database failure", "network failure"],
            "scores": [0.91, 0.09],
        }


def test_pipeline_device_uses_first_cuda_gpu_when_available() -> None:
    assert select_pipeline_device(cuda_available=True) == 0


def test_pipeline_device_falls_back_to_cpu_without_cuda() -> None:
    assert select_pipeline_device(cuda_available=False) == -1


def test_classifier_maps_model_prompt_to_canonical_label() -> None:
    classifier = HuggingFaceIncidentClassifier()
    fake_pipeline = FakePipeline()
    classifier._pipeline = fake_pipeline

    result = classifier.classify("PostgreSQL connection timeout")

    assert result.label == "database"
    assert result.score == 0.91
    assert fake_pipeline.calls == 1
